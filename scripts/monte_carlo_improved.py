import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from flatten_data import VisaDataProcessor

def monte_carlo(vdp, sims = 10000):
    data = vdp.flatten()
    data = data[data["Preference Category"].str.contains("2nd")]
    data = data[data["Visa Status"] == "Awaiting Availability"].sort_values("Date")

    hidden_back_log = vdp.get_i140_snapshot()
    print(hidden_back_log)
    print(data)
    data["Count"] = data["Count"].astype(float)
    print(data)
    start_date = data["Date"].iloc[0] if not data.empty else pd.Timestamp.now()
    print(start_date)
        
file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")
vdp = VisaDataProcessor(file_path, "India", "EB2")
monte_carlo(vdp)