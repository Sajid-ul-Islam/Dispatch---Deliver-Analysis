import pandas as pd
import streamlit as st


def render_data_table(df: pd.DataFrame) -> None:
    """Render interactive data table with column config and formatting."""
    if df.empty:
        st.info("No records found.")
        return

    # Show row count
    st.caption(f"Showing {len(df)} record(s)")

    # Default visible columns
    default_cols = ["Consignment ID", "Store", "Recipient Name", "Delivery Status", "Status Updated On", "COD Amount"]
    available_cols = [c for c in default_cols if c in df.columns]

    # Toggle to show all columns
    show_all = st.toggle("Show all columns", value=False, key="show_all_cols")

    if show_all:
        display_cols = list(df.columns)
    else:
        display_cols = available_cols

    display_df = df[display_cols].copy()

    # Build column config
    column_config = {}
    for col in ["COD Amount", "Charge", "Discount"]:
        if col in display_df.columns:
            column_config[col] = st.column_config.NumberColumn(
                col,
                format="\u09F3%.2f",
            )

    if "Status Updated On" in display_df.columns:
        column_config["Status Updated On"] = st.column_config.DateColumn(
            "Status Updated On",
            format="DD/MM/YYYY",
        )

    # Highlight Pending rows with a visually distinct background
    def _highlight_pending(row):
        if row.get("Delivery Status") == "Pending":
            return ["background-color: #fff3cd"] * len(row)  # soft yellow highlight
        return [""] * len(row)

    styled_df = display_df.style.apply(_highlight_pending, axis=1)

    st.dataframe(
        styled_df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=400,
    )
