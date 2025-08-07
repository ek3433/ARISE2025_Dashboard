import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import requests
import io
import numpy as np

# Dropbox direct download URL for CRZ data
CRZ_CSV_URL = "https://www.dropbox.com/scl/fi/no91aso4hhf2yi1wl9de5/MTA_Congestion_Relief_Zone_Vehicle_Entries__Beginning_2025_20250708.csv?rlkey=hbfljmt2n2ac64h52y3tapo4z&st=x0z517yn&dl=1"

@st.cache_data
def load_crz_data():
    """Load CRZ data from Dropbox - using ACTUAL data, no random assignment"""
    try:
        # Download from Dropbox
        response = requests.get(CRZ_CSV_URL, stream=True)
        if response.status_code != 200:
            raise Exception(f"Failed to download from Dropbox: {response.status_code}")
        # Load the CSV data
        df = pd.read_csv(io.BytesIO(response.content), on_bad_lines='skip', engine='c', sep=',')
        # Parse timestamps
        df["Toll 10 Minute Block"] = pd.to_datetime(df["Toll 10 Minute Block"], format="%m/%d/%Y %I:%M:%S %p", errors='coerce')
        df["Toll Date"] = pd.to_datetime(df["Toll Date"], format="%m/%d/%Y", errors='coerce')
        # Remove invalid timestamps
        df = df.dropna(subset=['Toll 10 Minute Block', 'Toll Date'])
        # Add derived columns
        df["Hour"] = df["Toll 10 Minute Block"].dt.hour
        df["Minute"] = df["Toll 10 Minute Block"].dt.minute
        df["Month"] = df["Toll 10 Minute Block"].dt.month_name()
        df["MonthNum"] = df["Toll 10 Minute Block"].dt.month
        df["Week"] = df["Toll 10 Minute Block"].dt.isocalendar().week
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
        return df
    except Exception as e:
        st.error(f"Error loading CRZ data: {e}")
        return None

df = load_crz_data()
if df is None or df.empty:
    st.error("Failed to load CRZ data. Please check your data source or try again later.")
    st.stop()

st.title("MTA CRZ Vehicle Entries Dashboard")
st.markdown("Comprehensive Analysis of Congestion Relief Zone Vehicle Entries")

# Sidebar filters
st.sidebar.header("Filters")

# Vehicle Class filter
vehicle_classes = sorted(df["Vehicle Class"].unique())
selected_vehicles = st.sidebar.multiselect(
    "Select Vehicle Class(es):",
    vehicle_classes,
    default=vehicle_classes
)

# Region filter
regions = sorted(df["Detection Region"].unique())
selected_regions = st.sidebar.multiselect(
    "Select Region(s):",
    regions,
    default=regions
)

# Detection Group filter
detect_groups = sorted(df["Detection Group"].unique())
selected_groups = st.sidebar.multiselect(
    "Select Detection Group(s):",
    detect_groups,
    default=detect_groups
)

# Date range filter
# Get valid date range (excluding NaT values)
valid_dates = df["Toll Date"].dropna()
if len(valid_dates) > 0:
    min_date = valid_dates.min()
    max_date = valid_dates.max()
else:
    min_date = pd.Timestamp("2025-01-01")
    max_date = pd.Timestamp("2025-12-31")

date_range = st.sidebar.date_input(
    "Select Date Range:",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Value type filter (default to Total)
value_type = st.sidebar.radio(
    "Choose Value Type:",
    ["mean", "sum"],
    index=1,  # 1 = "sum" (Total)
    format_func=lambda x: "Average" if x == "mean" else "Total"
)

# Aggregation level filter (default to Monthly)
agg_level = st.sidebar.selectbox(
    "Choose Aggregation Level:",
    ["Toll 10 Minute Block", "Hour", "Toll Date", "Week", "Month"],
    index=4,  # 4 = "Month"
    format_func=lambda x: {
        "Toll 10 Minute Block": "10-Minute",
        "Hour": "Hourly", 
        "Toll Date": "Daily",
        "Week": "Weekly",
        "Month": "Monthly"
    }[x]
)

# Filter data
filtered = df[
    (df["Vehicle Class"].isin(selected_vehicles)) &
    (df["Detection Region"].isin(selected_regions)) &
    (df["Detection Group"].isin(selected_groups))
]
# Apply date filtering only if we have valid dates
if len(date_range) == 2 and date_range[0] and date_range[1]:
    filtered = filtered[
        (filtered["Toll Date"] >= pd.to_datetime(date_range[0])) &
        (filtered["Toll Date"] <= pd.to_datetime(date_range[1]))
    ]

# Display summary stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Rows", f"{len(filtered):,}")
with col2:
    st.metric("Total CRZ Entries", f"{filtered['CRZ Entries'].sum():,.0f}")
with col3:
    # Fix NaT error by handling null dates properly
    min_date = filtered['Toll Date'].min()
    max_date = filtered['Toll Date'].max()
    if pd.isna(min_date) or pd.isna(max_date):
        date_range_text = "Date Range: No valid dates"
    else:
        date_range_text = f"Date Range: {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
    st.metric("Date Range", date_range_text)
with col4:
    st.metric("Vehicle Classes", len(filtered['Vehicle Class'].unique()))

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Time Series", "Peak vs Non-Peak", "Heatmap by Region", "Heatmap by Group",
    "Vehicle Trends", "Monthly Trends", "Standard Deviation", "Excluded Entries"
])

with tab1:
    st.subheader("Time Series")
    try:
        ts = getattr(filtered.groupby(agg_level, observed=False)["CRZ Entries"], value_type)().reset_index()
        ts = ts[ts["CRZ Entries"] > 0]
        if len(ts) > 0:
            fig = px.line(ts, x=agg_level, y="CRZ Entries", title=f"{value_type.title()} CRZ Entries by {agg_level}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating time series plot: {e}")

with tab2:
    st.subheader("Peak vs Non-Peak")
    try:
        peak = getattr(filtered.groupby(["Time Period", "Detection Region"], observed=False)["CRZ Entries"], value_type)().reset_index()
        if len(peak) > 0:
            fig = px.bar(peak, x="Detection Region", y="CRZ Entries", color="Time Period",
                         barmode="group", title=f"{value_type.title()} CRZ Entries: Peak vs Non-Peak by Region")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating peak vs non-peak plot: {e}")

with tab3:
    st.subheader("Heatmap by Region")
    try:
        heat = getattr(filtered.groupby(["Hour", "Detection Region"], observed=False)["CRZ Entries"], value_type)().reset_index()
        if len(heat) > 0:
            heat_pivot = heat.pivot(index="Hour", columns="Detection Region", values="CRZ Entries").fillna(0)
            fig = go.Figure(data=go.Heatmap(z=heat_pivot.values, x=heat_pivot.columns, y=heat_pivot.index, colorscale='Viridis'))
            fig.update_layout(title=f"{value_type.title()} Hourly CRZ Entries by Region", xaxis_title="Region", yaxis_title="Hour")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating heatmap by region: {e}")

with tab4:
    st.subheader("Heatmap by Group")
    try:
        heat = getattr(filtered.groupby(["Hour", "Detection Group"], observed=False)["CRZ Entries"], value_type)().reset_index()
        if len(heat) > 0:
            heat_pivot = heat.pivot(index="Hour", columns="Detection Group", values="CRZ Entries").fillna(0)
            fig = go.Figure(data=go.Heatmap(z=heat_pivot.values, x=heat_pivot.columns, y=heat_pivot.index, colorscale='Cividis'))
            fig.update_layout(title=f"{value_type.title()} Hourly CRZ Entries by Group", xaxis_title="Detection Group", yaxis_title="Hour")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating heatmap by group: {e}")

with tab5:
    st.subheader("Vehicle Trends")
    try:
        bar = getattr(filtered.groupby("Vehicle Class", observed=False)["CRZ Entries"], value_type)().reset_index()
        if len(bar) > 0:
            fig = px.bar(bar, x="Vehicle Class", y="CRZ Entries", title=f"{value_type.title()} CRZ Entries by Vehicle Class")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating vehicle trends plot: {e}")

with tab6:
    st.subheader("Monthly Trends")
    try:
        tmp = filtered.copy()
        tmp["YearMonth"] = tmp["Toll Date"].dt.to_period("M").dt.to_timestamp()
        month = getattr(tmp.groupby(["YearMonth", "Detection Region"], observed=False)["CRZ Entries"], value_type)().reset_index()
        month = month.sort_values("YearMonth")
        if len(month) > 0:
            fig = px.bar(month, x="YearMonth", y="CRZ Entries", color="Detection Region",
                        title=f"{value_type.title()} CRZ Entries by Month and Region")
            fig.update_xaxes(dtick="M1", tickformat="%Y-%m")
            fig.update_layout(legend=dict(x=1.02, y=1, xanchor="left", yanchor="top"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating monthly trends plot: {e}")

with tab7:
    st.subheader("Standard Deviation")
    try:
        std = filtered.groupby(agg_level, observed=False)["CRZ Entries"].std().reset_index()
        if len(std) > 0:
            fig = px.line(std, x=agg_level, y="CRZ Entries", title=f"Standard Deviation of CRZ Entries by {agg_level}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating standard deviation plot: {e}")

with tab8:
    st.subheader("Excluded Roadway Entries")
    try:
        excl = getattr(filtered.groupby("Toll Date", observed=False)["Excluded Roadway Entries"], value_type)().reset_index()
        if len(excl) > 0:
            fig = px.line(excl, x="Toll Date", y="Excluded Roadway Entries", title=f"{value_type.title()} Excluded Roadway Entries Over Time")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available for the selected filters.")
    except Exception as e:
        st.error(f"Error creating excluded entries plot: {e}") 