import h5py
import numpy as np
import matplotlib.pyplot as plt

def visualize_hdf5(file_path, dataset_name=None):
    """
    Reads an HDF5 file and visualizes its content as a plot.

    :param file_path: Path to the HDF5 file
    :param dataset_name: Name of the dataset to visualize (if multiple exist)
    """
    with h5py.File(file_path, 'r') as hdf5_file:
        # List all datasets
        datasets = list(hdf5_file.keys())

        if not datasets:
            print("No datasets found in the HDF5 file.")
            return

        # If dataset name is not provided, use the first one
        dataset_name = dataset_name or datasets[0]

        if dataset_name not in datasets:
            print(f"Dataset '{dataset_name}' not found. Available datasets: {datasets}")
            return
        
        # Read data
        data = np.array(hdf5_file[dataset_name])

        # Visualize data based on shape
        plt.figure(figsize=(8, 6))

        if data.ndim == 1:
            plt.plot(data)
            plt.xlabel("Index")
            plt.ylabel("Value")
            plt.title(f"Line Plot of {dataset_name}")
        elif data.ndim == 2:
            plt.imshow(data, aspect='auto', cmap='viridis', origin='lower')
            plt.colorbar(label="Value")
            plt.xlabel("X-axis")
            plt.ylabel("Y-axis")
            plt.title(f"Heatmap of {dataset_name}")
        else:
            print(f"Dataset '{dataset_name}' has {data.ndim} dimensions and cannot be visualized directly.")

        plt.show()

# Example usage:
filename = "data/uv_fields_io/PIV.1.0.h5.uvw"
visualize_hdf5(filename, 'U')
