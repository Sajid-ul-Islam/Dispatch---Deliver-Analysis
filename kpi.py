from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass
class KPIMetrics:
    total_parcels: int = 0
    total_cod: float = 0.0
    total_charges: float = 0.0
    total_discounts: float = 0.0
    net_revenue: float = 0.0
    pending_count: int = 0
    pickup_requested_count: int = 0


def compute_kpis(df: pd.DataFrame) -> KPIMetrics:
    """Compute all KPI values from filtered DataFrame."""
    if df.empty:
        return KPIMetrics()

    total_parcels = len(df)
    total_cod = float(df["COD Amount"].sum())
    total_charges = float(df["Charge"].sum())
    total_discounts = float(df["Discount"].sum())
    net_revenue = total_charges - total_discounts
    pending_count = int((df["Delivery Status"] == "Pending").sum())
    pickup_requested_count = int((df["Delivery Status"] == "Pickup Requested").sum())

    return KPIMetrics(
        total_parcels=total_parcels,
        total_cod=total_cod,
        total_charges=total_charges,
        total_discounts=total_discounts,
        net_revenue=net_revenue,
        pending_count=pending_count,
        pickup_requested_count=pickup_requested_count,
    )


def format_currency(value: float) -> str:
    """Format a number as BDT currency with comma separators."""
    return f"\u09F3{value:,.2f}"


def format_integer(value: int) -> str:
    """Format an integer with comma separators."""
    if value >= 1000:
        return f"{value:,}"
    return str(value)


def render_kpi_cards(metrics: KPIMetrics) -> None:
    """Render KPI metric cards using st.metric in a 4-column layout."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Parcels", format_integer(metrics.total_parcels))
        st.metric("Total COD", format_currency(metrics.total_cod))

    with col2:
        st.metric("Total Charges", format_currency(metrics.total_charges))
        st.metric("Total Discounts", format_currency(metrics.total_discounts))

    with col3:
        st.metric("Net Revenue", f"৳{metrics.net_revenue:,.2f}" if metrics.net_revenue >= 0 else f":red[-৳{abs(metrics.net_revenue):,.2f}]")
        st.metric("Pending Count", format_integer(metrics.pending_count))

    with col4:
        st.metric("Pickup Requested", format_integer(metrics.pickup_requested_count))
