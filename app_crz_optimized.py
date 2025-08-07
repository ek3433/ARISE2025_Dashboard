import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
import os

def load_crz_data():
    """Load CRZ data from pre-aggregated CSV files"""
    print("Loading CRZ data from pre-aggregated files...")
    
    try:
        # Check if aggregated files exist
        required_files = [
            'crz_hourly_summary.csv',
            'crz_daily_summary.csv', 
            'crz_weekly_summary.csv',
            'crz_monthly_summary.csv',
            'crz_excluded_summary.csv'
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        if missing_files:
            print(f"ERROR: Missing required files: {missing_files}")
            print("Please run 'python create_crz_summary.py' first to create the data files.")
            return None
        
        # Load all aggregated data
        hourly_data = pd.read_csv('crz_hourly_summary.csv')
        daily_data = pd.read_csv('crz_daily_summary.csv')
        weekly_data = pd.read_csv('crz_weekly_summary.csv')
        monthly_data = pd.read_csv('crz_monthly_summary.csv')
        excluded_data = pd.read_csv('crz_excluded_summary.csv')
        
        # Convert date columns
        for df in [hourly_data, daily_data, excluded_data]:
            df['Toll Date'] = pd.to_datetime(df['Toll Date'])
        
        print(f"Loaded aggregated data:")
        print(f"  - Hourly: {len(hourly_data):,} rows")
        print(f"  - Daily: {len(daily_data):,} rows")
        print(f"  - Weekly: {len(weekly_data):,} rows")
        print(f"  - Monthly: {len(monthly_data):,} rows")
        print(f"  - Excluded: {len(excluded_data):,} rows")
        
        return {
            'hourly': hourly_data,
            'daily': daily_data,
            'weekly': weekly_data,
            'monthly': monthly_data,
            'excluded': excluded_data
        }
        
    except Exception as e:
        print(f"Error loading CRZ data: {e}")
        return None

# Load the data
data_dict = load_crz_data()

if data_dict is None:
    # Show error message in the app
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    server = app.server
    
    app.layout = dbc.Container([
        html.H2("MTA CRZ Vehicle Entries Dashboard", className="my-4"),
        dbc.Alert([
            html.H4("Data Loading Error", className="alert-heading"),
            html.P("The CRZ data could not be loaded. Please ensure:"),
            html.Ul([
                html.Li("All CRZ summary files exist in the project directory"),
                html.Li("Run 'python create_crz_summary.py' to create the data files"),
                html.Li("The data files are not corrupted")
            ]),
            html.Hr(),
            html.P("If you continue to have issues, please check the console logs for more details.")
        ], color="danger", className="my-4")
    ], fluid=True)
    
    if __name__ == "__main__":
        import os
        port = int(os.environ.get("PORT", 8050))
        app.run(host="0.0.0.0", port=port, debug=False)
else:
    # Extract data
    hourly_data = data_dict['hourly']
    daily_data = data_dict['daily']
    weekly_data = data_dict['weekly']
    monthly_data = data_dict['monthly']
    excluded_data = data_dict['excluded']
    
    # Get unique values for filters
    regions = sorted(hourly_data['Detection Region'].unique())
    vehicle_classes = sorted(hourly_data['Vehicle Class'].unique())
    detect_groups = sorted(hourly_data['Detection Group'].unique())
    
    # Date range
    min_date = hourly_data['Toll Date'].min()
    max_date = hourly_data['Toll Date'].max()
    
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
    server = app.server
    
    app.layout = dbc.Container([
        html.H2("MTA CRZ Vehicle Entries Dashboard", className="my-4"),
        html.P("Comprehensive Analysis of Congestion Relief Zone Vehicle Entries", className="text-muted"),
        
        # Filters
        dbc.Row([
            dbc.Col([
                html.Label("Vehicle Class:"),
                dcc.Dropdown(
                    id="vehicle-select",
                    options=[{"label": v, "value": v} for v in vehicle_classes],
                    value=vehicle_classes,
                    multi=True,
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                html.Label("Detection Region:"),
                dcc.Dropdown(
                    id="region-select",
                    options=[{"label": r, "value": r} for r in regions],
                    value=regions,
                    multi=True,
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                html.Label("Detection Group:"),
                dcc.Dropdown(
                    id="group-select",
                    options=[{"label": g, "value": g} for g in detect_groups],
                    value=detect_groups,
                    multi=True,
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                html.Label("Date Range:"),
                dcc.DatePickerRange(
                    id="date-picker",
                    start_date=min_date,
                    end_date=max_date,
                    min_date_allowed=min_date,
                    max_date_allowed=max_date,
                    display_format="YYYY-MM-DD",
                ),
            ], md=3),
        ], className="mb-4"),
        
        dbc.Row([
            dbc.Col([
                html.Label("Aggregation Level:"),
                dcc.Dropdown(
                    id="agg-level",
                    options=[
                        {"label": "Hourly", "value": "hourly"},
                        {"label": "Daily", "value": "daily"},
                        {"label": "Weekly", "value": "weekly"},
                        {"label": "Monthly", "value": "monthly"},
                    ],
                    value="daily",
                    clearable=False,
                ),
            ], md=3),
            dbc.Col([
                html.Label("Metric:"),
                dcc.RadioItems(
                    id="metric-select",
                    options=[
                        {"label": "Total", "value": "sum"},
                        {"label": "Average", "value": "mean"},
                    ],
                    value="sum",
                    labelStyle={"display": "inline-block", "margin-right": "20px"},
                ),
            ], md=3),
        ], className="mb-4"),
        
        # Summary stats
        dbc.Row([
            dbc.Col(html.Div(id="total-entries"), md=3),
            dbc.Col(html.Div(id="date-range"), md=3),
            dbc.Col(html.Div(id="avg-daily"), md=3),
            dbc.Col(html.Div(id="peak-hour"), md=3),
        ], className="mb-4"),
        
        # Tabs
        dcc.Tabs([
            dcc.Tab(label="Time Series", children=[
                dcc.Graph(id="time-series-plot")
            ]),
            dcc.Tab(label="Regional Analysis", children=[
                dcc.Graph(id="regional-plot")
            ]),
            dcc.Tab(label="Vehicle Analysis", children=[
                dcc.Graph(id="vehicle-plot")
            ]),
            dcc.Tab(label="Hourly Heatmap", children=[
                dcc.Graph(id="heatmap-plot")
            ]),
            dcc.Tab(label="Excluded Entries", children=[
                dcc.Graph(id="excluded-plot")
            ]),
        ]),
        
    ], fluid=True)
    
    @app.callback(
        [Output("time-series-plot", "figure"),
         Output("regional-plot", "figure"),
         Output("vehicle-plot", "figure"),
         Output("heatmap-plot", "figure"),
         Output("excluded-plot", "figure"),
         Output("total-entries", "children"),
         Output("date-range", "children"),
         Output("avg-daily", "children"),
         Output("peak-hour", "children")],
        [Input("vehicle-select", "value"),
         Input("region-select", "value"),
         Input("group-select", "value"),
         Input("date-picker", "start_date"),
         Input("date-picker", "end_date"),
         Input("agg-level", "value"),
         Input("metric-select", "value")]
    )
    def update_plots(vehicles, regions, groups, start_date, end_date, agg_level, metric):
        # Filter data based on selection
        if agg_level == "hourly":
            df = hourly_data.copy()
        elif agg_level == "daily":
            df = daily_data.copy()
        elif agg_level == "weekly":
            df = weekly_data.copy()
        else:  # monthly
            df = monthly_data.copy()
        
        # Apply filters
        df = df[
            (df['Vehicle Class'].isin(vehicles)) &
            (df['Detection Region'].isin(regions)) &
            (df['Detection Group'].isin(groups))
        ]
        
        if start_date and end_date:
            if 'Toll Date' in df.columns:
                df = df[
                    (df['Toll Date'] >= pd.to_datetime(start_date)) &
                    (df['Toll Date'] <= pd.to_datetime(end_date))
                ]
        
        # Calculate summary stats
        total_entries = df['CRZ Entries'].sum()
        avg_daily = df['CRZ Entries'].mean() if len(df) > 0 else 0
        
        # Time series plot
        if agg_level == "hourly":
            time_series = df.groupby(['Toll Date', 'Hour'])['CRZ Entries'].sum().reset_index()
            time_series['DateTime'] = pd.to_datetime(time_series['Toll Date']) + pd.to_timedelta(time_series['Hour'], unit='h')
            fig1 = px.line(time_series, x='DateTime', y='CRZ Entries', title='Hourly CRZ Entries Over Time')
        else:
            time_series = df.groupby('Toll Date')['CRZ Entries'].sum().reset_index()
            fig1 = px.line(time_series, x='Toll Date', y='CRZ Entries', title=f'{agg_level.title()} CRZ Entries Over Time')
        
        # Regional analysis
        regional = df.groupby('Detection Region')['CRZ Entries'].sum().reset_index()
        fig2 = px.bar(regional, x='Detection Region', y='CRZ Entries', title='CRZ Entries by Region')
        
        # Vehicle analysis
        vehicle = df.groupby('Vehicle Class')['CRZ Entries'].sum().reset_index()
        fig3 = px.pie(vehicle, values='CRZ Entries', names='Vehicle Class', title='CRZ Entries by Vehicle Class')
        
        # Hourly heatmap
        if 'Hour' in df.columns:
            heatmap = df.groupby(['Hour', 'Detection Region'])['CRZ Entries'].sum().reset_index()
            heatmap_pivot = heatmap.pivot(index='Hour', columns='Detection Region', values='CRZ Entries').fillna(0)
            fig4 = go.Figure(data=go.Heatmap(z=heatmap_pivot.values, x=heatmap_pivot.columns, y=heatmap_pivot.index, colorscale='Viridis'))
            fig4.update_layout(title='Hourly CRZ Entries by Region', xaxis_title='Region', yaxis_title='Hour')
        else:
            fig4 = go.Figure()
            fig4.add_annotation(text="Hourly data not available for this aggregation level", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        
        # Excluded entries
        excluded_filtered = excluded_data.copy()
        if start_date and end_date:
            excluded_filtered = excluded_filtered[
                (excluded_filtered['Toll Date'] >= pd.to_datetime(start_date)) &
                (excluded_filtered['Toll Date'] <= pd.to_datetime(end_date))
            ]
        fig5 = px.line(excluded_filtered, x='Toll Date', y='Excluded Roadway Entries', title='Excluded Roadway Entries Over Time')
        
        # Summary stats
        date_range_text = f"Date Range: {start_date} to {end_date}" if start_date and end_date else "All Dates"
        avg_daily_text = f"Avg Daily: {avg_daily:,.0f}"
        peak_hour_text = f"Peak Hour: {df.loc[df['CRZ Entries'].idxmax(), 'Hour'] if 'Hour' in df.columns and len(df) > 0 else 'N/A'}"
        
        return fig1, fig2, fig3, fig4, fig5, f"Total: {total_entries:,.0f}", date_range_text, avg_daily_text, peak_hour_text
    
    if __name__ == "__main__":
        import os
        port = int(os.environ.get("PORT", 8050))
        app.run(host="0.0.0.0", port=port, debug=False) 