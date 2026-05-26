import streamlit as st
import streamlit.components.v1 as components
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

# 1. Page Configuration
st.set_page_config(page_title="Dispatch & Delivery Report", page_icon="📦", layout="wide", initial_sidebar_state="expanded")

st.title("📦 Dispatch & Delivery Report")
st.markdown("Monitor delivery performance, COD collections, and store distributions in real-time.")

# 2. Data Source Configuration
with st.expander("⚙️ Data Source Configuration", expanded=True):
    input_type = st.radio(
        "Select Data Input Format", 
        ["Excel (.xlsx)", "Raw Text (.txt)", "Paste Text"], 
        horizontal=True,
        label_visibility="collapsed"
    )

    df = None

    if input_type == "Excel (.xlsx)":
        source = st.file_uploader("Upload Excel file", type=["xlsx"])

        if not source:
            st.info("Please upload an Excel file to begin.")
            st.stop()

        try:
            with st.spinner("Loading Excel data..."):
                df = load_data(source)
        except SchemaValidationError as e:
            st.error(f"File schema mismatch: {e}")
            st.stop()
        except DataLoadError as e:
            st.error(str(e))
            st.stop()
        except Exception as e:
            st.error(f"Could not read file: {e}")
            st.stop()
    else:
        if input_type == "Raw Text (.txt)":
            uploaded_txt = st.file_uploader("Upload Raw Text file", type=["txt"])
            if uploaded_txt:
                raw_text = uploaded_txt.getvalue().decode("utf-8")
            else:
                st.info("Please upload a text file to parse raw delivery records.")
                st.stop()
        else:
            raw_text = st.text_area("Paste Raw Text Here", height=150, placeholder="Paste your raw delivery records here...")
            if not raw_text.strip():
                st.info("Please paste raw delivery records to begin.")
                st.stop()
                
        try:
            with st.spinner("Parsing text data..."):
                parsed_df = parse_records(raw_text)
                if parsed_df.empty:
                    parsed_df = parse_data_fuzzy(raw_text)
                
                if parsed_df.empty:
                    st.warning("No records could be parsed from the provided text.")
                    st.stop()
                    
                validate_schema(parsed_df)
                df = coerce_types(parsed_df)
        except SchemaValidationError as e:
            st.error(f"Parsed schema mismatch: {e}")
            st.stop()
        except Exception as e:
            st.error(f"Could not parse text: {e}")
            st.stop()

# 3. Sidebar Filters
st.sidebar.header("🔍 Filters")
state = render_sidebar_filters(df)
filtered_df = apply_filters(df, state)

if filtered_df.empty:
    st.warning("No records match the current filters.")
    st.stop()

# 4. Main Dashboard Tabs
tab_dashboard, tab_data, tab_issues = st.tabs(["📊 Dashboard", "📋 Data View", "📝 Issue Log"])

with tab_dashboard:
    # KPI Section
    st.subheader("Key Metrics")
    metrics = compute_kpis(filtered_df)
    render_kpi_cards(metrics)
    
    st.divider()
    
    # Charts Section
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

with tab_data:
    st.subheader("Detailed Records")
    render_data_table(filtered_df)

with tab_issues:
    st.subheader("Issue Log")
    st.markdown("Track and report issues directly in the embedded spreadsheet below or open the [Google Spreadsheet](https://docs.google.com/spreadsheets/d/1NwuJPzjNZEggxYI7585hT8w9qK7HVJk43Pgv6NHG3j4/edit?gid=0#gid=0) in a new tab.")
    components.iframe("https://docs.google.com/spreadsheets/d/1NwuJPzjNZEggxYI7585hT8w9qK7HVJk43Pgv6NHG3j4/edit?gid=0&rm=minimal", height=800, scrolling=True)

# 5. Export Buttons
st.sidebar.divider()
st.sidebar.header("💾 Export Data")
try:
    st.sidebar.download_button(
        "📥 Export CSV", 
        to_csv_bytes(filtered_df), 
        "deliveries_filtered.csv", 
        "text/csv", 
        use_container_width=True
    )
    st.sidebar.download_button(
        "📥 Export Excel", 
        to_excel_bytes(filtered_df), 
        "deliveries_filtered.xlsx", 
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
        use_container_width=True
    )
except Exception as e:
    st.sidebar.error(f"Export failed: {e}")