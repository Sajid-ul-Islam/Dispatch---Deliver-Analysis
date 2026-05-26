import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _no_data_fig() -> go.Figure:
    """Helper to return an empty placeholder figure."""
    fig = go.Figure()
    fig.add_annotation(
        text="No data",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=20)
    )
    fig.update_layout(xaxis_visible=False, yaxis_visible=False)
    return fig


def delivery_status_pie(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Delivery Status" not in df.columns:
        return _no_data_fig()
    
    fig = px.pie(
        df, 
        names="Delivery Status", 
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Delivery Status Distribution",
        hole=0.4
    )
    return fig


def store_distribution_bar(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Store" not in df.columns:
        return _no_data_fig()
        
    store_counts = df["Store"].value_counts().reset_index()
    store_counts.columns = ["Store", "Count"]
    
    fig = px.bar(
        store_counts, 
        x="Count", 
        y="Store", 
        orientation="h",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Store Distribution"
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    return fig


def cod_amount_histogram(df: pd.DataFrame) -> go.Figure:
    if df.empty or "COD Amount" not in df.columns:
        return _no_data_fig()
        
    valid_cod = df[pd.to_numeric(df["COD Amount"], errors='coerce').notna()]
    if valid_cod.empty:
        return _no_data_fig()
        
    fig = px.histogram(
        valid_cod, 
        x="COD Amount",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="COD Amount Distribution"
    )
    return fig


def daily_trend_line(df: pd.DataFrame) -> go.Figure:
    if df.empty or "Status Updated On" not in df.columns:
        return _no_data_fig()
        
    valid_dates = df[df["Status Updated On"].notna()].copy()
    if valid_dates.empty:
        return _no_data_fig()
        
    valid_dates["Date"] = valid_dates["Status Updated On"].dt.date
    daily_counts = valid_dates.groupby("Date").size().reset_index(name="Count")
    
    fig = px.line(
        daily_counts, 
        x="Date", 
        y="Count",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        title="Daily Delivery Trend"
    )
    return fig