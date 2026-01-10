import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flatten_data import VisaDataProcessor
from tqdm import tqdm
import seaborn as sns
import macros as m 
class MonteCarloVisaSimulation:
    def __init__(
        self,
        file_path,
        country,
        preference,
        target_date,
        visa_bulletin_date,
        total_greencards=m.TOTAL_GREENCARDS,
        country_cap=m.COUNTRY_CAP,
        category_preference=m.CATEGORY_PREFERENCE,
        n_years=m.N_YEARS,
        sims=m.SIMS,
        i140_inventory_date=m.I140_INVENTORY_DATE
    ):
        self.file_path = file_path
        self.country = country
        self.preference = preference
        self.total_greencards = total_greencards
        self.country_cap = country_cap
        self.category_preference = category_preference
        self.n_years = n_years
        self.sims = sims

        self.target_date = pd.Timestamp(target_date)
        self.visa_bulletin_date = pd.Timestamp(visa_bulletin_date)
        self.i140_inventory_date = pd.Timestamp(i140_inventory_date)

        self.vdp = VisaDataProcessor(file_path, country, preference)

    def gen_sim_parameters(self):
        base_quota = self.total_greencards * self.country_cap * self.category_preference

        # Use macros for ranges and probabilities
        ranges = m.SPILLOVER_RANGES
        scenarios = list(ranges.keys())
        probs = m.SPILLOVER_PROBS

        choices = [np.random.choice(scenarios, p=probs) for _ in range(self.n_years)]
        spillover_list = [
            np.random.randint(ranges[choices[i]][0], ranges[choices[i]][1] + 1)
            for i in range(self.n_years)
        ]

        # Use macros for stochastic distributions
        dependancy_ratio = np.random.triangular(
            left=m.DEP_RATIO_LEFT, 
            right=m.DEP_RATIO_RIGHT, 
            mode=m.DEP_RATIO_MODE
        )
        duplicate_rate = np.random.uniform(
            m.DUPLICATE_RATE_MIN, 
            m.DUPLICATE_RATE_MAX
        )
        attrition_rates = [
            np.random.uniform(m.ATTRITION_MIN, m.ATTRITION_MAX) 
            for _ in range(self.n_years)
        ]

        return base_quota, spillover_list, attrition_rates, dependancy_ratio, duplicate_rate

    def gen_people_ahead(self, inv, last_inv_d, dupl, dep):
        inv = inv[inv["Date"] > self.visa_bulletin_date]

        if self.target_date < last_inv_d:
            return inv[inv["Date"] < self.target_date]["Count"].sum()

        people_ahead = inv["Count"].sum()

        gap_days = (self.i140_inventory_date - last_inv_d).days
        gap_pos_days = (self.target_date - last_inv_d).days
        pct_in_gap = min(gap_pos_days / gap_days, 1.0)

        i140_count = self.vdp.get_i140_snapshot() * pct_in_gap * (1 - dupl) * dep

        return people_ahead + i140_count

    def monte_carlo(self):
        eb_inventory = self.vdp.flatten()
        eb_inventory = eb_inventory[
            (eb_inventory[m.COL_STATUS] == "Awaiting Availability")
            & (eb_inventory[m.COL_COUNTRY] == self.country)
            & (eb_inventory[m.COL_PREF].str.contains(self.preference))
            & (eb_inventory["Count"] > 0)
        ].sort_values("Date")

        last_inv_date = eb_inventory.iloc[-1]["Date"]

        if self.target_date < self.visa_bulletin_date:
            return [0.0] * self.sims

        results = []

        for _ in tqdm(range(self.sims), desc="running monte carlo simulations"):
            quota, spillovers, attr, dep, dupl = self.gen_sim_parameters()
            people_ahead = self.gen_people_ahead(eb_inventory, last_inv_date, dupl, dep)

            months_passed = 0
            current_backlog = people_ahead

            year_index = 0
            supply = quota + spillovers[year_index]
            current_backlog *= (1 - attr[year_index])

            while current_backlog > 0:
                if supply > current_backlog:
                    months_passed += current_backlog / supply * 12
                    break

                current_backlog -= supply
                months_passed += 12
                year_index += 1
                safe_index = min(year_index, len(spillovers) - 1)
                supply = quota + spillovers[safe_index]
                current_backlog *= (1 - attr[safe_index])
            results.append(float(months_passed / 12))

        return results
    def calculate_probability(self, results, years):
        count = 0
        result_size = len(results)
        if result_size == 0:
            return 0.0
        for i in range(result_size):
            if results[i] < years:
                count += 1
        prob = count / result_size * 100
        print(f"The probability that you will wait less than {years} years is {prob:.2f}%")
    def plot_histogram(self, results):
        p50 = np.percentile(results, 50)
        p95 = np.percentile(results, 95)
        plt.style.use("dark_background")
        plt.figure(figsize=m.HIST_FIGSIZE)

        sns.histplot(results, bins=m.HIST_BINS, edgecolor=m.HIST_COLOR_EDGE, alpha=0.85, kde=True)
        plt.axvline(p50, color=m.HIST_COLOR_MEDIAN, linestyle="-", linewidth=2, label=f"Median (50%): {p50:.1f} years")
        plt.axvline(p95, color=m.HIST_COLOR_95, linestyle="--", linewidth=2, label=f"95%: {p95:.1f} years")

        plt.xlabel("Years Passed")
        plt.ylabel("Monte Carlo Frequency")
        plt.title("Monte Carlo Simulation")

        plt.grid(True, axis="y", alpha=0.35)
        plt.legend()
        plt.savefig(f"{m.IMG_DIR}/{m.HISTOGRAM_FILE}")
        plt.show()