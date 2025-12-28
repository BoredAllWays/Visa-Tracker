import camelot
import pandas as pd
from IPython.display import display

file_name = "Employment_Worldwide_India_FY23.pdf"
tables = camelot.read_pdf(file_name, flavor = "lattice", pages= "all")
table = tables[0].df
print(len(tables))
display(table)