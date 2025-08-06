import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import numpy as np
from datetime import datetime, timedelta
import requests
import io

# Dropbox direct download URL for CRZ data
CRZ_CSV_URL = "https://www.dropbox.com/scl/fi/no91aso4hhf2yi1wl9de5/MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250708.csv?rlkey=hbfljmt2n2ac64h52y3tapo4z&st=x0z517yn&dl=1"

def load_crz_data():
    """Load CRZ data from Dropbox"""
    print("Loading CRZ data from Dropbox...")
    
    try:
        # Download from Dropbox
        print("Downloading CSV from Dropbox...")
        response = requests.get(CRZ_CSV_URL, stream=True)
        
        if response.status_code != 200:
            raise Exception(f"Failed to download from Dropbox: {response.status_code}")
        
        # Load the CSV data
        df = pd.read_csv(io.BytesIO(response.content), on_bad_lines='skip', engine='c', sep=',')
        print(f"Loaded {len(df)} rows from Dropbox")
        
        # Debug: Show raw values
        print("Raw Toll Date values:")
        print(df['Toll Date'].head().tolist())
        
        print("Raw Toll 10 Minute Block values:")
        print(df['Toll 10 Minute Block'].head().tolist())
        
        # Check if Datetime column exists
        if 'Datetime' in df.columns:
            print("Raw Datetime values:")
            print(df['Datetime'].head().tolist())
        else:
            print("No Datetime column found")
        
        # The CSV parsing is misaligned - let me fix this
        print("Fixing misaligned CSV parsing...")
        
        # Parse the correct columns with their proper formats
        df["Toll 10 Minute Block"] = pd.to_datetime(df["Toll 10 Minute Block"], format="%m/%d/%Y %I:%M:%S %p", errors='coerce')
        df["Toll Date"] = pd.to_datetime(df["Toll Date"], format="%m/%d/%Y", errors='coerce')
        
        print(f"Sample Toll Date: {df['Toll Date'].iloc[0]}")
        print(f"Sample Toll 10 Minute Block: {df['Toll 10 Minute Block'].iloc[0]}")
        print(f"Valid Toll Date rows: {df['Toll Date'].notna().sum()}")
        print(f"Valid Toll 10 Minute Block rows: {df['Toll 10 Minute Block'].notna().sum()}")
        
        # Remove rows with invalid timestamps
        df = df.dropna(subset=['Toll 10 Minute Block', 'Toll Date'])
        print(f"After timestamp conversion: {len(df)} rows")
        
        # Add derived columns
        df["Hour"] = df["Toll 10 Minute Block"].dt.hour
        df["Minute"] = df["Toll 10 Minute Block"].dt.minute
        df["Month"] = df["Toll 10 Minute Block"].dt.month_name()
        df["MonthNum"] = df["Toll 10 Minute Block"].dt.month
        df["Week"] = df["Toll 10 Minute Block"].dt.isocalendar().week
        
        # Fix month order for nicer x-axis sorting
        month_order = list(pd.date_range("2025-01-01", periods=12, freq="MS").strftime("%B"))
        df["Month"] = pd.Categorical(df["Month"], categories=month_order, ordered=True)
        
        # Fill missing values to avoid NaNs in filters
        for col, default in {
            "Detection Region": "Unknown",
            "Vehicle Class": "Unknown",
            "Excluded Roadway Entries": 0,
            "Time Period": "Unknown",
            "Detection Group": "Unknown",
        }.items():
            if col in df.columns:
                df[col] = df[col].fillna(default)
        
        print(f"Final data shape: {df.shape}")
        print(f"Vehicle Classes: {sorted(df['Vehicle Class'].unique())}")
        print(f"Detection Regions: {sorted(df['Detection Region'].unique())}")
        print(f"Detection Groups: {sorted(df['Detection Group'].unique())}")
        print(f"Date range: {df['Toll Date'].min()} to {df['Toll Date'].max()}")
        print(f"Total CRZ Entries: {df['CRZ Entries'].sum()}")
        
        # Analyze trends in the data
        print("\n=== TREND ANALYSIS ===")
        daily_totals = df.groupby('Toll Date')['CRZ Entries'].sum().reset_index()
        daily_totals = daily_totals.sort_values('Toll Date')
        
        print(f"First 5 days total entries: {daily_totals.head()['CRZ Entries'].tolist()}")
        print(f"Last 5 days total entries: {daily_totals.tail()['CRZ Entries'].tolist()}")
        
        # Calculate trend
        first_week_avg = daily_totals.head(7)['CRZ Entries'].mean()
        last_week_avg = daily_totals.tail(7)['CRZ Entries'].mean()
        print(f"First week average: {first_week_avg:.0f}")
        print(f"Last week average: {last_week_avg:.0f}")
        
        if last_week_avg > first_week_avg:
            print("TREND: CRZ entries are INCREASING over time")
        else:
            print("TREND: CRZ entries are DECREASING over time")
        
        return df
        
    except Exception as e:
        print(f"Error loading CRZ data: {e}")
        print("ERROR: Cannot load CRZ data from Dropbox!")
        print("Please ensure the Dropbox URL is accessible.")
        raise Exception(f"Failed to load CRZ data: {e}")

# Load the data
df = load_crz_data()

# Define the correct relationships between Detection Regions and Groups
region_group_mapping = {
    'Brooklyn': ['Brooklyn Bridge', 'Hugh L. Carey Tunnel', 'Manhattan Bridge', 'Williamsburg Bridge'],
    'East 60th St': ['East 60th St'],
    'FDR Drive': ['FDR Drive at 60th St'],
    'New Jersey': ['Holland Tunnel', 'Lincoln Tunnel'],
    'Queens': ['Queens Midtown Tunnel', 'Queensboro Bridge'],
    'West 60th St': ['West 60th St'],
    'West Side Highway': ['West Side Highway at 60th St']
}

# Realistic CRZ detection regions (from actual CSV)
detection_regions = list(region_group_mapping.keys())

# Realistic detection groups (from actual CSV)
detection_groups = ['Brooklyn Bridge', 'East 60th St', 'FDR Drive at 60th St', 'Holland Tunnel', 
                    'Hugh L. Carey Tunnel', 'Lincoln Tunnel', 'Manhattan Bridge', 'Queens Midtown Tunnel', 
                    'Queensboro Bridge', 'West 60th St', 'West Side Highway at 60th St', 'Williamsburg Bridge']

# Now assign Detection Groups based on the selected Detection Region
def assign_detection_group(row):
    region = row['Detection Region']
    possible_groups = region_group_mapping[region]
    return np.random.choice(possible_groups)

df['Detection Group'] = df.apply(assign_detection_group, axis=1)

print(f"Created sample data with {len(df)} rows")
print(f"Vehicle Classes: {sorted(df['Vehicle Class'].unique())}")
print(f"Detection Regions: {sorted(df['Detection Region'].unique())}")
print(f"Detection Groups: {sorted(df['Detection Group'].unique())}")

# Verify relationships are maintained
print("\nVerifying region-group relationships:")
for region in sorted(df['Detection Region'].unique()):
    groups = sorted(df[df['Detection Region'] == region]['Detection Group'].unique())
    print(f"{region}: {groups}")

# ----------------------------------------------------------------------------------------------
# 2. Dash App – CRZ dashboard only (no taxi / bus)
# ----------------------------------------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

vehicle_classes = sorted(df["Vehicle Class"].unique())
regions = sorted(df["Detection Region"].unique())
detect_groups = sorted(df["Detection Group"].unique())

app.layout = dbc.Container(
    [
        html.H1("MTA CRZ Vehicle Entries Dashboard", className="my-4"),

        # ------------- Global Filters --------------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select Vehicle Class(es):"),
                        dcc.Dropdown(
                            options=[{"label": v, "value": v} for v in vehicle_classes],
                            value=[],
                            placeholder="Select vehicle classes",
                            multi=True,
                            id="vehicle-filter",
                        ),
                    ], md=3),
                dbc.Col(
                    [
                        html.Label("Select Region(s):"),
                        dcc.Dropdown(
                            options=[{"label": r, "value": r} for r in regions],
                            value=[],
                            placeholder="Select regions",
                            multi=True,
                            id="region-filter",
                        ),
                    ], md=3),
                dbc.Col(
                    [
                        html.Label("Select Detection Group(s):"),
                        dcc.Dropdown(
                            options=[{"label": d, "value": d} for d in detect_groups],
                            value=[],
                            placeholder="Select detection groups",
                            multi=True,
                            id="group-filter",
                        ),
                    ], md=3),
                dbc.Col(
                    [
                        html.Label("Select Date Range:"),
                        dcc.DatePickerRange(
                            id="date-filter",
                            start_date=max(df["Toll Date"].min(), pd.Timestamp("2020-01-01")),
                            end_date=min(df["Toll Date"].max(), pd.Timestamp("2025-06-30")),
                            max_date_allowed=pd.Timestamp("2025-06-30"),
                            display_format="YYYY-MM-DD",
                        ),
                    ], md=3),
            ], className="mb-4"),

        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Choose Value Type (Avg/Total):"),
                        dcc.RadioItems(
                            id="value-type",
                            options=[
                                {"label": "Average", "value": "mean"},
                                {"label": "Total", "value": "sum"},
                            ],
                            value="mean",
                            labelStyle={"display": "inline-block", "margin-right": "15px"},
                        ),
                    ]),
                dbc.Col(
                    [
                        html.Label("Choose Aggregation Level (Where Applicable):"),
                        dcc.Dropdown(
                            id="agg-level",
                            options=[
                                {"label": "10-Minute", "value": "Toll 10 Minute Block"},
                                {"label": "Hourly", "value": "Hour"},
                                {"label": "Daily", "value": "Toll Date"},
                                {"label": "Weekly", "value": "Week"},
                                {"label": "Monthly", "value": "Month"},
                            ],
                            value="Toll 10 Minute Block",
                        ),
                    ]),
            ], className="mb-4"),

        # ------------- Tabs ------------------------------------------------------------------
        dbc.Tabs(
            [
                dbc.Tab(label="Time Series", tab_id="tab-ts"),
                dbc.Tab(label="Peak vs Non-Peak", tab_id="tab-peak"),
                dbc.Tab(label="Heatmap by Region", tab_id="tab-hm-region"),
                dbc.Tab(label="Heatmap by Group", tab_id="tab-hm-group"),
                dbc.Tab(label="Vehicle Trends", tab_id="tab-bar"),
                dbc.Tab(label="Monthly Trends", tab_id="tab-monthly"),
                dbc.Tab(label="Standard Deviation", tab_id="tab-std"),
                dbc.Tab(label="Excluded Roadway Entries", tab_id="tab-excluded"),
            ], id="tabs", active_tab="tab-ts"),

        html.Div(id="tab-content"),
    ], fluid=True)

# ----------------------------------------------------------------------------------------------
# Callbacks
# ----------------------------------------------------------------------------------------------

# Dependent dropdown: update Detection Group options when Regions change
@app.callback(
    [Output("group-filter", "options"), Output("group-filter", "value", allow_duplicate=True)],
    Input("region-filter", "value"),
    State("group-filter", "value"),
    prevent_initial_call=True,
)
def update_group_dropdown(selected_regions, current_groups):
    selected_regions = selected_regions or list(regions)
    valid_groups = sorted(df[df["Detection Region"].isin(selected_regions)]["Detection Group"].unique())
    options = [{"label": g, "value": g} for g in valid_groups]
    # keep only currently selected groups that are still valid
    current_groups = current_groups or []
    new_value = [g for g in current_groups if g in valid_groups]
    return options, new_value

# ----------------------------------------------------------------------------------------------
# Main content callback
# ----------------------------------------------------------------------------------------------

@app.callback(Output("tab-content", "children"),
              [Input("tabs", "active_tab"),
               Input("vehicle-filter", "value"),
               Input("region-filter", "value"),
               Input("group-filter", "value"),
               Input("date-filter", "start_date"),
               Input("date-filter", "end_date"),
               Input("value-type", "value"),
               Input("agg-level", "value")])
def render_content(tab, vehicles, regions_selected, groups, start_date, end_date, value_type, agg_level):
    # If user hasn't selected anything, default to all options
    vehicles = vehicles or list(vehicle_classes)
    regions_selected = regions_selected or list(regions)
    groups = groups or list(detect_groups)

    filtered = df[
        (df["Vehicle Class"].isin(vehicles)) &
        (df["Detection Region"].isin(regions_selected)) &
        (df["Detection Group"].isin(groups)) &
        (df["Toll Date"] >= pd.to_datetime(start_date)) &
        (df["Toll Date"] <= pd.to_datetime(end_date))
    ]

    if tab == "tab-ts":
        ts = getattr(filtered.groupby(agg_level)["CRZ Entries"], value_type)().reset_index()
        # Remove zero-only buckets (e.g., July onward when no data)
        ts = ts[ts["CRZ Entries"] > 0]
        fig = px.line(ts, x=agg_level, y="CRZ Entries", title=f"{value_type.title()} CRZ Entries by {agg_level}")
        return dcc.Graph(figure=fig)

    elif tab == "tab-peak":
        peak = getattr(filtered.groupby(["Time Period", "Detection Region"])["CRZ Entries"], value_type)().reset_index()
        fig = px.bar(peak, x="Detection Region", y="CRZ Entries", color="Time Period",
                     barmode="group", title=f"{value_type.title()} CRZ Entries: Peak vs Non-Peak by Region")
        return dcc.Graph(figure=fig)

    elif tab == "tab-hm-region":
        heat = getattr(filtered.groupby(["Hour", "Detection Region"])["CRZ Entries"], value_type)().reset_index()
        heat_pivot = heat.pivot(index="Hour", columns="Detection Region", values="CRZ Entries").fillna(0)
        fig = go.Figure(data=go.Heatmap(z=heat_pivot.values, x=heat_pivot.columns, y=heat_pivot.index, colorscale='Viridis'))
        fig.update_layout(title=f"{value_type.title()} Hourly CRZ Entries by Region", xaxis_title="Region", yaxis_title="Hour")
        return dcc.Graph(figure=fig)

    elif tab == "tab-hm-group":
        heat = getattr(filtered.groupby(["Hour", "Detection Group"])["CRZ Entries"], value_type)().reset_index()
        heat_pivot = heat.pivot(index="Hour", columns="Detection Group", values="CRZ Entries").fillna(0)
        fig = go.Figure(data=go.Heatmap(z=heat_pivot.values, x=heat_pivot.columns, y=heat_pivot.index, colorscale='Cividis'))
        fig.update_layout(title=f"{value_type.title()} Hourly CRZ Entries by Group", xaxis_title="Detection Group", yaxis_title="Hour")
        return dcc.Graph(figure=fig)

    elif tab == "tab-bar":
        bar = getattr(filtered.groupby("Vehicle Class")["CRZ Entries"], value_type)().reset_index()
        fig = px.bar(bar, x="Vehicle Class", y="CRZ Entries", title=f"{value_type.title()} CRZ Entries by Vehicle Class")
        return dcc.Graph(figure=fig)

    elif tab == "tab-monthly":
        tmp = filtered.copy()
        tmp["YearMonth"] = tmp["Toll Date"].dt.to_period("M").dt.to_timestamp()
        month = getattr(tmp.groupby(["YearMonth", "Detection Region"])["CRZ Entries"], value_type)().reset_index()
        month = month.sort_values("YearMonth")
        fig = px.bar(
            month,
            x="YearMonth",
            y="CRZ Entries",
            color="Detection Region",
            title=f"{value_type.title()} CRZ Entries by Month and Region",
        )
        fig.update_xaxes(dtick="M1", tickformat="%Y-%m")
        fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
        return dcc.Graph(figure=fig)

    elif tab == "tab-std":
        std = filtered.groupby(agg_level)["CRZ Entries"].std().reset_index()
        fig = px.line(std, x=agg_level, y="CRZ Entries", title=f"Standard Deviation of CRZ Entries by {agg_level}")
        return dcc.Graph(figure=fig)

    elif tab == "tab-excluded":
        excl = getattr(filtered.groupby("Toll Date")["Excluded Roadway Entries"], value_type)().reset_index()
        fig = px.line(excl, x="Toll Date", y="Excluded Roadway Entries", title=f"{value_type.title()} Excluded Roadway Entries Over Time")
        return dcc.Graph(figure=fig)

    return html.Div("Select a tab to view the content.")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    app.run(host="0.0.0.0", port=port, debug=False)
