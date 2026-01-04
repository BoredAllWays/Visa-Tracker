import os
from flatten_data import VisaDataProcessor

file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")

vdp = VisaDataProcessor(file_path, "India", "EB2", ["EB2", "EB3"])
vdp.display()