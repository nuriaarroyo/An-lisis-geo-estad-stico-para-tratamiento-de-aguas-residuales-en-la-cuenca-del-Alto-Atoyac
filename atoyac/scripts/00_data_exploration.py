import pandas as pd
import matplotlib.pyplot as plt

def explore_data(file_path):
    # Load the dataset
    data = pd.read_csv(file_path)
    
    # Display basic information about the dataset
    print("Dataset Information:")
    print(data.info())
    
    # Display the first few rows of the dataset
    print("\nFirst 5 Rows:")
    print(data.head())
    
    # Display summary statistics
    print("\nSummary Statistics:")
    print(data.describe())
    
    # Check for missing values
    print("\nMissing Values:")
    print(data.isnull().sum())
    
    # Plot histograms for numerical features
    numerical_features = data.select_dtypes(include=['float64', 'int64']).columns
    data[numerical_features].hist(figsize=(10, 8))
    plt.tight_layout()
    plt.show()

