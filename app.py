import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc

# 1. Load and preprocess CRZ vehicle entry data --------------------------------------------------

df = pd.read_csv("MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250708.csv")
df["Toll 10 Minute Block"] = pd.to_datetime(df["Toll 10 Minute Block"], format="%m/%d/%Y %I:%M:%S %p")
df["Toll Date"] = pd.to_datetime(df["Toll Date"], format="%m/%d/%Y")
df["Hour"] = df["Toll 10 Minute Block"].dt.hour
df["Minute"] = df["Toll 10 Minute Block"].dt.minute
df["Month"] = df["Toll 10 Minute Block"].dt.month_name()
df["MonthNum"] = df["Toll 10 Minute Block"].dt.month
df["Week"] = df["Toll 10 Minute Block"].dt.isocalendar().week

# Fix month order so plots are sorted chronologically not alphabetically
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
    df[col] = df[col].fillna(default)

# 2. Load and preprocess TAXI monthly reports ----------------------------------------------------

taxi_df = pd.read_csv("data_reports_monthly.csv")
# Parse month / year to a datetime index for easy grouping
# The format in the CSV is YYYY-MM, e.g. 2025-05
# Some rows might have stray spaces, so strip them first

# Clean numeric column (Trips Per Day) – remove commas then convert to float

taxi_df["Trips Per Day"] = (
    taxi_df["Trips Per Day"].astype(str).str.replace(",", "", regex=False).replace("-", pd.NA).astype(float)
)

taxi_df["Date"] = pd.to_datetime(taxi_df["Month/Year"].str.strip(), format="%Y-%m")

taxi_df["Year"] = taxi_df["Date"].dt.year
taxi_df["Month"] = taxi_df["Date"].dt.month_name()

taxi_df["MonthNum"] = taxi_df["Date"].dt.month

license_classes = sorted(taxi_df["License Class"].unique())

# 3. Load and preprocess Bus ridership data ------------------------------------------------------
# NOTE: These two CSV files are large (>2 MB) which exceeds the direct file read limit of the
# automated tooling, therefore we are not reading their contents during development. The code
# below assumes a generic structure with columns «Route», «Timestamp» (or «Date»/«Hour»)
# and «Rides»/«Ridership».  We try to detect the correct column names at run-time so the
# dashboard will still work even if they differ slightly.

def load_bus_csv(path: str) -> pd.DataFrame:
    """Attempt to load the MTA Bus ridership CSV with best-effort column name handling."""
    df_bus = pd.read_csv(path)

    # Try to infer the timestamp column
    date_col_candidates = [
        col
        for col in [
            "Timestamp",
            "Hour",
            "Date",
            "Service Date",
            "Datetime",
            "DateTime",
            "transit_timestamp",
        ]
        if col in df_bus.columns
    ]
    if not date_col_candidates:
        raise ValueError(f"None of the expected date columns found in {path!s}")
    date_col = date_col_candidates[0]

    # Parse to pandas datetime (robust)
    df_bus[date_col] = pd.to_datetime(df_bus[date_col], errors='coerce')
    df_bus = df_bus.dropna(subset=[date_col])  # drop rows where timestamp couldn't be parsed

    # Try to find the ridership column
    ride_col_candidates = [
        col
        for col in [
            "Ridership",
            "ridership",
            "Rides",
            "Entries",
            "Total_Ridership",
            "Bus Ridership",
        ]
        if col in df_bus.columns
    ]
    if not ride_col_candidates:
        raise ValueError(f"None of the expected ridership columns found in {path!s}")
    rides_col = ride_col_candidates[0]

    # Try to find route / line column
    route_col_candidates = [c for c in ["Route", "Line", "Bus Line", "route_id", "bus_route"] if c in df_bus.columns]
    if not route_col_candidates:
        raise ValueError(f"None of the expected route columns found in {path!s}")
    route_col = route_col_candidates[0]

    # Standardise names for convenience
    df_bus = df_bus.rename(
        columns={date_col: "Timestamp", rides_col: "Ridership", route_col: "Route"}
    )

    return df_bus[["Timestamp", "Route", "Ridership"]]


try:
    bus_df_1 = load_bus_csv("MTA_Bus_Hourly_Ridership__2020-2024.csv")
    bus_df_2 = load_bus_csv("MTA_Bus_Hourly_Ridership__Beginning_2025.csv")
    bus_df = pd.concat([bus_df_1, bus_df_2], ignore_index=True)
except Exception as e:
    # If loading fails we still want the dashboard to launch – create an empty placeholder
    print(f"[WARNING] Could not load bus CSV files – {e}")
    bus_df = pd.DataFrame(columns=["Timestamp", "Route", "Ridership"])

if not bus_df.empty:
    bus_df["Year"] = bus_df["Timestamp"].dt.year
    bus_df["Month"] = bus_df["Timestamp"].dt.month_name()
    bus_df["MonthNum"] = bus_df["Timestamp"].dt.month

    bus_monthly = (
        bus_df.groupby(["Route", "Year", "Month", "MonthNum"], as_index=False)["Ridership"].sum()
    )
    bus_lines = sorted(bus_monthly["Route"].unique())
else:
    bus_monthly = pd.DataFrame(columns=["Route", "Year", "Month", "MonthNum", "Ridership"])
    bus_lines = []

# 4. Dash App setup -----------------------------------------------------------------------------
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
server = app.server

vehicle_classes = df["Vehicle Class"].unique()
regions = df["Detection Region"].unique()
detect_groups = df["Detection Group"].unique()

# ------------------------------------------------------------------------------------------------
# Layout
# ------------------------------------------------------------------------------------------------
app.layout = dbc.Container(
    [
        html.H1("MTA CRZ Vehicle Entries Dashboard", className="my-4"),

        # -------------------------------------------------------------------------------------
        # Global filters (apply to the CRZ vehicle-entries dataset only)
        # -------------------------------------------------------------------------------------
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select Vehicle Class(es):"),
                        dcc.Dropdown(
                            options=[{"label": v, "value": v} for v in vehicle_classes],
                            value=list(vehicle_classes),
                            multi=True,
                            id="vehicle-filter",
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        html.Label("Select Region(s):"),
                        dcc.Dropdown(
                            options=[{"label": r, "value": r} for r in regions],
                            value=list(regions),
                            multi=True,
                            id="region-filter",
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        html.Label("Select Detection Group(s):"),
                        dcc.Dropdown(
                            options=[{"label": d, "value": d} for d in detect_groups],
                            value=list(detect_groups),
                            multi=True,
                            id="group-filter",
                        ),
                    ],
                    md=3,
                ),
                dbc.Col(
                    [
                        html.Label("Select Date Range:"),
                        dcc.DatePickerRange(
                            id="date-filter",
                            start_date=df["Toll Date"].min(),
                            end_date=df["Toll Date"].max(),
                            display_format="YYYY-MM-DD",
                        ),
                    ],
                    md=3,
                ),
            ],
            className="mb-4",
        ),

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
                    ]
                ),
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
                    ]
                ),
            ],
            className="mb-4",
        ),

        # -------------------------------------------------------------------------------------
        # Tabs – original + new Taxi & Bus tabs
        # -------------------------------------------------------------------------------------
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
                dbc.Tab(label="Taxi Trends", tab_id="tab-taxi"),
                dbc.Tab(label="Bus Ridership", tab_id="tab-bus"),
            ],
            id="tabs",
            active_tab="tab-ts",
        ),

        html.Div(id="tab-content"),
    ],
    fluid=True,
)

# ------------------------------------------------------------------------------------------------
# Callback – switch between tabs, providing layout (not necessarily the graph itself)
# ------------------------------------------------------------------------------------------------
@app.callback(Output("tab-content", "children"), Input("tabs", "active_tab"))
def render_tab_content(tab):
    if tab == "tab-taxi":
        return html.Div(
            [
                html.Div(
                    [
                        html.Label("Select License Class:"),
                        dcc.Dropdown(
                            id="taxi-license-select",
                            options=[{"label": lc, "value": lc} for lc in license_classes],
                            value=license_classes[0] if license_classes else None,
                            clearable=False,
                        ),
                    ],
                    style={"width": "30%", "display": "inline-block"},
                ),
                html.Div(
                    [
                        html.Label("Select Metric:"),
                        dcc.RadioItems(
                            id="taxi-metric-select",
                            options=[
                                {"label": "Trips Per Day", "value": "trips"},
                                {"label": "% Change (YoY)", "value": "pct"},
                            ],
                            value="trips",
                            labelStyle={"display": "inline-block", "margin-right": "20px"},
                        ),
                    ],
                    style={"margin-left": "40px", "display": "inline-block"},
                ),
                dcc.Graph(id="taxi-graph"),
            ]
        )

    if tab == "tab-bus":
        return html.Div(
            [
                html.Label("Select Bus Line:"),
                dcc.Dropdown(
                    id="bus-line-select",
                    options=[{"label": line, "value": line} for line in bus_lines],
                    value=bus_lines[0] if bus_lines else None,
                    clearable=False,
                ),
                dcc.Graph(id="bus-line-graph"),
            ]
        )

    # All other tabs retain the original behaviour handled by the old callback
    return dash.no_update

# ------------------------------------------------------------------------------------------------
# Callback – original CRZ vehicle entry visualisations (time-series, heatmaps, etc.)
# ------------------------------------------------------------------------------------------------
@app.callback(
    Output("tab-content", "children", allow_duplicate=True),
    [
        Input("tabs", "active_tab"),
        Input("vehicle-filter", "value"),
        Input("region-filter", "value"),
        Input("group-filter", "value"),
        Input("date-filter", "start_date"),
        Input("date-filter", "end_date"),
        Input("value-type", "value"),
        Input("agg-level", "value"),
    ],
    prevent_initial_call=True,
)
def update_existing_tabs(
    tab,
    selected_vehicles,
    selected_regions,
    selected_groups,
    start_date,
    end_date,
    value_type,
    agg_level,
):
    if tab in {"tab-taxi", "tab-bus"}:  # These tabs handled elsewhere
        return dash.no_update

    filtered = df[
        (df["Vehicle Class"].isin(selected_vehicles))
        & (df["Detection Region"].isin(selected_regions))
        & (df["Detection Group"].isin(selected_groups))
        & (df["Toll Date"] >= pd.to_datetime(start_date))
        & (df["Toll Date"] <= pd.to_datetime(end_date))
    ]

    if tab == "tab-ts":
        ts = getattr(filtered.groupby(agg_level)["CRZ Entries"], value_type)().reset_index()
        fig = px.line(ts, x=agg_level, y="CRZ Entries", title=f"{value_type.title()} CRZ Entries by {agg_level}")
        return dcc.Graph(figure=fig)

    elif tab == "tab-peak":
        peak = (
            getattr(filtered.groupby(["Time Period", "Detection Region"])["CRZ Entries"], value_type)()
            .reset_index()
        )
        fig = px.bar(
            peak,
            x="Detection Region",
            y="CRZ Entries",
            color="Time Period",
            barmode="group",
            title=f"{value_type.title()} CRZ Entries: Peak vs Non-Peak by Region",
        )
        return dcc.Graph(figure=fig)

    elif tab == "tab-hm-region":
        heat = (
            getattr(filtered.groupby(["Hour", "Detection Region"])["CRZ Entries"], value_type)()
            .reset_index()
        )
        heat_pivot = heat.pivot(index="Hour", columns="Detection Region", values="CRZ Entries").fillna(0)
        fig = go.Figure(
            data=go.Heatmap(
                z=heat_pivot.values, x=heat_pivot.columns, y=heat_pivot.index, colorscale="Viridis"
            )
        )
        fig.update_layout(
            title=f"{value_type.title()} Hourly CRZ Entries by Region",
            xaxis_title="Region",
            yaxis_title="Hour",
        )
        return dcc.Graph(figure=fig)

    elif tab == "tab-hm-group":
        heat = (
            getattr(filtered.groupby(["Hour", "Detection Group"])["CRZ Entries"], value_type)()
            .reset_index()
        )
        heat_pivot = heat.pivot(index="Hour", columns="Detection Group", values="CRZ Entries").fillna(0)
        fig = go.Figure(
            data=go.Heatmap(
                z=heat_pivot.values, x=heat_pivot.columns, y=heat_pivot.index, colorscale="Cividis"
            )
        )
        fig.update_layout(
            title=f"{value_type.title()} Hourly CRZ Entries by Group",
            xaxis_title="Detection Group",
            yaxis_title="Hour",
        )
        return dcc.Graph(figure=fig)

    elif tab == "tab-bar":
        bar = getattr(filtered.groupby("Vehicle Class")["CRZ Entries"], value_type)().reset_index()
        fig = px.bar(bar, x="Vehicle Class", y="CRZ Entries", title=f"{value_type.title()} CRZ Entries by Vehicle Class")
        return dcc.Graph(figure=fig)

    elif tab == "tab-monthly":
        # For monthly tab we provide a dropdown to choose colour grouping – rendered here
        return html.Div(
            [
                html.Label("Colour Grouping:"),
                dcc.Dropdown(
                    id="monthly-colourby",
                    options=[
                        {"label": "Detection Region", "value": "Detection Region"},
                        {"label": "Detection Group", "value": "Detection Group"},
                    ],
                    value="Detection Region",
                    clearable=False,
                    style={"width": "30%"},
                ),
                dcc.Graph(id="monthly-graph"),
            ]
        )

    elif tab == "tab-std":
        std = filtered.groupby([agg_level])["CRZ Entries"].std().reset_index()
        fig = px.line(std, x=agg_level, y="CRZ Entries", title=f"Standard Deviation of CRZ Entries by {agg_level}")
        return dcc.Graph(figure=fig)

    elif tab == "tab-excluded":
        excl = getattr(filtered.groupby("Toll Date")["Excluded Roadway Entries"], value_type)().reset_index()
        fig = px.line(
            excl,
            x="Toll Date",
            y="Excluded Roadway Entries",
            title=f"{value_type.title()} Excluded Roadway Entries Over Time",
        )
        return html.Div(
            [
                dcc.Graph(figure=fig),
                html.Br(),
                html.A(
                    "Download filtered data as CSV",
                    id="download-link",
                    download="filtered_data.csv",
                    href="data:text/csv;charset=utf-8," + filtered.to_csv(index=False),
                    target="_blank",
                ),
            ]
        )

    return html.Div("Select a tab to view the content.")

# ------------------------------------------------------------------------------------------------
# Callback – Monthly graph (CRZ) – responds to colour grouping dropdown
# ------------------------------------------------------------------------------------------------
@app.callback(
    Output("monthly-graph", "figure"),
    [
        Input("monthly-colourby", "value"),
        Input("vehicle-filter", "value"),
        Input("region-filter", "value"),
        Input("group-filter", "value"),
        Input("date-filter", "start_date"),
        Input("date-filter", "end_date"),
        Input("value-type", "value"),
    ],
    prevent_initial_call=True,
)
def update_monthly_graph(
    colour_by,
    selected_vehicles,
    selected_regions,
    selected_groups,
    start_date,
    end_date,
    value_type,
):
    filtered = df[
        (df["Vehicle Class"].isin(selected_vehicles))
        & (df["Detection Region"].isin(selected_regions))
        & (df["Detection Group"].isin(selected_groups))
        & (df["Toll Date"] >= pd.to_datetime(start_date))
        & (df["Toll Date"] <= pd.to_datetime(end_date))
    ]

    month = (
        getattr(filtered.groupby(["MonthNum", "Month", colour_by])["CRZ Entries"], value_type)()
        .reset_index()
    )
    fig = px.bar(
        month.sort_values("MonthNum"),
        x="Month",
        y="CRZ Entries",
        color=colour_by,
        title=f"{value_type.title()} CRZ Entries by Month and {colour_by}",
    )
    # Place legend on the right-hand side as requested in user preferences
    fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
    return fig

# ------------------------------------------------------------------------------------------------
# Callback – Taxi trends visualisation
# ------------------------------------------------------------------------------------------------
@app.callback(
    Output("taxi-graph", "figure"),
    [Input("taxi-license-select", "value"), Input("taxi-metric-select", "value")],
    prevent_initial_call=True,
)
def update_taxi_graph(selected_license, metric):
    if taxi_df.empty or selected_license is None:
        return go.Figure()

    data = taxi_df[taxi_df["License Class"] == selected_license].copy()
    data = data.sort_values(["Year", "MonthNum"])  # chronological order

    if metric == "trips":
        fig = px.line(
            data,
            x="Date",
            y="Trips Per Day",
            title=f"Trips Per Day – {selected_license}",
        )
    else:  # Year-over-year percentage change
        data["pct_change"] = data["Trips Per Day"].pct_change(periods=12) * 100
        fig = px.bar(
            data,
            x="Date",
            y="pct_change",
            title=f"Year-over-Year % Change – {selected_license}",
        )
        fig.update_yaxes(title="% Change")

    fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
    return fig

# ------------------------------------------------------------------------------------------------
# Callback – Bus ridership visualisation
# ------------------------------------------------------------------------------------------------
@app.callback(
    Output("bus-line-graph", "figure"),
    Input("bus-line-select", "value"),
    prevent_initial_call=True,
)
def update_bus_graph(selected_line):
    if bus_monthly.empty or selected_line is None:
        return go.Figure()

    data = (
        bus_monthly[bus_monthly["Route"] == selected_line]
        .sort_values(["Year", "MonthNum"])
        .copy()
    )
    # Create a combined year-month column for cleaner x-axis
    data["YearMonth"] = pd.to_datetime(
        data["Year"].astype(str) + "-" + data["MonthNum"].astype(str).str.zfill(2) + "-01"
    )

    fig = px.line(
        data,
        x="YearMonth",
        y="Ridership",
        title=f"Monthly Bus Ridership – Route {selected_line}",
    )
    fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
    return fig


if __name__ == "__main__":
    app.run(debug=True)
