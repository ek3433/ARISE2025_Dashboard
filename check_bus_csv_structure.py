import pandas as pd

print("=== CHECKING BUS CSV STRUCTURE ===\n")

# Check the 2020-2024 file
print("1. MTA_Bus_Hourly_Ridership__2020-2024.csv:")
try:
    df_2020_2024 = pd.read_csv("MTA_Bus_Hourly_Ridership__2020-2024.csv", nrows=1000)
    print(f"   Shape: {df_2020_2024.shape}")
    print(f"   Columns: {df_2020_2024.columns.tolist()}")
    print(f"   Sample data:")
    print(df_2020_2024.head(3))
    print(f"   Unique bus routes: {len(df_2020_2024['bus_route'].unique()) if 'bus_route' in df_2020_2024.columns else 'bus_route column not found'}")
    print(f"   Date range: {df_2020_2024['transit_timestamp'].min()} to {df_2020_2024['transit_timestamp'].max() if 'transit_timestamp' in df_2020_2024.columns else 'transit_timestamp column not found'}")
except Exception as e:
    print(f"   Error reading file: {e}")

print("\n" + "="*50 + "\n")

# Check the 2025 file
print("2. MTA_Bus_Hourly_Ridership__Beginning_2025.csv:")
try:
    df_2025 = pd.read_csv("MTA_Bus_Hourly_Ridership__Beginning_2025.csv", nrows=1000)
    print(f"   Shape: {df_2025.shape}")
    print(f"   Columns: {df_2025.columns.tolist()}")
    print(f"   Sample data:")
    print(df_2025.head(3))
    print(f"   Unique bus routes: {len(df_2025['bus_route'].unique()) if 'bus_route' in df_2025.columns else 'bus_route column not found'}")
    print(f"   Date range: {df_2025['transit_timestamp'].min()} to {df_2025['transit_timestamp'].max() if 'transit_timestamp' in df_2025.columns else 'transit_timestamp column not found'}")
except Exception as e:
    print(f"   Error reading file: {e}")

print("\n" + "="*50 + "\n")

# Check the parquet file
print("3. bus_monthly.parquet:")
try:
    df_parquet = pd.read_parquet("bus_monthly.parquet")
    print(f"   Shape: {df_parquet.shape}")
    print(f"   Columns: {df_parquet.columns.tolist()}")
    print(f"   Sample data:")
    print(df_parquet.head(3))
    print(f"   Unique bus routes: {len(df_parquet['Route'].unique()) if 'Route' in df_parquet.columns else 'Route column not found'}")
    print(f"   Date range: {df_parquet['YearMonth'].min()} to {df_parquet['YearMonth'].max() if 'YearMonth' in df_parquet.columns else 'YearMonth column not found'}")
except Exception as e:
    print(f"   Error reading file: {e}")

print("\n" + "="*50 + "\n")

# Check for common bus routes across files
print("4. Comparing bus routes across files:")
try:
    if 'bus_route' in df_2020_2024.columns and 'bus_route' in df_2025.columns:
        routes_2020_2024 = set(df_2020_2024['bus_route'].unique())
        routes_2025 = set(df_2025['bus_route'].unique())
        common_routes = routes_2020_2024.intersection(routes_2025)
        print(f"   Common routes between 2020-2024 and 2025: {len(common_routes)}")
        print(f"   Sample common routes: {list(common_routes)[:10]}")
    else:
        print("   Cannot compare routes - column names don't match")
except Exception as e:
    print(f"   Error comparing routes: {e}") 