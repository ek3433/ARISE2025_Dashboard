import os
from pathlib import Path

import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# ----------------------------------------------------------------------------------------------
# 1. Load pre-aggregated BUS ridership data
# ----------------------------------------------------------------------------------------------

PARQUET_FILE = "bus_monthly.parquet"

if not pathlib.Path(PARQUET_FILE).exists():
    raise FileNotFoundError(
        f"{PARQUET_FILE} is missing. Run the pre-aggregation script locally and commit the file."
    )

bus_monthly = pd.read_parquet(PARQUET_FILE)

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

# Only keep Manhattan + express routes of interest
wanted_lines = [
    "M15", "M5", "M1", "M2", "M3", "M4", "M55", "M7", "M20", "M42", "M34", "M22",
    "BxM1", "BxM2", "BxM3", "BxM4", "BxM11",
    "BM1", "BM2", "BM3", "BM4", "BM5",
    "QM1", "QM2", "QM4", "QM5", "QM20",
    "SIM1", "SIM5", "SIM6", "SIM11", "SIM22", "SIM25",
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
    if line is None or bus_monthly.empty:
        return {}

    data = bus_monthly[bus_monthly["Route"] == line].copy()
    if start_date and end_date:
        data = data[(data["YearMonth"] >= pd.to_datetime(start_date)) & (data["YearMonth"] <= pd.to_datetime(end_date))]
    data = data.sort_values(["Year", "MonthNum"])
    data["YearMonth"] = pd.to_datetime(
        data["Year"].astype(str) + "-" + data["MonthNum"].astype(str).str.zfill(2) + "-01"
    )

    if metric == "abs":
        fig = px.line(
            data, x="YearMonth", y="Ridership", title=f"Monthly Bus Ridership – Route {line}"
        )
    else:
        data["pct_change"] = data["Ridership"].pct_change(periods=12) * 100
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
