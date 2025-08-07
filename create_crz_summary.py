import pandas as pd
import requests
import io
import numpy as np

# Dropbox direct download URL for CRZ data
CRZ_CSV_URL = "https://www.dropbox.com/scl/fi/no91aso4hhf2yi1wl9de5/MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250708.csv?rlkey=hbfljmt2n2ac64h52y3tapo4z&st=x0z517yn&dl=1"

def create_crz_summary():
    """Download CRZ data from Dropbox and create optimized summary"""
    print("Downloading and processing CRZ data...")
    
    try:
        # Download from Dropbox
        print("Downloading CRZ data from Dropbox...")
        response = requests.get(CRZ_CSV_URL, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download from Dropbox: {response.status_code}")
        
        # Load the CSV data
        df = pd.read_csv(io.BytesIO(response.content), on_bad_lines='skip', engine='c', sep=',')
        print(f"Loaded {len(df):,} rows from Dropbox")
        print(f"Columns: {df.columns.tolist()}")
        
        # Parse timestamps
        print("Converting timestamps...")
        df["Toll 10 Minute Block"] = pd.to_datetime(df["Toll 10 Minute Block"], format="%m/%d/%Y %I:%M:%S %p", errors='coerce')
        df["Toll Date"] = pd.to_datetime(df["Toll Date"], format="%m/%d/%Y", errors='coerce')
        
        # Remove invalid timestamps
        df = df.dropna(subset=['Toll 10 Minute Block', 'Toll Date'])
        print(f"After timestamp conversion: {len(df):,} rows")
        
        # Add derived columns using existing columns
        df["Year"] = df["Toll Date"].dt.year
        df["Month"] = df["Toll Date"].dt.month_name()
        df["MonthNum"] = df["Toll Date"].dt.month
        
        # Use existing columns that are already in the data
        # 'Hour of Day' is already there, 'Day of Week' is already there, etc.
        
        # Fix month order
        month_order = list(pd.date_range("2025-01-01", periods=12, freq="MS").strftime("%B"))
        df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)
        
        # Fill missing values
        for col, default in {
            "Detection Region": "Unknown",
            "Vehicle Class": "Unknown",
            "Excluded Roadway Entries": 0,
            "Time Period": "Unknown",
            "Detection Group": "Unknown",
        }.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)
        
        print("Creating optimized aggregations...")
        
        # Create multiple aggregation levels to reduce memory usage
        # 1. Hourly aggregation by region and vehicle class
        hourly_agg = df.groupby([
            'Toll Date', 'Hour of Day', 'Detection Region', 'Vehicle Class', 'Detection Group'
        ])['CRZ Entries'].sum().reset_index()
        hourly_agg = hourly_agg.rename(columns={'Hour of Day': 'Hour'})
        
        # 2. Daily aggregation by region and vehicle class
        daily_agg = df.groupby([
            'Toll Date', 'Detection Region', 'Vehicle Class', 'Detection Group', 'Time Period'
        ])['CRZ Entries'].sum().reset_index()
        
        # 3. Weekly aggregation
        weekly_agg = df.groupby([
            'Year', 'Toll Week', 'Detection Region', 'Vehicle Class', 'Detection Group'
        ])['CRZ Entries'].sum().reset_index()
        weekly_agg = weekly_agg.rename(columns={'Toll Week': 'Week'})
        
        # 4. Monthly aggregation
        monthly_agg = df.groupby([
            'Year', 'MonthNum', 'Month', 'Detection Region', 'Vehicle Class', 'Detection Group'
        ])['CRZ Entries'].sum().reset_index()
        
        # 5. Excluded entries aggregation
        excluded_agg = df.groupby(['Toll Date'])['Excluded Roadway Entries'].sum().reset_index()
        
        print(f"Created aggregations:")
        print(f"  - Hourly: {len(hourly_agg):,} rows")
        print(f"  - Daily: {len(daily_agg):,} rows")
        print(f"  - Weekly: {len(weekly_agg):,} rows")
        print(f"  - Monthly: {len(monthly_agg):,} rows")
        print(f"  - Excluded: {len(excluded_agg):,} rows")
        
        # Save all aggregations to separate files
        hourly_agg.to_csv('crz_hourly_summary.csv', index=False)
        daily_agg.to_csv('crz_daily_summary.csv', index=False)
        weekly_agg.to_csv('crz_weekly_summary.csv', index=False)
        monthly_agg.to_csv('crz_monthly_summary.csv', index=False)
        excluded_agg.to_csv('crz_excluded_summary.csv', index=False)
        
        # Show file sizes
        import os
        files = ['crz_hourly_summary.csv', 'crz_daily_summary.csv', 'crz_weekly_summary.csv', 
                'crz_monthly_summary.csv', 'crz_excluded_summary.csv']
        
        total_size = 0
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file) / (1024 * 1024)  # MB
                total_size += size
                print(f"  {file}: {size:.2f} MB")
        
        print(f"Total size: {total_size:.2f} MB")
        print("All CRZ summary files created successfully!")
        
        return {
            'hourly': hourly_agg,
            'daily': daily_agg,
            'weekly': weekly_agg,
            'monthly': monthly_agg,
            'excluded': excluded_agg
        }
        
    except Exception as e:
        print(f"Error processing CRZ data: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    create_crz_summary() 