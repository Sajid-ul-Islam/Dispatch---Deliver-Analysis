import streamlit as st

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

st.set_page_config(page_title="Dispatch & Delivery Report", layout="wide")

st.title("Dispatch & Delivery Report")

# File source selection setup
st.header("Data Source")
input_type = st.radio("Data Input Format", ["Excel (.xlsx)", "Raw Text (.txt)", "Paste Text"], horizontal=True)

df = None

if input_type == "Excel (.xlsx)":
    uploaded = st.file_uploader("Upload Excel file", type=["xlsx"])
    default_path = r"h:\Repo\Dispatch & Deliver Analysis\deliveries_dispatc_sample.xlsx"
    source = uploaded if uploaded else default_path

    if not source:
        st.info("Please upload an Excel file or configure a file path to begin.")
        st.stop()

    try:
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
        raw_text = st.text_area("Paste Raw Text Here", height=300)
        if not raw_text.strip():
            st.info("Please paste raw delivery records to begin.")
            st.stop()
            
    try:
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

with st.expander("Data Preview", expanded=True):
    st.dataframe(df.head(5), use_container_width=True)

st.markdown("---")

# 2. Sidebar filters
state = render_sidebar_filters(df)
filtered_df = apply_filters(df, state)

if filtered_df.empty:
    st.warning("No records match the current filters.")

# 3. KPI section
metrics = compute_kpis(filtered_df)
render_kpi_cards(metrics)

# 4. Charts section
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(delivery_status_pie(filtered_df), width='stretch')
    st.plotly_chart(cod_amount_histogram(filtered_df), width='stretch')

with col2:
    st.plotly_chart(store_distribution_bar(filtered_df), width='stretch')
    st.plotly_chart(daily_trend_line(filtered_df), width='stretch')

# 5. Data table section
st.markdown("### Data Table")
render_data_table(filtered_df)

# 6. Export buttons
st.sidebar.markdown("---")
st.sidebar.header("Export Data")
try:
    st.sidebar.download_button(
        "Export CSV", to_csv_bytes(filtered_df), "deliveries_filtered.csv", "text/csv"
    )
    st.sidebar.download_button(
        "Export Excel", to_excel_bytes(filtered_df), "deliveries_filtered.xlsx", 
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
except Exception as e:
    st.sidebar.error(f"Export failed: {e}")