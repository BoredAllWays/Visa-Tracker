import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flatten_data import VisaDataProcessor
import seaborn as sns

class VisualVisaSim:
    def __init__(self, vdp_file, country, category, sims=5000):
        self.country = country
        self.category = category
        self.sims = sims

        vdp = VisaDataProcessor(vdp_file, country, category)
        self.raw_inv = vdp.flatten()
        self.raw_inv = self.raw_inv[self.raw_inv["Visa Status"] == "Awaiting Availability"].sort_values("Date")
        self.hidden_total_snapshot = float(vdp.get_i140_snapshot())

        self.annual_base_quota = 140000 * 0.07 * 0.286

    def _get_scenario_parameters(self, mode):
        if mode == "Pessimistic":
            return {
                "deflation_min": 0.80, "deflation_max": 0.90,
                "attrition_min": 0.005, "attrition_max": 0.01,
                "family_ratio_min": 1.9, "family_ratio_max": 2.0
            }
        elif mode == "Realistic":
            return {
                "deflation_min": 0.70, "deflation_max": 0.80,
                "attrition_min": 0.005, "attrition_max": 0.01,
                "family_ratio_min": 1.8, "family_ratio_max": 2.0
            }
        else:  # Optimistic
            return {
                "deflation_min": 0.60, "deflation_max": 0.70,
                "attrition_min": 0.005, "attrition_max": 0.01,
                "family_ratio_min": 1.7, "family_ratio_max": 1.9
            }

    def _generate_spillover_stream(self, mode, n_years=10):
        scenarios = ["zero", "low", "moderate", "high", "extreme"]
        ranges = {
            "zero": (0, 2000),
            "low": (2000, 15000),
            "moderate": (15000, 40000),
            "high": (40000, 60000),
            "extreme": (100000, 160000)
        }

        if mode == "Pessimistic":
            probs = [0.5, 0.4, 0.1, 0.0, 0.0]
        elif mode == "Realistic":
            probs = [0.3, 0.35, 0.25, 0.08, 0.02]
        else:  # Optimistic
            probs = [0.1, 0.2, 0.4, 0.25, 0.05]

        spillover = []
        for _ in range(n_years):
            scenario = np.random.choice(scenarios, p=probs)
            smin, smax = ranges[scenario]
            spillover.append(np.random.randint(smin, smax + 1))
        return np.array(spillover)

    def _distribute_hidden_backlog(self, start_date, count):
        if count <= 0:
            return np.array([]), np.array([])
        current_date = pd.to_datetime(start_date)
        year_weights = {2021: 1.8, 2022: 1.6, 2023: 1.5, 2024: 1.5, 2025: 1.5}
        base_flow = 60000
        dates, counts = [], []
        rem = count
        curr_year = current_date.year
        for yr in range(curr_year, curr_year + 15):
            w = year_weights.get(yr, 1.2)
            m_flow = (base_flow * w) / 12
            for m in range(1, 13):
                if yr == curr_year and m <= current_date.month:
                    continue
                if rem <= 0:
                    break
                take = min(m_flow, rem)
                dates.append(np.datetime64(f"{yr}-{m:02d}-01"))
                counts.append(take)
                rem -= take
        return np.array(dates), np.array(counts)

    def run_simulation(self, target_pd_str, mode):
        params = self._get_scenario_parameters(mode)
        target_pd = pd.to_datetime(target_pd_str).to_datetime64()

        inv_dates = pd.to_datetime(self.raw_inv["Date"]).values
        inv_counts = self.raw_inv["Count"].astype(float).values
        last_date = inv_dates.max()
        hid_dates, hid_counts = self._distribute_hidden_backlog(last_date, self.hidden_total_snapshot)

        full_dates = np.concatenate([inv_dates, hid_dates]) if len(hid_dates) > 0 else inv_dates
        full_counts = np.concatenate([inv_counts, hid_counts]) if len(hid_dates) > 0 else inv_counts

        results = []
        for _ in range(self.sims):
            deflation = np.random.uniform(params["deflation_min"], params["deflation_max"])
            fam_ratio = np.random.uniform(params["family_ratio_min"], params["family_ratio_max"])
            sim_queue = full_counts * deflation * fam_ratio

            attrition = np.random.uniform(params["attrition_min"], params["attrition_max"])
            monthly_decay = 1 - (attrition / 12)

            spillover_stream = self._generate_spillover_stream(mode, n_years=100)

            idx = 0
            months_passed = 0
            year_idx = 0
            reached = False
            base_monthly = self.annual_base_quota / 12

            while not reached and idx < len(sim_queue):
                if months_passed > 0 and months_passed % 12 == 0:
                    year_idx += 1
                supply = base_monthly + (spillover_stream[year_idx] / 12 if year_idx < len(spillover_stream) else 0)
                sim_queue[idx] *= monthly_decay
                if full_dates[idx] >= target_pd:
                    reached = True
                    break
                sim_queue[idx] -= supply
                while idx < len(sim_queue) and sim_queue[idx] <= 0:
                    supply_left = abs(sim_queue[idx])
                    idx += 1
                    if idx < len(sim_queue):
                        sim_queue[idx] -= supply_left
                        sim_queue[idx] *= monthly_decay
                months_passed += 1
                if months_passed > 1200:
                    break
            results.append(months_passed / 12)
        return np.array(results)

    # --- PLOTTING FUNCTIONS ---
    def plot_individual_safety(self, data, mode, color, target_pd, output_dir):
        plt.figure(figsize=(10, 6))
        safe_val = np.percentile(data, 90)
        median_val = np.median(data)
        plt.hist(data, bins=40, color=color, alpha=0.7, edgecolor='black', density=True)
        plt.axvline(safe_val, color='black', linestyle='--', linewidth=2,
                    label=f'90% Safe Limit: {safe_val:.1f} Years')
        plt.title(f"{mode} Scenario: Safety Analysis\n(Priority Date: {target_pd})", fontsize=14)
        plt.xlabel("Years to Wait", fontsize=12)
        plt.ylabel("Density", fontsize=12)
        stats_text = (f"Median Wait: {median_val:.1f} yrs\n90% Chance Complete by: {safe_val:.1f} yrs")
        plt.gca().text(0.65, 0.85, stats_text, transform=plt.gca().transAxes,
                       fontsize=12, verticalalignment='top',
                       bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        plt.legend(loc='upper right')
        plt.grid(axis='y', alpha=0.3)
        filename = f"{output_dir}/scenario_{mode.lower()}_safety.png"
        plt.savefig(filename)
        plt.close()
        print(f"Generated: {filename}")

    def plot_combined_ci(self, res_pess, res_real, res_opt, target_pd, output_dir):
        plt.figure(figsize=(14, 8))
        sns.kdeplot(res_pess, fill=True, color='#ff4d4d', alpha=0.3, label='Pessimistic')
        sns.kdeplot(res_real, fill=True, color='#ffa600', alpha=0.3, label='Realistic')
        sns.kdeplot(res_opt, fill=True, color='#2db300', alpha=0.3, label='Optimistic')

        def add_ci_lines(data, color):
            lower = np.percentile(data, 2.5)
            upper = np.percentile(data, 97.5)
            median = np.median(data)
            ymax = plt.gca().get_ylim()[1]
            plt.axvline(lower, color=color, linestyle='--', linewidth=2, ymax=0.95)
            plt.axvline(upper, color=color, linestyle='--', linewidth=2, ymax=0.95)
            plt.axvline(median, color=color, linestyle='-', linewidth=2, ymax=0.95)
            plt.text(median, ymax*0.97, f'{median:.1f}y', color=color, ha='center', fontweight='bold',
                     bbox=dict(facecolor='white', alpha=0.6, edgecolor='none'))

        add_ci_lines(res_pess, '#ff4d4d')
        add_ci_lines(res_real, '#ffa600')
        add_ci_lines(res_opt, '#2db300')

        plt.title(f"Master Analysis: 95% Confidence Intervals\nTarget PD: {target_pd}", fontsize=16)
        plt.xlabel("Years to Wait", fontsize=12)
        plt.ylabel("Density", fontsize=12)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        filename = f"{output_dir}/master_combined_analysis.png"
        plt.savefig(filename)
        plt.close()
        print(f"Generated: {filename}")


# --- EXECUTION ---
if __name__ == "__main__":
    output_dir = "simulation_images"
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    print(f"Created directory: {output_dir}")

    file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")
    engine = VisualVisaSim(file_path, "India", "EB2", sims=1000)
    vdp = VisaDataProcessor(file_path, "India", "EB2")
    vdp.create_line_chart()
    target_date = "2016-08-11"
    print(f"--- Running Simulations for {target_date} ---")

    r_pess = engine.run_simulation(target_date, "Pessimistic")
    r_real = engine.run_simulation(target_date, "Realistic")
    r_opt = engine.run_simulation(target_date, "Optimistic")

    engine.plot_individual_safety(r_pess, "Pessimistic", "#ff4d4d", target_date, output_dir)
    engine.plot_individual_safety(r_real, "Realistic", "#ffa600", target_date, output_dir)
    engine.plot_individual_safety(r_opt, "Optimistic", "#2db300", target_date, output_dir)

    engine.plot_combined_ci(r_pess, r_real, r_opt, target_date, output_dir)

    print("\nDone! Check the 'simulation_images' folder.")
