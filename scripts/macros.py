import os

# --- Simulation Configuration ---
COUNTRY = "India"
PREFERENCE = "EB2"
TARGET_DATE = "2016-08-15"
VISA_BULLETIN_DATE = "2013-07-15"
SIMS = 1000
N_YEARS = 100

# --- Quota Constants ---
TOTAL_GREENCARDS = 140_000
COUNTRY_CAP = 0.07
CATEGORY_PREFERENCE = 0.286

# --- Dates ---
I140_INVENTORY_DATE = "2025-06-01"

# --- Stochastic Parameters (Monte Carlo) ---
# Spillover scenarios
SPILLOVER_RANGES = {
    "zero": (0, 2000),
    "low": (2000, 15000),
    "moderate": (15000, 40000),
    "high": (40000, 60000),
    "extreme": (100000, 160000)
}
SPILLOVER_PROBS = [0.3, 0.35, 0.25, 0.08, 0.02]

# Dependency Ratio (Triangular Distribution)
DEP_RATIO_LEFT = 1.9
DEP_RATIO_RIGHT = 3.0
DEP_RATIO_MODE = 1.9

# Duplicate Rate (Uniform Distribution)
DUPLICATE_RATE_MIN = 0.05
DUPLICATE_RATE_MAX = 0.10

# Attrition Rate (Uniform Distribution)
ATTRITION_MIN = 0.01
ATTRITION_MAX = 0.04

# --- File System Paths ---
# Directory names
DATA_DIR = "data"
IMG_DIR = "simulation_images"

# File names
INVENTORY_FILE = "eb_inventory_october_2025.xlsx"
I140_FILE = "eb_i140_i360_i526_performancedata_fy2025_q3.xlsx"
HISTOGRAM_FILE = "Monte_Carlo_Simulation.png"

# --- Excel Parsing Settings ---
EXCEL_SKIPROWS = 3
EXCEL_SKIPFOOTER = 12
VALUE_REPLACE_DASH = 0
VALUE_REPLACE_D = 5
SHEET_NAME_INDIA = "India (EB2 EB3)"

# Column Identification
COL_COUNTRY = 'Country Of Chargeability'
COL_PREF = 'Preference Category'
COL_STATUS = 'Visa Status'
COL_PRIORITY_MONTH = 'Priority Date Month'
COL_YEAR_PREFIX = "Priority Date Year - "
COL_PRIOR_YEARS = "Prior Years"

# --- Plotting & Visualization ---
# Colors
COLORS_DEFAULT = {"EB1": "#007BFF", "EB2": "#FF9F00", "EB3": "#28A745"}
COLORS_INDIA = {"EB2": "#FF9F00", "EB3": "#28A745"}

# Histogram Settings
HIST_BINS = 20
HIST_FIGSIZE = (10, 6)
HIST_COLOR_EDGE = "yellow"
HIST_COLOR_BAR = "#3B82F6"
HIST_COLOR_MEDIAN = "white"
HIST_COLOR_95 = "#F87171"

# --- Mappings ---
# Mapping user preference strings to I-140 Excel columns
I140_PREF_MAP = {
    "EB1": "1st (Priority)",
    "EB2": "2nd (Advanced Degree Professional)",
    "EB3": "3rd (Professional and Skilled)"
}