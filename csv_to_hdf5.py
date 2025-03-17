import os
import pandas as pd
import h5py
import numpy as np

# Define the folder containing CSV files and where to save HDF5 files
csv_folder = "newdata/data"  # Change this to your actual path
hdf5_folder = "newdata/hdf5"  # Change this to your desired output path

# Ensure output folder exists
os.makedirs(hdf5_folder, exist_ok=True)

# Iterate through all CSV files in the folder
for csv_file in os.listdir(csv_folder):
    if csv_file.endswith(".csv"):
        csv_path = os.path.join(csv_folder, csv_file)
        hdf5_path = os.path.join(hdf5_folder, csv_file.replace(".csv", ".h5"))

        # Load CSV into DataFrame
        df = pd.read_csv(csv_path)

        # Convert to numpy arrays (ensure 2D structure)
        u_data = df[['U:0']].to_numpy()
        v_data = df[['U:1']].to_numpy().T
        x_data = df[['x']].to_numpy()  # Keep 'x' as a column vector
        y_data = df[['y']].to_numpy().T  # Transpose 'y' to match expected shape

        # Create HDF5 file
        with h5py.File(hdf5_path, "w") as hdf5_file:
            hdf5_file.create_dataset("U", data=u_data)
            hdf5_file.create_dataset("V", data=v_data)
            hdf5_file.create_dataset("x", data=x_data)
            hdf5_file.create_dataset("y", data=y_data)

        print(f"Converted {csv_file} to {hdf5_path}")
