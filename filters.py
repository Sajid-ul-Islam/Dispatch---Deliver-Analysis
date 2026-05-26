from datetime import date
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd
import streamlit as st


@dataclass
class FilterState:
    stores: list[str] = field(default_factory=list)
    statuses: list[str] = field(default_factory=list)
    payment_statuses: list[str] = field(default_factory=list)
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    search_text: str = ""


def render_sidebar_filters(df: pd.DataFrame) -> FilterState:
    """Render all sidebar filter widgets and return current FilterState."""
    st.sidebar.header("Filters")

    # Store filter - dynamic options from data
    stores = sorted(df["Store"].dropna().unique().tolist())
    selected_stores = st.sidebar.multiselect(
        "Store",
        options=stores,
        default=stores,
        key="store_filter",
    )

    # Delivery status filter
    statuses = sorted(df["Delivery Status"].dropna().unique().tolist())
    selected_statuses = st.sidebar.multiselect(
        "Delivery Status",
        options=statuses,
        default=statuses,
        key="status_filter",
    )

    # Payment status filter
    payment_statuses = sorted(df["Payment Status"].dropna().unique().tolist())
    selected_payment_statuses = st.sidebar.multiselect(
        "Payment Status",
        options=payment_statuses,
        default=payment_statuses,
        key="payment_status_filter",
    )

    # Date range filter
    st.sidebar.subheader("Date Range")
    if "Status Updated On" in df.columns and df["Status Updated On"].notna().any():
        min_date = df["Status Updated On"].min().date()
        max_date = df["Status Updated On"].max().date()
    else:
        min_date = date.today()
        max_date = date.today()

    date_from = st.sidebar.date_input("From", value=min_date, min_value=min_date, max_value=max_date, key="date_from")
    date_to = st.sidebar.date_input("To", value=max_date, min_value=min_date, max_value=max_date, key="date_to")

    # Free-text search
    search_text = st.sidebar.text_input("Search (Consignment ID / Recipient)", value="", key="search_text")

    return FilterState(
        stores=selected_stores,
        statuses=selected_statuses,
        payment_statuses=selected_payment_statuses,
        date_from=date_from,
        date_to=date_to,
        search_text=search_text.strip(),
    )


def apply_filters(df: pd.DataFrame, state: FilterState) -> pd.DataFrame:
    """Apply FilterState to df and return filtered copy."""
    mask = pd.Series([True] * len(df), index=df.index)

    # Store filter
    if state.stores:
        mask &= df["Store"].isin(state.stores)

    # Delivery status filter
    if state.statuses:
        mask &= df["Delivery Status"].isin(state.statuses)

    # Payment status filter
    if state.payment_statuses:
        mask &= df["Payment Status"].isin(state.payment_statuses)

    # Date range filter - inclusive bounds; exclude NaT rows when date filter is active
    date_filter_active = False
    if state.date_from is not None:
        date_filter_active = True
        mask &= df["Status Updated On"].dt.date >= state.date_from
    if state.date_to is not None:
        date_filter_active = True
        mask &= df["Status Updated On"].dt.date <= state.date_to

    # Exclude NaT rows when date filter is active
    if date_filter_active:
        mask &= df["Status Updated On"].notna()

    # Free-text search - case-insensitive substring match
    if state.search_text:
        text = state.search_text.lower()
        text_mask = (
            df["Consignment ID"].astype(str).str.lower().str.contains(text, na=False)
            | df["Recipient Name"].astype(str).str.lower().str.contains(text, na=False)
        )
        mask &= text_mask

    return df[mask].reset_index(drop=True)
