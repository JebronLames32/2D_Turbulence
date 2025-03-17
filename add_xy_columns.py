import pandas as pd
import os

folder_path = "newdata/data"
# Define the range of file numbers
start, end = 1000, 1100

# Number of rows per x increment
y_steps = 500

# Read and modify each file
for i in range(start, end + 1):
    filename = os.path.join(folder_path, f"vel_{i}.csv")  # Construct full path
    
    # Load the CSV file
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        
        # Generate x and y values
        num_rows = len(df)
        x_values = [(j // y_steps) * 0.1 for j in range(num_rows)]
        y_values = [(j % y_steps) * 0.1 for j in range(num_rows)]
        
        # Add the new columns
        df["x"] = x_values
        df["y"] = y_values
        
        # Save the modified file
        df.to_csv(filename, index=False)
        
        print(f"Updated {filename}")
    else:
        print(f"File {filename} not found.")
