import numpy as np
import pandas as pd
import h5py
import matplotlib.pyplot as plt
import os

# Define grid dimensions
x_grid = np.arange(0, 50, 0.1).reshape(500, 1)
y_grid = np.arange(0, 50, 0.1).reshape(1, 500)

# Process multiple CSV files
for file_num in range(1000, 1101):
    filename = f"vel_{file_num}.csv"
    hdf5_filename = f"vel_{file_num}.h5"
    
    if not os.path.exists(filename):
        print(f"File {filename} not found, skipping...")
        continue
    
    # Load the CSV file
    df = pd.read_csv(filename)
    
    # Extract relevant columns
    x_values = df["x"].values
    y_values = df["y"].values
    U_values = df["U:0"].values
    V_values = df["U:1"].values
    
    U_grid = np.full((len(y_grid.flatten()), len(x_grid.flatten())), np.nan)
    V_grid = np.full((len(y_grid.flatten()), len(x_grid.flatten())), np.nan)
    
    # Fill grid with values
    for i in range(len(x_values)):
        x_idx = int(round(x_values[i] / 0.1))
        y_idx = int(round(y_values[i] / 0.1))
        if 0 <= x_idx < len(x_grid) and 0 <= y_idx < len(y_grid.flatten()):
            U_grid[y_idx, x_idx] = U_values[i]
            V_grid[y_idx, x_idx] = V_values[i]
    
    # Save to HDF5 file
    with h5py.File(hdf5_filename, "w") as hdf5_file:
        hdf5_file.create_dataset("x", data=x_grid)
        hdf5_file.create_dataset("y", data=y_grid)
        hdf5_file.create_dataset("U", data=U_grid)
        hdf5_file.create_dataset("V", data=V_grid)
    
    # Generate heatmaps
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    c1 = axes[0, 0].imshow(U_grid, extent=[0, 50, 0, 50], origin="lower", cmap="jet")
    axes[0, 0].set_title(f"Heatmap of U - {filename}")
    axes[0, 0].set_xlabel("X Coordinate")
    axes[0, 0].set_ylabel("Y Coordinate")
    fig.colorbar(c1, ax=axes[0, 0])
    
    c2 = axes[0, 1].imshow(V_grid, extent=[0, 50, 0, 50], origin="lower", cmap="jet")
    axes[0, 1].set_title(f"Heatmap of V - {filename}")
    axes[0, 1].set_xlabel("X Coordinate")
    axes[0, 1].set_ylabel("Y Coordinate")
    fig.colorbar(c2, ax=axes[0, 1])
    
    # Generate 1D heatmaps
    fig, axes = plt.subplots(2, 1, figsize=(10, 6))
    
    c3 = axes[0].imshow([x_grid.flatten()], aspect="auto", cmap="jet", extent=[0, 50, 0, 1])
    axes[0].set_title(f"1D Heatmap of X - {filename}")
    axes[0].set_xlabel("X Coordinate")
    axes[0].set_yticks([])
    fig.colorbar(c3, ax=axes[0])
    
    c4 = axes[1].imshow([y_grid.flatten()], aspect="auto", cmap="jet", extent=[0, 50, 0, 1])
    axes[1].set_title(f"1D Heatmap of Y - {filename}")
    axes[1].set_xlabel("Y Coordinate")
    axes[1].set_yticks([])
    fig.colorbar(c4, ax=axes[1])
    
    plt.tight_layout()
    plt.show()
    
    print(f"Data successfully stored in {hdf5_filename}")
