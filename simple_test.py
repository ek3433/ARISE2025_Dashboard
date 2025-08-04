import pandas as pd

# Test URLs
BUS_2020_2024_URL = "https://drive.google.com/uc?export=download&id=15LJHuu9oleo_3R7ugYDu_akNHMX6AvLF"
BUS_2025_URL = "https://drive.google.com/uc?export=download&id=1BJbjV4vcx31dMOY2f3YlJ-r1ot3WG8nG"

print("=== SIMPLE BUS DATA TEST ===")

try:
    # Test 1: Load 2020-2024 data
    print("Loading 2020-2024 data...")
    df_2020_2024 = pd.read_csv(BUS_2020_2024_URL, nrows=100, on_bad_lines='skip', engine='c')
    print(f"Loaded {len(df_2020_2024)} rows")
    print(f"Columns: {list(df_2020_2024.columns)}")
    
    # Test 2: Load 2025 data
    print("Loading 2025 data...")
    df_2025 = pd.read_csv(BUS_2025_URL, nrows=100, on_bad_lines='skip', engine='c')
    print(f"Loaded {len(df_2025)} rows")
    print(f"Columns: {list(df_2025.columns)}")
    
    # Test 3: Check if columns exist
    print("Checking columns...")
    
    if 'transit_timestamp' in df_2020_2024.columns:
        print("OK: transit_timestamp found in 2020-2024 data")
        print(f"Sample: {df_2020_2024['transit_timestamp'].iloc[0]}")
    else:
        print("ERROR: transit_timestamp NOT found in 2020-2024 data")
        
    if 'transit_timestamp' in df_2025.columns:
        print("OK: transit_timestamp found in 2025 data")
        print(f"Sample: {df_2025['transit_timestamp'].iloc[0]}")
    else:
        print("ERROR: transit_timestamp NOT found in 2025 data")
        
    if 'bus_route' in df_2020_2024.columns:
        print("OK: bus_route found in 2020-2024 data")
        print(f"Sample routes: {list(df_2020_2024['bus_route'].unique())[:5]}")
    else:
        print("ERROR: bus_route NOT found in 2020-2024 data")
        
    if 'bus_route' in df_2025.columns:
        print("OK: bus_route found in 2025 data")
        print(f"Sample routes: {list(df_2025['bus_route'].unique())[:5]}")
    else:
        print("ERROR: bus_route NOT found in 2025 data")
        
    if 'ridership' in df_2020_2024.columns:
        print("OK: ridership found in 2020-2024 data")
        print(f"Range: {df_2020_2024['ridership'].min()} to {df_2020_2024['ridership'].max()}")
    else:
        print("ERROR: ridership NOT found in 2020-2024 data")
        
    if 'ridership' in df_2025.columns:
        print("OK: ridership found in 2025 data")
        print(f"Range: {df_2025['ridership'].min()} to {df_2025['ridership'].max()}")
    else:
        print("ERROR: ridership NOT found in 2025 data")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc() 