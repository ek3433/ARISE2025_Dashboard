import pandas as pd

# Read just the first few rows to check structure
print("Reading CSV structure...")
df_sample = pd.read_csv("MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250708.csv", nrows=1000)

print("\nColumn names:")
print(df_sample.columns.tolist())

print("\nUnique Vehicle Classes:")
print(sorted(df_sample["Vehicle Class"].unique()))

print("\nUnique Detection Groups:")
print(sorted(df_sample["Detection Group"].unique()))

print("\nUnique Detection Regions:")
print(sorted(df_sample["Detection Region"].unique()))

print("\n=== RELATIONSHIP BETWEEN DETECTION REGIONS AND GROUPS ===")
print("\nDetection Groups by Region:")
for region in sorted(df_sample["Detection Region"].unique()):
    groups = sorted(df_sample[df_sample["Detection Region"] == region]["Detection Group"].unique())
    print(f"\n{region}:")
    for group in groups:
        print(f"  - {group}")

print("\nDetection Regions by Group:")
for group in sorted(df_sample["Detection Group"].unique()):
    regions = sorted(df_sample[df_sample["Detection Group"] == group]["Detection Region"].unique())
    print(f"\n{group}:")
    for region in regions:
        print(f"  - {region}")

print("\nSample data (first 5 rows):")
print(df_sample.head()) 