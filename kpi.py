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
    # 4-column layout as requested
    cols1 = st.columns(4)
    with cols1[0]:
        st.metric("Total Parcels", f"{metrics.total_parcels:,}")
    with cols1[1]:
        st.metric("Total COD", f"৳{metrics.total_cod:,.2f}")
    with cols1[2]:
        st.metric("Total Charges", f"৳{metrics.total_charges:,.2f}")
    with cols1[3]:
        st.metric("Total Discounts", f"৳{metrics.total_discounts:,.2f}")
        
    cols2 = st.columns(4)
    with cols2[0]:
        if metrics.net_revenue < 0:
            # Display negative net revenue in red without breaking the layout
            st.markdown(
                f"<div><p style='font-size: 0.875rem; color: rgba(49, 51, 63, 0.6); margin-bottom: 0px;'>Net Revenue</p>"
                f"<h2 style='color: red; padding-top: 0px; margin-top: 0px;'>৳{metrics.net_revenue:,.2f}</h2></div>", 
                unsafe_allow_html=True
            )
        else:
            st.metric("Net Revenue", f"৳{metrics.net_revenue:,.2f}")
            
    with cols2[1]:
        st.metric("Pending", f"{metrics.pending_count:,}")
    with cols2[2]:
        st.metric("Pickup Requested", f"{metrics.pickup_requested_count:,}")