import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


# Consistent colour palette shared across all charts
COLOR_PALETTE = px.colors.qualitative.Pastel


def _no_data_figure(message: str = "No data") -> go.Figure:
    """Return a figure with a centred 'No data' annotation."""
    fig = go.Figure()
    fig.add_annotation(
        text=message,
        x=0.5,
        y=0.5,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=20, color="gray"),
    )
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        template="plotly_white",
    )
    return fig
``

def delivery_status_pie(df: pd.DataFrame) -> go.Figure:
    """Pie/donut chart of parcel count by Delivery Status."""
    if df.empty:
        return _no_data_figure()

    status_counts = df["Delivery Status"].value_counts().reset_index()
    status_counts.columns = ["Delivery Status", "Count"]

    fig = px.pie(
        status_counts,
        names="Delivery Status",
        values="Count",
        title="Delivery Status Distribution",
        color_discrete_sequence=COLOR_PALETTE,
        hole=0.4,
    )
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(template="plotly_white")
    return fig


def store_distribution_bar(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart of parcel count by Store, sorted descending."""
    if df.empty:
        return _no_data_figure()

    store_counts = df["Store"].value_counts().reset_index()
    store_counts.columns = ["Store", "Count"]
    store_counts = store_counts.sort_values("Count", ascending=True)  # ascending for horizontal bar (bottom = highest)

    fig = px.bar(
        store_counts,
        y="Store",
        x="Count",
        title="Parcels by Store",
        orientation="h",
        color="Store",
        color_discrete_sequence=COLOR_PALETTE,
        text="Count",
    )
    fig.update_traces(textposition="outside")
    fig.update_layout(
        template="plotly_white",
        yaxis=dict(title=""),
        xaxis=dict(title="Number of Parcels"),
        showlegend=False,
    )
    return fig


def cod_amount_histogram(df: pd.DataFrame) -> go.Figure:
    """Histogram of COD Amount distribution (excludes null/non-numeric rows)."""
    if df.empty:
        return _no_data_figure()

    cod_values = df["COD Amount"].dropna()
    if cod_values.empty:
        return _no_data_figure("No COD Amount data")

    fig = px.histogram(
        cod_values,
        x="COD Amount",
        nbins=20,
        title="COD Amount Distribution",
        color_discrete_sequence=[COLOR_PALETTE[0]],
        labels={"COD Amount": "COD Amount (\u09F3)"},
    )
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(title="COD Amount (\u09F3)"),
        yaxis=dict(title="Number of Parcels"),
        showlegend=False,
    )
    return fig


def daily_trend_line(df: pd.DataFrame) -> go.Figure:
    """Line chart of parcel count grouped by calendar day of Status Updated On."""
    if df.empty:
        return _no_data_figure()

    # Exclude NaT dates
    daily_df = df[df["Status Updated On"].notna()].copy()
    if daily_df.empty:
        return _no_data_figure("No date data available")

    daily_df["Date"] = daily_df["Status Updated On"].dt.date
    daily_counts = daily_df.groupby("Date").size().reset_index(name="Count")
    daily_counts = daily_counts.sort_values("Date")

    fig = px.line(
        daily_counts,
        x="Date",
        y="Count",
        title="Daily Delivery Trend",
        markers=True,
        color_discrete_sequence=[COLOR_PALETTE[1]],
        labels={"Date": "Date", "Count": "Parcels"},
    )
    fig.update_traces(line=dict(width=2.5))
    fig.update_layout(
        template="plotly_white",
        xaxis=dict(title="Date"),
        yaxis=dict(title="Number of Parcels"),
        showlegend=False,
    )
    return fig
