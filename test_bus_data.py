import pandas as pd
import numpy as np
import requests
from io import StringIO
import gdown

# Google Drive URLs for bus data
BUS_2020_2024_URL = "https://drive.google.com/uc?export=download&id=15LJHuu9oleo_3R7ugYDu_akNHMX6AvLF"
BUS_2025_URL = "https://drive.google.com/uc?export=download&id=1BJbjV4vcx31dMOY2f3YlJ-r1ot3WG8nG"

def download_from_gdrive(url, filename):
    """Download file from Google Drive using gdown"""
    try:
        gdown.download(url, filename, quiet=False)
        return True
    except Exception as e:
        print(f"Error downloading {filename}: {e}")
        return False

def test_monthly_aggregation():
    """Test monthly aggregation of bus data"""
    print("=== TESTING MONTHLY AGGREGATION ===")
    
    try:
        print("\n1. Loading data for monthly aggregation...")
        
        # Load larger samples for aggregation testing
        df_2020_2024 = pd.read_csv("bus_2020_2024.csv", nrows=50000)
        df_2025 = pd.read_csv("bus_2025.csv", nrows=50000)
        
        print(f"   Loaded {len(df_2020_2024)} rows from 2020-2024 data")
        print(f"   Loaded {len(df_2025)} rows from 2025 data")
        
        # Convert timestamps
        print("\n2. Converting timestamps...")
        df_2020_2024['datetime'] = pd.to_datetime(df_2020_2024['transit_timestamp'])
        df_2025['datetime'] = pd.to_datetime(df_2025['transit_timestamp'])
        
        # Create monthly aggregation
        print("\n3. Creating monthly aggregations...")
        
        for df_name, df in [("2020-2024", df_2020_2024), ("2025", df_2025)]:
            print(f"\n   {df_name} dataset:")
            
            # Add month column
            df['year_month'] = df['datetime'].dt.to_period('M')
            
            # Show date range
            print(f"     Date range: {df['datetime'].min()} to {df['datetime'].max()}")
            print(f"     Month range: {df['year_month'].min()} to {df['year_month'].max()}")
            
            # Monthly aggregation by route
            monthly_data = df.groupby(['year_month', 'bus_route'])['ridership'].agg([
                'sum', 'mean', 'count'
            ]).reset_index()
            
            monthly_data.columns = ['year_month', 'bus_route', 'total_ridership', 'avg_ridership', 'data_points']
            
            print(f"     Monthly records: {len(monthly_data)}")
            print(f"     Unique months: {monthly_data['year_month'].nunique()}")
            print(f"     Unique routes: {monthly_data['bus_route'].nunique()}")
            
            # Show sample monthly data
            print(f"     Sample monthly data:")
            print(monthly_data.head(10))
            
            # Check target routes
            target_routes = [
                'M15', 'M5', 'M1', 'M2', 'M3', 'M4', 'M55', 'M7', 'M20', 'M42', 'M34', 'M22',
                'BxM1', 'BxM2', 'BxM3', 'BxM4', 'BxM11',
                'BM1', 'BM2', 'BM3', 'BM4', 'BM5',
                'QM1', 'QM2', 'QM4', 'QM5', 'QM20',
                'SIM1', 'SIM5', 'SIM6', 'SIM11', 'SIM22', 'SIM25'
            ]
            
            target_monthly = monthly_data[monthly_data['bus_route'].isin(target_routes)]
            print(f"     Target routes monthly data: {len(target_monthly)} records")
            
            if len(target_monthly) > 0:
                print(f"     Sample target route monthly data:")
                print(target_monthly.head(10))
                
                # Show ridership ranges
                print(f"     Monthly ridership range: {target_monthly['total_ridership'].min()} to {target_monthly['total_ridership'].max()}")
                print(f"     Average monthly ridership: {target_monthly['total_ridership'].mean():.2f}")
        
        # Test creating a proper monthly dataset for dashboard
        print("\n4. Creating dashboard-ready monthly dataset...")
        
        # Combine both datasets
        df_combined = pd.concat([
            df_2020_2024[['datetime', 'bus_route', 'ridership']],
            df_2025[['datetime', 'bus_route', 'ridership']]
        ], ignore_index=True)
        
        # Monthly aggregation for dashboard
        df_combined['year_month'] = df_combined['datetime'].dt.to_period('M')
        
        monthly_dashboard = df_combined.groupby(['year_month', 'bus_route'])['ridership'].sum().reset_index()
        monthly_dashboard.columns = ['year_month', 'bus_route', 'total_ridership']
        
        # Convert period to datetime for plotting
        monthly_dashboard['month_date'] = monthly_dashboard['year_month'].dt.to_timestamp()
        
        print(f"   Combined monthly dataset: {len(monthly_dashboard)} records")
        print(f"   Date range: {monthly_dashboard['month_date'].min()} to {monthly_dashboard['month_date'].max()}")
        print(f"   Total routes: {monthly_dashboard['bus_route'].nunique()}")
        
        # Filter for target routes
        target_monthly_dashboard = monthly_dashboard[monthly_dashboard['bus_route'].isin(target_routes)]
        print(f"   Target routes monthly data: {len(target_monthly_dashboard)} records")
        
        if len(target_monthly_dashboard) > 0:
            print(f"   Sample dashboard monthly data:")
            print(target_monthly_dashboard.head(10))
            
            # Show summary statistics
            print(f"   Monthly ridership summary:")
            print(f"     Min: {target_monthly_dashboard['total_ridership'].min()}")
            print(f"     Max: {target_monthly_dashboard['total_ridership'].max()}")
            print(f"     Mean: {target_monthly_dashboard['total_ridership'].mean():.2f}")
            print(f"     Median: {target_monthly_dashboard['total_ridership'].median():.2f}")
        
        print("\n=== MONTHLY AGGREGATION TEST COMPLETED ===")
        
    except Exception as e:
        print(f"Error in test_monthly_aggregation: {e}")
        import traceback
        traceback.print_exc()

def test_data_quality():
    """Test the actual data quality and values"""
    print("=== TESTING BUS DATA QUALITY ===")
    
    try:
        # Load larger samples for better analysis
        print("\n1. Loading larger data samples...")
        
        # Load 10,000 rows from each file for better analysis
        df_2020_2024 = pd.read_csv("bus_2020_2024.csv", nrows=10000)
        df_2025 = pd.read_csv("bus_2025.csv", nrows=10000)
        
        print(f"   Loaded {len(df_2020_2024)} rows from 2020-2024 data")
        print(f"   Loaded {len(df_2025)} rows from 2025 data")
        
        # Check ridership data quality
        print("\n2. Analyzing ridership data quality...")
        
        for df_name, df in [("2020-2024", df_2020_2024), ("2025", df_2025)]:
            print(f"\n   {df_name} dataset:")
            
            # Ridership statistics
            ridership = df['ridership']
            print(f"     Total rows: {len(ridership)}")
            print(f"     Non-zero ridership: {len(ridership[ridership > 0])}")
            print(f"     Zero ridership: {len(ridership[ridership == 0])}")
            print(f"     Ridership range: {ridership.min()} to {ridership.max()}")
            print(f"     Mean ridership: {ridership.mean():.2f}")
            print(f"     Median ridership: {ridership.median():.2f}")
            
            # Check for non-zero ridership samples
            non_zero = df[df['ridership'] > 0]
            if len(non_zero) > 0:
                print(f"     Sample non-zero ridership rows:")
                print(non_zero[['transit_timestamp', 'bus_route', 'ridership']].head())
            else:
                print(f"     WARNING: No non-zero ridership found in sample!")
        
        # Check timestamp ranges
        print("\n3. Analyzing timestamp ranges...")
        
        for df_name, df in [("2020-2024", df_2020_2024), ("2025", df_2025)]:
            print(f"\n   {df_name} dataset:")
            
            # Convert timestamps
            df['datetime'] = pd.to_datetime(df['transit_timestamp'])
            
            print(f"     Date range: {df['datetime'].min()} to {df['datetime'].max()}")
            print(f"     Year range: {df['datetime'].dt.year.min()} to {df['datetime'].dt.year.max()}")
            
            # Check for expected years
            if df_name == "2020-2024":
                expected_years = [2020, 2021, 2022, 2023, 2024]
                actual_years = df['datetime'].dt.year.unique()
                print(f"     Expected years: {expected_years}")
                print(f"     Actual years: {sorted(actual_years)}")
                if not all(year in actual_years for year in expected_years):
                    print(f"     WARNING: Missing expected years!")
            else:  # 2025
                expected_years = [2025]
                actual_years = df['datetime'].dt.year.unique()
                print(f"     Expected years: {expected_years}")
                print(f"     Actual years: {sorted(actual_years)}")
                if 2025 not in actual_years:
                    print(f"     WARNING: 2025 data not found!")
        
        # Check route distribution
        print("\n4. Analyzing route distribution...")
        
        target_routes = [
            'M15', 'M5', 'M1', 'M2', 'M3', 'M4', 'M55', 'M7', 'M20', 'M42', 'M34', 'M22',
            'BxM1', 'BxM2', 'BxM3', 'BxM4', 'BxM11',
            'BM1', 'BM2', 'BM3', 'BM4', 'BM5',
            'QM1', 'QM2', 'QM4', 'QM5', 'QM20',
            'SIM1', 'SIM5', 'SIM6', 'SIM11', 'SIM22', 'SIM25'
        ]
        
        for df_name, df in [("2020-2024", df_2020_2024), ("2025", df_2025)]:
            print(f"\n   {df_name} dataset:")
            
            route_counts = df['bus_route'].value_counts()
            print(f"     Total unique routes: {len(route_counts)}")
            print(f"     Most common routes: {route_counts.head(10).to_dict()}")
            
            # Check target routes with ridership
            target_with_ridership = {}
            for route in target_routes:
                route_data = df[df['bus_route'] == route]
                if len(route_data) > 0:
                    total_ridership = route_data['ridership'].sum()
                    non_zero_count = len(route_data[route_data['ridership'] > 0])
                    target_with_ridership[route] = {
                        'total_rows': len(route_data),
                        'total_ridership': total_ridership,
                        'non_zero_count': non_zero_count
                    }
            
            print(f"     Target routes with data: {len(target_with_ridership)}")
            if target_with_ridership:
                print(f"     Sample target route data:")
                for route, data in list(target_with_ridership.items())[:5]:
                    print(f"       {route}: {data['total_rows']} rows, {data['total_ridership']} total ridership, {data['non_zero_count']} non-zero entries")
        
        print("\n=== DATA QUALITY TEST COMPLETED ===")
        
    except Exception as e:
        print(f"Error in test_data_quality: {e}")
        import traceback
        traceback.print_exc()

def test_data_loading():
    """Test the data loading process step by step"""
    print("=== TESTING BUS DATA LOADING ===")
    
    try:
        # Download files first
        print("\n1. Downloading data files...")
        success_2020 = download_from_gdrive(BUS_2020_2024_URL, "bus_2020_2024.csv")
        success_2025 = download_from_gdrive(BUS_2025_URL, "bus_2025.csv")
        
        if not success_2020 or not success_2025:
            print("Failed to download one or more files. Trying alternative method...")
            # Alternative: try direct pandas read with different parameters
            try:
                print("\n2. Trying direct pandas read for 2020-2024 data...")
                df_2020_2024 = pd.read_csv(BUS_2020_2024_URL, 
                                          nrows=1000, 
                                          on_bad_lines='skip', 
                                          engine='python',
                                          encoding='utf-8')
                print(f"   Successfully loaded {len(df_2020_2024)} rows")
                print(f"   Columns: {df_2020_2024.columns.tolist()}")
            except Exception as e:
                print(f"   Failed to load 2020-2024 data: {e}")
                df_2020_2024 = None
                
            try:
                print("\n3. Trying direct pandas read for 2025 data...")
                df_2025 = pd.read_csv(BUS_2025_URL, 
                                     nrows=1000, 
                                     on_bad_lines='skip', 
                                     engine='python',
                                     encoding='utf-8')
                print(f"   Successfully loaded {len(df_2025)} rows")
                print(f"   Columns: {df_2025.columns.tolist()}")
            except Exception as e:
                print(f"   Failed to load 2025 data: {e}")
                df_2025 = None
        else:
            # Load from downloaded files
            print("\n2. Loading downloaded files...")
            try:
                df_2020_2024 = pd.read_csv("bus_2020_2024.csv", nrows=1000)
                print(f"   Loaded 2020-2024: {len(df_2020_2024)} rows")
                print(f"   Columns: {df_2020_2024.columns.tolist()}")
            except Exception as e:
                print(f"   Failed to load 2020-2024 file: {e}")
                df_2020_2024 = None
                
            try:
                df_2025 = pd.read_csv("bus_2025.csv", nrows=1000)
                print(f"   Loaded 2025: {len(df_2025)} rows")
                print(f"   Columns: {df_2025.columns.tolist()}")
            except Exception as e:
                print(f"   Failed to load 2025 file: {e}")
                df_2025 = None
        
        # Analyze data structure
        if df_2020_2024 is not None:
            print("\n4. Analyzing 2020-2024 data structure...")
            print(f"   Shape: {df_2020_2024.shape}")
            print(f"   Data types: {df_2020_2024.dtypes.to_dict()}")
            print(f"   First few rows:")
            print(df_2020_2024.head())
            
            # Find timestamp column
            timestamp_col_2020 = None
            for col in df_2020_2024.columns:
                if any(keyword in col.lower() for keyword in ['timestamp', 'date', 'time', 'datetime']):
                    timestamp_col_2020 = col
                    break
            
            if timestamp_col_2020:
                print(f"   Found timestamp column: {timestamp_col_2020}")
                print(f"   Sample values: {df_2020_2024[timestamp_col_2020].head().tolist()}")
                
                # Test timestamp parsing
                try:
                    sample_ts = df_2020_2024[timestamp_col_2020].iloc[0]
                    parsed_ts = pd.to_datetime(sample_ts, errors='coerce')
                    print(f"   Timestamp parsing test: '{sample_ts}' -> {parsed_ts}")
                except Exception as e:
                    print(f"   Timestamp parsing failed: {e}")
        
        if df_2025 is not None:
            print("\n5. Analyzing 2025 data structure...")
            print(f"   Shape: {df_2025.shape}")
            print(f"   Data types: {df_2025.dtypes.to_dict()}")
            print(f"   First few rows:")
            print(df_2025.head())
            
            # Find timestamp column
            timestamp_col_2025 = None
            for col in df_2025.columns:
                if any(keyword in col.lower() for keyword in ['timestamp', 'date', 'time', 'datetime']):
                    timestamp_col_2025 = col
                    break
            
            if timestamp_col_2025:
                print(f"   Found timestamp column: {timestamp_col_2025}")
                print(f"   Sample values: {df_2025[timestamp_col_2025].head().tolist()}")
                
                # Test timestamp parsing
                try:
                    sample_ts = df_2025[timestamp_col_2025].iloc[0]
                    parsed_ts = pd.to_datetime(sample_ts, errors='coerce')
                    print(f"   Timestamp parsing test: '{sample_ts}' -> {parsed_ts}")
                except Exception as e:
                    print(f"   Timestamp parsing failed: {e}")
        
        # Check for route and ridership columns
        print("\n6. Checking for route and ridership columns...")
        target_routes = [
            'M15', 'M5', 'M1', 'M2', 'M3', 'M4', 'M55', 'M7', 'M20', 'M42', 'M34', 'M22',
            'BxM1', 'BxM2', 'BxM3', 'BxM4', 'BxM11',
            'BM1', 'BM2', 'BM3', 'BM4', 'BM5',
            'QM1', 'QM2', 'QM4', 'QM5', 'QM20',
            'SIM1', 'SIM5', 'SIM6', 'SIM11', 'SIM22', 'SIM25'
        ]
        
        for df_name, df in [("2020-2024", df_2020_2024), ("2025", df_2025)]:
            if df is not None:
                print(f"\n   {df_name} dataset:")
                # Find route column
                route_col = None
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['route', 'bus', 'line']):
                        route_col = col
                        break
                
                if route_col:
                    routes = set(df[route_col].unique())
                    found_routes = [r for r in target_routes if r in routes]
                    print(f"     Route column: {route_col}")
                    print(f"     Total routes: {len(routes)}")
                    print(f"     Target routes found: {found_routes}")
                
                # Find ridership column
                ridership_col = None
                for col in df.columns:
                    if any(keyword in col.lower() for keyword in ['ridership', 'passenger', 'count', 'volume']):
                        ridership_col = col
                        break
                
                if ridership_col:
                    print(f"     Ridership column: {ridership_col}")
                    print(f"     Ridership range: {df[ridership_col].min()} to {df[ridership_col].max()}")
                    print(f"     Non-null count: {df[ridership_col].count()}")
        
        print("\n=== TEST COMPLETED ===")
        
    except Exception as e:
        print(f"Error in test_data_loading: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the basic loading test first
    test_data_loading()
    
    # Then run the detailed quality test
    print("\n" + "="*50)
    test_data_quality()
    
    # Finally run the monthly aggregation test
    print("\n" + "="*50)
    test_monthly_aggregation() 