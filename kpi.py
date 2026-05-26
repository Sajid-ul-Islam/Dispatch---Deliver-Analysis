import pandas as pd
import streamlit as st
from dataclasses import dataclass


@dataclass
class KPIMetrics:
    total_parcels: int
    total_cod: float
    total_charges: float
    total_discounts: float
    net_revenue: float
    pending_count: int
    pickup_requested_count: int


def compute_kpis(df: pd.DataFrame) -> KPIMetrics:
    if df.empty:
        return KPIMetrics(
            total_parcels=0,
            total_cod=0.0,
            total_charges=0.0,
            total_discounts=0.0,
            net_revenue=0.0,
            pending_count=0,
            pickup_requested_count=0
        )
    
    total_charges = float(df["Charge"].sum())
    total_discounts = float(df["Discount"].sum())
    
    return KPIMetrics(
        total_parcels=len(df),
        total_cod=float(df["COD Amount"].sum()),
        total_charges=total_charges,
        total_discounts=total_discounts,
        net_revenue=total_charges - total_discounts,
        pending_count=len(df[df["Delivery Status"] == "Pending"]),
        pickup_requested_count=len(df[df["Delivery Status"] == "Pickup Requested"])
    )


def render_kpi_cards(metrics: KPIMetrics) -> None:
    # Grid Layout: Row 1 - Main Volume & Financials
    row1_cols = st.columns([1, 1.2, 1, 1, 1.2])
    row1_cols[0].metric("📦 Total Parcels", f"{metrics.total_parcels:,}")
    row1_cols[1].metric("💰 Total COD", f"৳{metrics.total_cod:,.0f}")
    row1_cols[2].metric("🏷️ Charges", f"৳{metrics.total_charges:,.0f}")
    row1_cols[3].metric("✂️ Discounts", f"৳{metrics.total_discounts:,.0f}")
    
    # Net Revenue Highlight
    with row1_cols[4]:
        if metrics.net_revenue < 0:
            st.metric("📉 Net Revenue", f"৳{metrics.net_revenue:,.2f}", delta="Loss", delta_color="inverse")
        else:
            st.metric("📈 Net Revenue", f"৳{metrics.net_revenue:,.2f}")

    # Row 2 - Status Specifics
    st.write("") # Spacer
    row2_cols = st.columns([1, 1, 1, 1, 1.2])
    with row2_cols[0]:
        st.metric("⏳ Pending", f"{metrics.pending_count:,}")
    with row2_cols[1]:
        st.metric("🚚 Pickup Req.", f"{metrics.pickup_requested_count:,}")