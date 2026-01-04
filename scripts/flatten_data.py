import pandas as pd
import os
import matplotlib.pyplot as plt


class VisaDataProcessor():
    def __init__(self, file_path, country_name, preference, preference_range = ["EB1", "EB2", "EB3"]):
        self.file_path = file_path
        self.country_name = country_name
        self.sheet_name = self.country_name
        self.preference_range = preference_range
        if (preference == "EB2" or preference == "EB3") and self.country_name == "India":
            self.sheet_name = "India (EB2 EB3)"
            
    def flatten(self):
        data = pd.read_excel(self.file_path, self.sheet_name, skiprows=3, skipfooter=12)
        df = pd.DataFrame(data)
        id_cols = ['Country Of Chargeability', 'Preference Category', 'Visa Status', 'Priority Date Month']
        prior_year = self.get_prior_year(df)
        df_flat = df.melt(id_vars=id_cols, var_name = "Year", value_name = "Count")
        df_flat["Year"] = df_flat["Year"].str.replace("Priority Date Year - ", "", regex=False)
        df_flat["Count"] = df_flat["Count"].replace("-", 0).replace("D", 5)
        temp_yrs = df_flat["Year"].replace("Prior Years", str(prior_year))
        df_flat["Date"] = pd.to_datetime(df_flat["Priority Date Month"] + " " + temp_yrs, format = "%B %Y")
        return df_flat
    def get_prior_year(self, df):
        list_columns = list(df.columns)
        year = int(list_columns[5].replace("Priority Date Year -", "")) - 1
        return year
    def display(self):
        df_flat = self.flatten()
        back_log = df_flat[df_flat["Visa Status"] == "Awaiting Availability"]
        eb_back_logs = []
        #line chart
        for i in self.preference_range:
            temp = back_log[back_log["Preference Category"].str.contains(i)]
            temp = temp[temp["Count"] > 0]
            eb_back_logs.append(temp)
        plt.figure(figsize=(12, 6))
        colors = ["#007BFF", "#FF9F00", "#28A745"]
        for i in range(len(eb_back_logs)): 
            plt.plot(eb_back_logs[i]["Date"], eb_back_logs[i]["Count"], label = f"eb{i+1}-backlog", color=colors[i], linewidth = 2)
        plt.title("Graph")
        plt.xlabel("Priority Date", fontsize = 12)
        plt.ylabel("Number of people waiting", fontsize = 12)
        plt.legend()
        plt.grid(True, linestyle='--', alpha=0.6)
        plt.savefig('data/backlog_graph.png')
        plt.close()
    