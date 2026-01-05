# slow backup that needs to be optimized
# import os
# import pandas as pd

# import numpy as np
# import matplotlib.pyplot as plt
# from flatten_data import VisaDataProcessor

# def get_spillover_for_year():
#     scenarios = ["pessimistic", "realistic", "optimistic"]
#     probabilties = [0.6, 0.3, 0.1]
#     chosen_scenario = np.random.choice(scenarios, p=probabilties)
#     if chosen_scenario == "pessimistic":
#         return np.random.randint(0, 50)
#     elif chosen_scenario == "realistic":
#         return np.random.randint(100, 500)
#     else:
#         return np.random.randint(2000, 8000)

# def run_monte_carlo(vdp, priority_date, country_cap=0.07, pref_percent=0.286, annual_quota=140000, sims=10000):
#     inv = vdp.flatten()
#     inv = inv[inv["Visa Status"] == "Awaiting Availability"].sort_values("Date")
    
#     inv_counts = inv["Count"].astype(float).values
    
#     hidden_total = float(vdp.get_i140_snapshot())
    
#     monthly_quota = (annual_quota * country_cap * pref_percent) / 12
#     target_date = pd.to_datetime(priority_date).to_datetime64()
#     results = []
    
#     if len(inv_dates) == 0:
#         max_inv_date = np.datetime64('1677-09-21')
#     else:
#         max_inv_date = inv_dates.max()
        
#     is_hidden = target_date > max_inv_date
    
#     for _ in range(sims):
#         sim_hidden = hidden_total
#         sim_counts = inv_counts.copy()
        
#         idx = 0
#         max_idx = len(sim_counts)
        
#         months_passed = 0
#         user_reached = False
        
#         spillover = get_spillover_for_year() / 12
        
#         while not user_reached:
#             if months_passed > 0 and months_passed % 12 == 0:
#                 spillover = get_spillover_for_year() / 12
                
#             uscis_efficiency = np.random.uniform(0.8, 1.2)
#             current_supply = monthly_quota * uscis_efficiency + spillover
            
#             annual_dropout = np.random.uniform(0.02, 0.08)
#             monthly_dropout_factor = 1 - (annual_dropout) / 12
#             sim_hidden *= monthly_dropout_factor
            
#             if idx < max_idx:
#                 if not is_hidden and inv_dates[idx] > target_date:
#                     user_reached = True
#                     break
                
#                 sim_counts[idx] -= current_supply
                
#                 while idx < max_idx and sim_counts[idx] <= 0:
#                     leftover_visas = abs(sim_counts[idx])
#                     idx += 1
                    
#                     if idx < max_idx:
#                         sim_counts[idx] -= leftover_visas
#                     else:
#                         sim_hidden -= leftover_visas
#             else:
#                 sim_hidden -= current_supply
                
#             if is_hidden and idx >= max_idx and sim_hidden <= 0:
#                 user_reached = True
#             if not is_hidden and idx >= max_idx:
#                 user_reached = True
                
#             months_passed += 1
#             if months_passed > 1200:
#                 break
                
#         results.append(months_passed / 12)
        
#     return results

# def plot_simulation_results(results, country, preference):
#     if not results:
#         return
#     plt.figure(figsize=(10, 6))
#     plt.hist(results, bins=100, color="skyblue", edgecolor="black", alpha=0.7)
#     avg_years = np.mean(results)
#     median_years = np.median(results)
#     safe_years = np.percentile(results, 90)
#     plt.axvline(median_years, color="green", linestyle="dashed", linewidth=2, label=f"Median : {median_years:.1f} Years")
#     plt.axvline(safe_years, color='red', linestyle='dashed', linewidth=2, label=f'90% Certainty: {safe_years:.1f} Years')
#     plt.title(f'Monte Carlo Simulation: Green Card Wait Time ({country} {preference})', fontsize=14)
#     plt.xlabel('Years to Wait', fontsize=12)
#     plt.ylabel('Frequency (Number of Simulations)', fontsize=12)
#     plt.legend()
#     plt.grid(axis='y', alpha=0.3)
#     output_file = "simulation_result.png"
#     plt.savefig(output_file)
#     print(f"Plot saved to {output_file}")
#     plt.close()

# if __name__ == "__main__":
#     file = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")
#     vdp = VisaDataProcessor(file, "India", "EB2")
#     final_results = run_monte_carlo(vdp, "2014-12-01", sims=10000)
#     print(final_results[:10])
#     plot_simulation_results(final_results, "India", "EB2")