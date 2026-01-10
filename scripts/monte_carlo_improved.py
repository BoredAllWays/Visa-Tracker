import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flatten_data import VisaDataProcessor
from tqdm import tqdm
import seaborn as sns


def gen_sim_parameters(total_greencards = 140_000, country_cap = 0.07, category_preference = 0.286, n_years = 100):
    base_quota = total_greencards * country_cap * category_preference
    #spillovers
    ranges = {
        "zero": (0, 2000),
        "low": (2000, 15000),
        "moderate": (15000, 40000),
        "high": (40000, 60000),
        "extreme": (100000, 160000)
    }
    scenarios = list(ranges.keys())
    probs = [0.3, 0.35, 0.25, 0.08, 0.02]
    choices = [np.random.choice(scenarios, p=probs) for _ in range(n_years)]
    spillover_list = [np.random.randint(ranges[choices[i]][0], ranges[choices[i]][1] + 1) for i in range(n_years)]
    #extra factors
    dependancy_ratio = np.random.triangular(left = 1.9, right = 3.0, mode = 1.9)
    duplicate_rate = np.random.uniform(0.05, 0.10)
    attrition_rates = [np.random.uniform(0.01, 0.04) for _ in range(n_years)]
    return base_quota, spillover_list,attrition_rates, dependancy_ratio, duplicate_rate
def gen_people_ahead(vdp, eb_inventory, td, l_inv_d, i_140_d, vbd, dupl, dep):
    target_date = td
    last_inv_date = l_inv_d
    i_140_inventory_date = i_140_d
    visa_bulletin_date = vbd
    eb_inventory = eb_inventory[eb_inventory["Date"] > visa_bulletin_date]
    if target_date < last_inv_date:
        people_ahead = eb_inventory[(eb_inventory["Date"] < target_date)]["Count"].sum()
        return people_ahead
    people_ahead = eb_inventory["Count"].sum()
    gap_days = (i_140_inventory_date - last_inv_date).days
    gap_position_days = (target_date - last_inv_date).days
    percent_in_gap = min(gap_position_days / gap_days, 1.0)
    i_140_inventory_count = vdp.get_i140_snapshot() * percent_in_gap * (1-dupl) * dep
    people_ahead += i_140_inventory_count
    return people_ahead
def monte_carlo(vdp, preference, country, sims=1000):
    #paremeters
    target_date = "2020-08-11"
    visa_bulletin_date = "2023-02-23"
    target_date = pd.to_datetime(target_date)
    simulation_start_date = pd.Timestamp("2025-10-01")
    i_140_inventory_date = pd.Timestamp("2025-06-01")
    eb_inventory = vdp.flatten()
    eb_inventory = eb_inventory[(eb_inventory["Visa Status"] == "Awaiting Availability") & (eb_inventory["Country Of Chargeability"] == country) & (eb_inventory["Preference Category"].str.contains(preference)) & (eb_inventory["Count"] > 0)].sort_values("Date")
    last_inv_date = eb_inventory.iloc[-1]["Date"]

    results = []
    #for _ in tqdm(range(sims), desc="running monte carlo simulations"):
    for _ in range(sims):
        quota, spillovers, attr, dep, dupl = gen_sim_parameters()
        people_ahead = gen_people_ahead(vdp, eb_inventory, target_date, last_inv_date, i_140_inventory_date, visa_bulletin_date, dupl, dep)
        print(eb_inventory[["Visa Status", "Preference Category", "Count"]])
        months_passed = 0
        current_backlog = people_ahead
        year_index = 0
        supply = quota
        supply += spillovers[year_index]
        people_ahead *= (1 - attr[year_index])
        current_backlog = people_ahead
        while current_backlog > 0:
            if supply > current_backlog:
                months_passed += current_backlog/supply * 12
                break
            current_backlog -= supply
            months_passed += 12
            year_index += 1
            safe_index = min(year_index, len(spillovers) - 1)
            supply = quota + spillovers[safe_index]
            current_backlog *= (1-attr[safe_index])
        results.append(months_passed / 12)
    return results

def plot_histogram(results):
    p50 = np.percentile(results, 50)
    p95 = np.percentile(results, 95)
    mean = np.mean(results)

    plt.style.use("dark_background")
    plt.figure(figsize=(10, 6))

    sns.histplot(results, bins=20, color="#3B82F6", edgecolor="yellow", alpha=0.85, kde=True)
    plt.axvline(p50, color="white", linestyle="-", linewidth=2, label=f"Median (50%): {p50:.1f} years")
    plt.axvline(p95, color="#F87171", linestyle="--", linewidth=2, label=f"95%: {p95:.1f} years")

    plt.xlabel("Years Passed")
    plt.ylabel("Monte Carlo Frequency")
    plt.title("Monte Carlo Simulation")

    plt.grid(True, axis="y", alpha=0.35)
    plt.legend()
    plt.savefig("simulation_images/Monte_Carlo_Simulation.png")
    plt.show()

def main():
    file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")
    vdp = VisaDataProcessor(file_path, "China", "1st")
    results = monte_carlo(vdp, "1st", "China", sims=1000)
    print(results)
    #plot_histogram(results)

if __name__ == "__main__":
    main()