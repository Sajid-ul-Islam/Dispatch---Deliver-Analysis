import streamlit as st
from datetime import datetime
from data_loader import load_data, DataLoadError, SchemaValidationError
from filters import render_sidebar_filters, apply_filters
from kpi import compute_kpis, render_kpi_cards
from charts import (
    delivery_status_pie, 
    store_distribution_bar, 
    cod_amount_histogram, 
    daily_trend_line
)
from table import render_data_table
from exporter import to_csv_bytes, to_excel_bytes
from delivery_parser import parse_records, parse_data_fuzzy
from data_loader import validate_schema, coerce_types
import issue_dashboard

# 1. Page Configuration
st.set_page_config(page_title="Dispatch & Delivery Report", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

# Custom UI Styling
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.6rem; font-weight: 700; }
    [data-testid="stExpander"] { border: 1px solid #f0f2f6; border-radius: 0.5rem; }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f8f9fa; border-radius: 5px 5px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #e9ecef !important; font-weight: bold; }
    /* Card-like containers for charts */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { padding: 1rem; }
    </style>
    """, unsafe_allow_html=True)

st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Select Module", ["📦 Dispatch Analysis", "📝 Issue Tracker"])

if app_mode == "📦 Dispatch Analysis":
    st.title("📦 Dispatch & Delivery Report")
    st.markdown("Monitor delivery performance, COD collections, and store distributions in real-time.")
    
    # 2. Data Source Configuration (Top Section)
    with st.container(border=True):
        col_src1, col_src2 = st.columns([1, 3])
        with col_src1:
            input_type = st.radio(
                "📥 Data Source", 
                ["Excel (.xlsx)", "Raw Text (.txt)", "Paste Text"]
            )
    
        df = None
        last_fetched = None
        data_ready = False
    
        if input_type == "Excel (.xlsx)":
            source = st.file_uploader("Upload Excel file", type=["xlsx"])
            if source:
                try:
                    with st.spinner("Loading Excel data..."):
                        df, last_fetched = load_data(source)
                        data_ready = True
                except SchemaValidationError as e:
                    st.error(f"File schema mismatch: {e}")
                except DataLoadError as e:
                    st.error(str(e))
            else:
                st.caption("Awaiting file upload...")

        else:
            if input_type == "Raw Text (.txt)":
                uploaded_txt = st.file_uploader("Upload Raw Text file", type=["txt"])
                if uploaded_txt:
                    raw_text = uploaded_txt.getvalue().decode("utf-8")
                else:
                    st.info("Please upload a text file to parse raw delivery records.")
                    raw_text = None
            else:
                raw_text = st.text_area("Paste Raw Text Here", height=150, placeholder="Paste your raw delivery records here...")
                if not raw_text.strip():
                    st.info("Please paste raw delivery records to begin.")
                    raw_text = None
                    
            if raw_text:
                try:
                    with st.spinner("Parsing text data..."):
                        parsed_df = parse_records(raw_text)
                        if parsed_df.empty:
                            parsed_df = parse_data_fuzzy(raw_text)
                        
                        if parsed_df.empty:
                            st.warning("No records could be parsed from the provided text.")
                        else:
                            validate_schema(parsed_df)
                            df = coerce_types(parsed_df)
                            last_fetched = datetime.now()
                            data_ready = True
                except SchemaValidationError as e:
                    st.error(f"Parsed schema mismatch: {e}")
                except Exception as e:
                    st.error(f"Could not parse text: {e}")
    
    # 3. Sidebar Filters
    filtered_df = None
    if data_ready and df is not None and last_fetched is not None:
        with st.sidebar.container(border=True):
            st.caption("📈 Data Summary")
            st.metric("Total Cached Records", f"{len(df):,}")
            
            # Freshness Indicator
            diff = datetime.now() - last_fetched
            minutes = int(diff.total_seconds() // 60)
            freshness = "Just now" if minutes == 0 else f"{minutes}m ago"
            st.caption(f"⏱️ Freshness: {freshness}")

        with st.sidebar.expander("🔍 Filter Controls", expanded=True):
            state = render_sidebar_filters(df)
            filtered_df = apply_filters(df, state)
            
            if filtered_df.empty:
                st.warning("No records match the current filters.")
    
    # 4. Main Dashboard Tabs
    tab_dashboard, tab_data = st.tabs(["📊 Dashboard", "📋 Data View"])
    
    with tab_dashboard:
        if filtered_df is not None and not filtered_df.empty:
            with st.container():
                # KPI Section
                st.subheader("Performance Overview")
                metrics = compute_kpis(filtered_df)
                render_kpi_cards(metrics)
            
            st.divider()
            
            # Charts Section
            with st.container():
                st.subheader("Trends & Distributions")
                col1, col2 = st.columns(2)
                with col1:
                    with st.container(border=True):
                        st.plotly_chart(delivery_status_pie(filtered_df), use_container_width=True)
                    with st.container(border=True):
                        st.plotly_chart(cod_amount_histogram(filtered_df), use_container_width=True)
            
                with col2:
                    with st.container(border=True):
                        st.plotly_chart(store_distribution_bar(filtered_df), use_container_width=True)
                    with st.container(border=True):
                        st.plotly_chart(daily_trend_line(filtered_df), use_container_width=True)
        else:
            if not data_ready:
                st.image("https://illustrations.popsy.co/gray/delivery-service.svg", width=300)
            st.info("Upload dispatch data to view key metrics and trends.")
    
    with tab_data:
        if filtered_df is not None and not filtered_df.empty:
            st.subheader("Detailed Records")
            render_data_table(filtered_df)
        else:
            st.info("Upload dispatch data to view detailed records.")
    
    # 5. Export Buttons
    if filtered_df is not None and not filtered_df.empty:
        with st.sidebar.expander("💾 Export Data"):
            try:
                st.download_button(
                    "📥 Export CSV", 
                    to_csv_bytes(filtered_df), 
                    "deliveries_filtered.csv", 
                    "text/csv", 
                    use_container_width=True
                )
                st.download_button(
                    "📥 Export Excel", 
                    to_excel_bytes(filtered_df), 
                    "deliveries_filtered.xlsx", 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export failed: {e}")

elif app_mode == "📝 Issue Tracker":
    issue_dashboard.render()