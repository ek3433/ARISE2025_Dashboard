import os
from pathlib import Path
import numpy as np

import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# ----------------------------------------------------------------------------------------------
# 1. Load BUS ridership data from Google Drive
# ----------------------------------------------------------------------------------------------

# Google Drive URLs for bus data
BUS_2020_2024_URL = "https://drive.google.com/uc?export=download&id=15LJHuu9oleo_3R7ugYDu_akNHMX6AvLF"
BUS_2025_URL = "https://drive.google.com/uc?export=download&id=1BJbjV4vcx31dMOY2f3YlJ-r1ot3WG8nG"

def load_bus_data():
    """Load bus data from Google Drive with error handling"""
    print("Loading bus data from Google Drive...")
    
    try:
        # Load 2020-2024 data
        print("Loading 2020-2024 data...")
        df_2020_2024 = pd.read_csv(BUS_2020_2024_URL, nrows=50000)  # Load more data
        print(f"Loaded {len(df_2020_2024)} rows from 2020-2024 data")
        print(f"Columns: {df_2020_2024.columns.tolist()}")
        
        # Load 2025 data
        print("Loading 2025 data...")
        df_2025 = pd.read_csv(BUS_2025_URL, nrows=50000)  # Load more data
        print(f"Loaded {len(df_2025)} rows from 2025 data")
        print(f"Columns: {df_2025.columns.tolist()}")
        
        # Handle different timestamp formats
        print("Converting timestamps...")
        
        # 2020-2024 data: format like "10/23/2024 1:00"
        df_2020_2024['transit_timestamp'] = pd.to_datetime(df_2020_2024['transit_timestamp'], format='%m/%d/%Y %H:%M', errors='coerce')
        
        # 2025 data: format like "01/02/2025 07:00:00 AM"
        df_2025['transit_timestamp'] = pd.to_datetime(df_2025['transit_timestamp'], format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
        
        # Remove rows with invalid timestamps
        df_2020_2024 = df_2020_2024.dropna(subset=['transit_timestamp'])
        df_2025 = df_2025.dropna(subset=['transit_timestamp'])
        
        print(f"After timestamp conversion - 2020-2024: {len(df_2020_2024)} rows, 2025: {len(df_2025)} rows")
        
        # Combine datasets
        df_combined = pd.concat([df_2020_2024, df_2025], ignore_index=True)
        print(f"Combined data shape: {df_combined.shape}")
        
        # Create monthly aggregation
        df_combined['Year'] = df_combined['transit_timestamp'].dt.year
        df_combined['Month'] = df_combined['transit_timestamp'].dt.month
        df_combined['YearMonth'] = df_combined['transit_timestamp'].dt.to_period('M').dt.to_timestamp()
        
        # Aggregate by month and route
        bus_monthly = df_combined.groupby(['bus_route', 'Year', 'Month', 'YearMonth'])['ridership'].sum().reset_index()
        bus_monthly = bus_monthly.rename(columns={'bus_route': 'Route'})
        
        print(f"Created monthly data with {len(bus_monthly)} rows")
        print(f"Available routes: {sorted(bus_monthly['Route'].unique())[:10]}...")
        print(f"Date range: {bus_monthly['YearMonth'].min()} to {bus_monthly['YearMonth'].max()}")
        print(f"Ridership range: {bus_monthly['Ridership'].min()} to {bus_monthly['Ridership'].max()}")
        
        return bus_monthly
        
    except Exception as e:
        print(f"Error loading bus data: {e}")
        print("Creating sample bus data...")
        
        # Create sample data as fallback
        dates = pd.date_range('2020-01-01', '2025-06-30', freq='M')
        sample_routes = ['M15', 'M5', 'M1', 'M2', 'M3', 'M4', 'M55', 'M7', 'M20', 'M42', 'M34', 'M22',
                        'BxM1', 'BxM2', 'BxM3', 'BxM4', 'BxM11', 'BM1', 'BM2', 'BM3', 'BM4', 'BM5',
                        'QM1', 'QM2', 'QM4', 'QM5', 'QM20', 'SIM1', 'SIM5', 'SIM6', 'SIM11', 'SIM22', 'SIM25']
        
        sample_data = []
        for date in dates:
            for route in sample_routes:
                sample_data.append({
                    'Route': route,
                    'Year': date.year,
                    'Month': date.month,
                    'YearMonth': date,
                    'Ridership': np.random.randint(1000, 50000)
                })
        
        bus_monthly = pd.DataFrame(sample_data)
        print(f"Created sample data with {len(bus_monthly)} rows")
        return bus_monthly

# Load the data
bus_monthly = load_bus_data()

def map_borough(route):
    if route.startswith("BxM"):
        return "Bronx"
    elif route.startswith("BM"):
        return "Brooklyn"
    elif route.startswith("QM"):
        return "Queens"
    elif route.startswith("SIM"):
        return "Staten Island"
    else:
        return "Manhattan"

if not bus_monthly.empty and "Borough" not in bus_monthly.columns:
    bus_monthly["Borough"] = bus_monthly["Route"].apply(map_borough)

if not bus_monthly.empty and "YearMonth" not in bus_monthly.columns:
    bus_monthly["YearMonth"] = pd.to_datetime(
        bus_monthly["Year"].astype(str) + "-" + bus_monthly["MonthNum"].astype(str).str.zfill(2) + "-01"
    )

# Only keep Manhattan + express routes of interest (matching user's target_routes)
wanted_lines = [
    # Local Manhattan routes
    'M15', 'M5', 'M1', 'M2', 'M3', 'M4', 'M55', 'M7', 'M20', 'M42', 'M34', 'M22',
    # Express routes
    'BxM1', 'BxM2', 'BxM3', 'BxM4', 'BxM11',
    'BM1', 'BM2', 'BM3', 'BM4', 'BM5',
    'QM1', 'QM2', 'QM4', 'QM5', 'QM20',
    'SIM1', 'SIM5', 'SIM6', 'SIM11', 'SIM22', 'SIM25'
]

bus_lines_all = [l for l in wanted_lines if l in bus_monthly["Route"].unique()]

boroughs = ["Manhattan", "Bronx", "Brooklyn", "Queens", "Staten Island"]

bus_lines = bus_lines_all.copy()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# ----------------------------------------------------------------------------------------------
# Dependent dropdown: update bus-line options when borough selection changes
@app.callback(
    [Output("bus-line-select", "options"), Output("bus-line-select", "value", allow_duplicate=True)],
    Input("bus-borough-select", "value"),
    State("bus-line-select", "value"),
    prevent_initial_call=True,
)
def update_line_dropdown(selected_boroughs, current_line):
    selected_boroughs = selected_boroughs or boroughs
    valid_lines = [l for l in bus_lines_all if map_borough(l) in selected_boroughs]
    options = [{"label": l, "value": l} for l in valid_lines]
    new_value = current_line if current_line in valid_lines else (valid_lines[0] if valid_lines else None)
    return options, new_value

# ----------------------------------------------------------------------------------------------
# 2. Dash – Bus Ridership dashboard
# ----------------------------------------------------------------------------------------------

app.layout = dbc.Container(
    [
        html.H2("MTA Bus – Monthly Ridership Dashboard", className="my-4"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Borough:"),
                        dcc.Dropdown(
                            id="bus-borough-select",
                            options=[{"label": b, "value": b} for b in boroughs],
                            value=boroughs,
                            multi=True,
                            clearable=False,
                        ),
                    ], md=3,
                ),
                dbc.Col(
                    [
                        html.Label("Select Bus Line:"),
                        dcc.Dropdown(
                            id="bus-line-select",
                            options=[{"label": l, "value": l} for l in bus_lines],
                            value=bus_lines[0] if bus_lines else None,
                            clearable=False,
                        ),
                    ], md=4,
                ),
                dbc.Col(
                    [
                        html.Label("Date Range:"),
                        dcc.DatePickerRange(
                            id="bus-date-picker",
                            start_date=max(bus_monthly["YearMonth"].min(), pd.Timestamp("2020-01-01")) if not bus_monthly.empty else pd.Timestamp("2020-01-01"),
                            end_date=min(bus_monthly["YearMonth"].max(), pd.Timestamp("2025-06-30")) if not bus_monthly.empty else pd.Timestamp("2025-06-30"),
                            max_date_allowed=pd.Timestamp("2025-06-30"),
                            display_format="YYYY-MM-DD",
                        ),
                    ], md=6,
                ),
            ],
            className="mb-4",
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Metric:"),
                        dcc.RadioItems(
                            id="bus-metric-select",
                            options=[
                                {"label": "Ridership", "value": "abs"},
                                {"label": "% Change YoY", "value": "pct"},
                            ],
                            value="abs",
                            labelStyle={"display": "inline-block", "margin-right": "20px"},
                        ),
                    ], md=6),
            ],
            className="mb-4",
        ),
        dcc.Graph(id="bus-graph"),
    ], fluid=True)


@app.callback(
    Output("bus-graph", "figure"),
    [
        Input("bus-line-select", "value"),
        Input("bus-date-picker", "start_date"),
        Input("bus-date-picker", "end_date"),
        Input("bus-borough-select", "value"),
        Input("bus-metric-select", "value"),
    ],
)
def update_bus_graph(line, start_date, end_date, selected_boroughs, metric):
    print(f"Updating graph for line: {line}, metric: {metric}")
    print(f"Data shape: {bus_monthly.shape}")
    print(f"Available routes: {sorted(bus_monthly['Route'].unique())[:5]}...")
    print(f"Data date range: {bus_monthly['YearMonth'].min()} to {bus_monthly['YearMonth'].max()}")
    print(f"Data ridership range: {bus_monthly['Ridership'].min()} to {bus_monthly['Ridership'].max()}")
    
    if line is None or bus_monthly.empty:
        print("No line selected or data is empty")
        return {}

    # Check if the route exists in data
    if line not in bus_monthly['Route'].unique():
        print(f"Route {line} not found in data")
        print(f"Available routes: {sorted(bus_monthly['Route'].unique())}")
        return {}

    data = bus_monthly[bus_monthly["Route"] == line].copy()
    print(f"Filtered data for {line}: {len(data)} rows")
    print(f"Route {line} ridership range: {data['Ridership'].min()} to {data['Ridership'].max()}")
    
    if start_date and end_date:
        data = data[(data["YearMonth"] >= pd.to_datetime(start_date)) & (data["YearMonth"] <= pd.to_datetime(end_date))]
        print(f"After date filtering: {len(data)} rows")
    
    if len(data) == 0:
        print("No data after filtering")
        return {}
    
    # Sort by year and month
    data = data.sort_values(["Year", "Month"])
    
    # Ensure YearMonth is properly formatted
    if "YearMonth" not in data.columns or data["YearMonth"].isna().all():
        data["YearMonth"] = pd.to_datetime(data["Year"].astype(str) + "-" + data["Month"].astype(str).str.zfill(2) + "-01")

    print(f"Final data for plotting: {len(data)} rows")
    print(f"Date range: {data['YearMonth'].min()} to {data['YearMonth'].max()}")
    print(f"Ridership values: {data['Ridership'].tolist()}")

    if metric == "abs":
        fig = px.line(
            data, x="YearMonth", y="Ridership", title=f"Monthly Bus Ridership – Route {line}"
        )
        fig.update_yaxes(title="Total Ridership")
    else:
        data["pct_change"] = data["Ridership"].pct_change(periods=12) * 100
        data = data.dropna(subset=["pct_change"])  # Remove NaN values
        if len(data) == 0:
            print("No data for percentage change")
            return {}
        fig = px.bar(
            data, x="YearMonth", y="pct_change", title=f"Year-over-Year % Change – Route {line}"
        )
        fig.update_yaxes(title="% Change")

    fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
    return fig


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8052))
    app.run(host="0.0.0.0", port=port, debug=False)
