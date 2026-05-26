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

def compute_issues_kpi(df_issues: pd.DataFrame) -> dict:
    if df_issues.empty:
        return {"Total Issues": 0, "Pending/Open": 0}
        
    total_issues = len(df_issues)
    
    # Try to find a status column fuzzy match
    status_col = next((col for col in df_issues.columns if 'status' in col.lower() or 'state' in col.lower()), None)
    
    pending_count = 0
    if status_col:
        # assume anything like 'open', 'pending', 'unresolved', 'in progress'
        open_keywords = ['open', 'pending', 'unresolved', 'in progress', 'new']
        # Convert to lowercase and strip whitespace for matching
        status_series = df_issues[status_col].astype(str).str.lower().str.strip()
        pending_mask = status_series.isin(open_keywords)
        pending_count = int(pending_mask.sum())
        
    return {"Total Issues": total_issues, "Pending/Open": pending_count}

def render_issues_kpi(issues_kpi: dict) -> None:
    st.markdown("### 📝 Issue Log Insights")
    cols = st.columns(4)
    with cols[0]:
        st.metric("Total Logged Issues", f"{issues_kpi.get('Total Issues', 0):,}")
    
    pending = issues_kpi.get('Pending/Open', 0)
    with cols[1]:
        if pending > 0:
            # Show in red if there are pending issues
            st.markdown(
                f"<div><p style='font-size: 0.875rem; color: rgba(49, 51, 63, 0.6); margin-bottom: 0px;'>Pending/Open Issues</p>"
                f"<h2 style='color: red; padding-top: 0px; margin-top: 0px;'>{pending:,}</h2></div>", 
                unsafe_allow_html=True
            )
        else:
            st.metric("Pending/Open Issues", "0")
            
    # Add a small insight
    if issues_kpi.get('Total Issues', 0) > 0:
        if pending > 0:
            st.info(f"💡 **Insight:** There are {issues_kpi.get('Total Issues', 0)} total issues logged in the central sheet. **{pending}** of these are currently pending/open and require attention.")
        else:
            st.success(f"💡 **Insight:** All {issues_kpi.get('Total Issues', 0)} logged issues have been resolved. Great job!")