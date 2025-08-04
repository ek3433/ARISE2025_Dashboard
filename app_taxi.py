import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc

# ----------------------------------------------------------------------------------------------
# 1. Load Taxi Monthly Report
# ----------------------------------------------------------------------------------------------

taxi_df = pd.read_csv("data_reports_monthly.csv")

taxi_df["Trips Per Day"] = (
    taxi_df["Trips Per Day"].astype(str).str.replace(",", "", regex=False).replace("-", pd.NA).astype(float)
)

taxi_df["Date"] = pd.to_datetime(taxi_df["Month/Year"].str.strip(), format="%Y-%m")

taxi_df["Year"] = taxi_df["Date"].dt.year
taxi_df["MonthNum"] = taxi_df["Date"].dt.month

taxi_df = taxi_df.sort_values(["Year", "MonthNum"])
license_classes = sorted(taxi_df["License Class"].unique())

# ----------------------------------------------------------------------------------------------
# 2. Dash  – Taxi dashboard only
# ----------------------------------------------------------------------------------------------

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.layout = dbc.Container(
    [
        html.H2("NYC Taxi – Monthly Trends Dashboard", className="my-4"),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Label("Select License Class:"),
                        dcc.Dropdown(
                            id="taxi-license-select",
                            options=[{"label": lc, "value": lc} for lc in license_classes],
                            value=("Yellow" if "Yellow" in license_classes else (license_classes[0] if license_classes else None)),
                            clearable=False,
                        ),
                    ], md=4),
                dbc.Col(
                    [
                        html.Label("Metric:"),
                        dcc.RadioItems(
                            id="taxi-metric-select",
                            options=[
                                {"label": "Trips Per Day", "value": "trips"},
                                {"label": "% Change YoY", "value": "pct"},
                            ],
                            value="trips",
                            labelStyle={"display": "inline-block", "margin-right": "20px"},
                        ),
                    ], md=4),
                dbc.Col(
                    [
                        html.Label("Date Range:"),
                        dcc.DatePickerRange(
                            id="taxi-date-picker",
                            start_date=max(taxi_df["Date"].min(), pd.Timestamp("2020-01-01")),
                            end_date=min(taxi_df["Date"].max(), pd.Timestamp("2025-06-30")),
                            max_date_allowed=pd.Timestamp("2025-06-30"),
                            display_format="YYYY-MM-DD",
                        ),
                    ], md=4),
            ], className="mb-4"),

        dcc.Graph(id="taxi-graph"),
    ], fluid=True)

# ----------------------------------------------------------------------------------------------
# Callback
# ----------------------------------------------------------------------------------------------

@app.callback(
    Output("taxi-graph", "figure"),
    [
        Input("taxi-license-select", "value"),
        Input("taxi-metric-select", "value"),
        Input("taxi-date-picker", "start_date"),
        Input("taxi-date-picker", "end_date"),
    ],
)
def update_taxi_graph(selected_license, metric, start_date, end_date):
    if selected_license is None:
        return {}

    data = taxi_df[taxi_df["License Class"] == selected_license].copy()
    if start_date and end_date:
        data = data[(data["Date"] >= pd.to_datetime(start_date)) & (data["Date"] <= pd.to_datetime(end_date))]

    if metric == "trips":
        fig = px.line(data, x="Date", y="Trips Per Day", title=f"Trips Per Day – {selected_license}")
    else:
        data["pct_change"] = data["Trips Per Day"].pct_change(periods=12) * 100
        fig = px.bar(data, x="Date", y="pct_change", title=f"Year-over-Year % Change – {selected_license}")
        fig.update_yaxes(title="% Change")

    fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
    return fig

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8051))
    app.run(host="0.0.0.0", port=port, debug=False)
