import os
from flatten_data import VisaDataProcessor

file_path = os.path.join(os.getcwd(), "data", "eb_inventory_october_2025.xlsx")

vdp = VisaDataProcessor(file_path, "Mexico", "EB2")
vdp.create_line_chart()
vdp.create_bar_chart()