# view csv file

import pandas as pd
import os

filename = "newdata/data/vel_1000.csv"

if os.path.exists(filename):
    df = pd.read_csv(filename)
    # print first 60 rows
    print(df.tail())