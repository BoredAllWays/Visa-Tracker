import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flatten_data import VisaDataProcessor

class VisaSimulationEngine:
    def __init__(self, vdp_file, country, category, sims=10000):
        self.country = country
        self.category = category
        self.sims = sims
        
        # Load and Filter Data
        vdp = VisaDataProcessor(vdp_file, country, category)
        self.raw_inv = vdp.flatten()
        self.raw_inv = self.raw_inv[self.raw_inv["Visa Status"] == "Awaiting Availability"].sort_values("Date")
        self.hidden_total_snapshot = float(vdp.get_i140_snapshot())
        
        # Simulation Settings
        self.annual_quota = 140000
        self.country_cap = 0.07
        self.pref_percent = 0.286
        self.child_age_out_rate = 0.015
        
        # USCIS Trend Weights (For distributing hidden backlog)
        self.year_weights = {
            2014: 1.0, 2015: 1.0, 2016: 1.4, 2017: 1.3, 
            2018: 1.3, 2019: 1.4, 2020: 1.2, 2021: 1.8, 
            2022: 1.6, 2023: 1.5, 2024: 1.5, 2025: 1.5
        }

    def _get_random_streams(self, max_years=50):
        # 1. Spillover Scenarios
        choices = [0, 1, 2, 3, 4]
        probs = [0.20, 0.35, 0.30, 0.10, 0.05]
        scenario_indices = np.random.choice(choices, size=(self.sims, max_years), p=probs)
        
        spillovers = np.zeros((self.sims, max_years))
        spillovers[scenario_indices == 0] = np.random.randint(0, 1000, size=(scenario_indices == 0).sum())
        spillovers[scenario_indices == 1] = np.random.randint(2000, 8000, size=(scenario_indices == 1).sum())
        spillovers[scenario_indices == 2] = np.random.randint(10000, 25000, size=(scenario_indices == 2).sum())
        spillovers[scenario_indices == 3] = np.random.randint(30000, 50000, size=(scenario_indices == 3).sum())
        spillovers[scenario_indices == 4] = np.random.randint(80000, 120000, size=(scenario_indices == 4).sum())
        
        # 2. Dependent Ratios (Family Size)
        dep_ratios = np.random.triangular(1.6, 2.0, 2.3, size=self.sims)
        
        # 3. Duplicate Deflation (Porting/Multiple Filings)
        deflation_factors = np.random.triangular(0.65, 0.75, 0.85, size=self.sims)
        
        # 4. Annual Attrition (Dropouts)
        attrition_rates = np.random.uniform(0.05, 0.12, size=self.sims)
        
        return spillovers, dep_ratios, deflation_factors, attrition_rates

    def _distribute_hidden_backlog(self, start_date, total_hidden_count):
        if total_hidden_count <= 0:
            return np.array([]), np.array([])

        current_date = pd.to_datetime(start_date)
        start_year = current_date.year
        base_annual_inflow = 50000 
        years_to_project = list(range(start_year, start_year + 15))
        
        synthetic_dates = []
        synthetic_counts = []
        remaining_people = total_hidden_count
        
        for year in years_to_project:
            weight = self.year_weights.get(year, 1.5)
            monthly_flow = (base_annual_inflow * weight) / 12
            
            for month in range(1, 13):
                if year == start_year and month <= current_date.month:
                    continue
                if remaining_people <= 0:
                    break
                
                flow = min(monthly_flow, remaining_people)
                synthetic_dates.append(np.datetime64(f"{year}-{month:02d}-01"))
                synthetic_counts.append(flow)
                remaining_people -= flow
            
            if remaining_people <= 0:
                break
                
        return np.array(synthetic_dates), np.array(synthetic_counts)

    def run(self, priority_date, current_bulletin_date):
        bulletin_cutoff = pd.to_datetime(current_bulletin_date)
        target_date = pd.to_datetime(priority_date).to_datetime64()
        
        if target_date < bulletin_cutoff.to_datetime64():
            print("User is already current!")
            return np.zeros(self.sims)

        # Prepare Visible Inventory
        active_inv = self.raw_inv[self.raw_inv["Date"] >= bulletin_cutoff]
        inv_dates = pd.to_datetime(active_inv["Date"]).values
        inv_counts = active_inv["Count"].astype(float).values
        
        max_inv_date = inv_dates.max() if len(inv_dates) > 0 else np.datetime64(bulletin_cutoff)

        # Prepare Hidden Inventory (Weighted Distribution)
        hidden_dates, hidden_counts = self._distribute_hidden_backlog(max_inv_date, self.hidden_total_snapshot)
        
        # Merge Timelines
        if len(hidden_dates) > 0:
            full_dates = np.concatenate([inv_dates, hidden_dates])
            full_counts = np.concatenate([inv_counts, hidden_counts])
        else:
            full_dates = inv_dates
            full_counts = inv_counts
            
        if len(full_dates) > 0 and target_date > full_dates.max():
             print(f"Warning: Date {priority_date} exceeds estimated backlog timeline.")

        monthly_quota_base = (self.annual_quota * self.country_cap * self.pref_percent) / 12
        spillover_stream, dep_ratios, deflation_factors, attrition_rates = self._get_random_streams()
        
        results = np.zeros(self.sims)

        print(f"Simulating {self.sims} runs for {priority_date}...")
        
        # Main Loop
        for i in range(self.sims):
            # Apply Adjustment Factors
            adjustment = deflation_factors[i] * dep_ratios[i]
            sim_counts = full_counts * adjustment
            
            # Decay Logic
            total_monthly_decay = 1 - ((attrition_rates[i] + self.child_age_out_rate) / 12)
            
            idx = 0
            max_idx = len(sim_counts)
            months_passed = 0
            user_reached = False
            year_idx = 0
            
            monthly_spillover = spillover_stream[i, year_idx] / 12
            
            while not user_reached:
                # Annual Updates
                if months_passed > 0 and months_passed % 12 == 0:
                    year_idx += 1
                    if year_idx < 50:
                        monthly_spillover = spillover_stream[i, year_idx] / 12
                
                # Monthly Processing
                efficiency = 0.8 + (0.4 * np.random.random())
                current_supply = (monthly_quota_base * efficiency) + monthly_spillover
                
                # Apply Decay to Current Bucket
                if idx < max_idx:
                    sim_counts[idx] *= total_monthly_decay
                
                # Consume Quota
                if idx < max_idx:
                    if full_dates[idx] > target_date:
                        user_reached = True; break
                    
                    sim_counts[idx] -= current_supply
                    
                    while idx < max_idx and sim_counts[idx] <= 0:
                        leftover = abs(sim_counts[idx])
                        idx += 1
                        if idx < max_idx:
                            sim_counts[idx] -= leftover
                            sim_counts[idx] *= total_monthly_decay 
                else:
                    user_reached = True
                
                months_passed += 1
                if months_passed > 1200: break
            
            results[i] = months_passed / 12
            
        return results

    def plot(self, results, title_suffix=""):
        if len(results) == 0 or np.all(results == 0):
            print("No plot generated.")
            return

        plt.figure(figsize=(10, 6))
        plt.hist(results, bins=100, color="cornflowerblue", edgecolor="black", alpha=0.7)
        
        median_val = np.median(results)
        safe_val = np.percentile(results, 90)
        
        plt.axvline(median_val, color="navy", linestyle="dashed", linewidth=2, label=f"Median: {median_val:.1f} Yrs")
        plt.axvline(safe_val, color="red", linestyle="dashed", linewidth=2, label=f"90% Safe: {safe_val:.1f} Yrs")
        
        plt.title(f'Wait Time Simulation ({self.country} {self.category}) {title_suffix}', fontsize=14)
        plt.xlabel('Years to Wait', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.legend()
        plt.grid(axis='y', alpha=0.3)
        
        filename = f"simulation_{title_suffix.strip().replace(' ','_')}.png"
        plt.savefig(filename)
        print(f"Plot saved to {filename}")
        plt.close()

if __name__ == "__main__":
    file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")
    engine = VisaSimulationEngine(file_path, "India", "EB2", sims=100000)

    res = engine.run("2015-08-01", "2013-07-15")
    print(f"Median: {np.median(res):.2f} years")
    engine.plot(res, "2018")