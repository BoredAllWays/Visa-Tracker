import os
import numpy as np
from monte_carlo_visa_simulation import MonteCarloVisaSimulation
from macros import *

def main():
    file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")

    sim = MonteCarloVisaSimulation(
        file_path=file_path,
        country=COUNTRY,
        preference=PREFERENCE,
        target_date=TARGET_DATE,
        visa_bulletin_date=VISA_BULLETIN_DATE,
        sims=SIMS
    )

    results = sim.monte_carlo()
    sim.calculate_probability(results, 5)
    if len(results) > 0 and np.sum(results) == 0:
        print("Date already current. 0 wait time")
    else:
        sim.plot_histogram(results)


if __name__ == "__main__":
    main()
