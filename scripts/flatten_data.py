import pandas as pd
import os
import matplotlib.pyplot as plt
import macros as m

class VisaDataProcessor():
    def __init__(self, file_path, country_name, preference, preference_range=m.COLORS_DEFAULT):
        self.file_path = file_path
        self.country_name = country_name
        self.preference = preference
        self.sheet_name = self.country_name
        self.preference_range = preference_range
        
        if (self.preference == "EB2" or self.preference == "EB3") and self.country_name == "India":
            self.sheet_name = m.SHEET_NAME_INDIA
            self.preference_range = m.COLORS_INDIA
        self.i_140_count = self.set_i140_snapshot()
    def flatten(self):
        data = pd.read_excel(self.file_path, self.sheet_name, skiprows=m.EXCEL_SKIPROWS, skipfooter=m.EXCEL_SKIPFOOTER)
        df = pd.DataFrame(data)
        id_cols = [m.COL_COUNTRY, m.COL_PREF, m.COL_STATUS, m.COL_PRIORITY_MONTH]
        prior_year = self.get_prior_year(df)
        df_flat = df.melt(id_vars=id_cols, var_name="Year", value_name="Count")
        df_flat["Year"] = df_flat["Year"].str.replace(m.COL_YEAR_PREFIX, "", regex=False)
        df_flat["Count"] = df_flat["Count"].replace("-", m.VALUE_REPLACE_DASH).replace("D", m.VALUE_REPLACE_D).infer_objects(copy = False)
        temp_yrs = df_flat["Year"].replace(m.COL_PRIOR_YEARS, str(prior_year))
        df_flat["Date"] = pd.to_datetime(df_flat[m.COL_PRIORITY_MONTH] + " " + temp_yrs, format="%B %Y")
        return df_flat

    def get_prior_year(self, df):
        list_columns = list(df.columns)
        year = int(list_columns[5].replace(m.COL_YEAR_PREFIX.strip(), "")) - 1
        return year

    def create_line_chart(self):
        df_flat = self.flatten()
        back_log = df_flat[df_flat[m.COL_STATUS] == "Awaiting Availability"]
        plt.figure(figsize=(12, 6))
        for pref, color in self.preference_range.items():
            temp = back_log[back_log[m.COL_PREF].str.contains(pref)]
            temp = temp[temp["Count"] > 0].sort_values("Date")
            if not temp.empty:
                plt.plot(temp["Date"], temp["Count"], label=f"{pref.lower()}-backlog", color=color, linewidth=2)     
        plt.title(f"{self.country_name} Priority Date Inventory (Line)")
        plt.xlabel("Priority Date")
        plt.ylabel("Number of people waiting")
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.savefig(f'{m.DATA_DIR}/{self.country_name.lower()}_line_graph.png')
        plt.close()

    def get_i140_snapshot(self):
        return self.i_140_count
    def set_i140_snapshot(self):
        file = os.path.join(os.getcwd(), m.DATA_DIR, m.I140_FILE)
        data = pd.read_excel(file, skiprows=m.EXCEL_SKIPROWS, skipfooter=m.EXCEL_SKIPFOOTER)
        data["Country"] = data["Country"].astype(str).str.strip()
        cols = list(data.columns)
        cols = cols[1:]
        for col in cols:
            data[col] = pd.to_numeric(data[col].replace("-", m.VALUE_REPLACE_DASH), errors="coerce").fillna(0)
        row = data[data["Country"] == self.country_name]
        
        mapping = m.I140_PREF_MAP
        
        if row.empty:
            return 0
        return int(row[mapping.get(self.preference)].iloc[0])