import streamlit as st
from data_loader import load_data, DataLoadError, SchemaValidationError
from filters import render_sidebar_filters, apply_filters
from kpi import compute_kpis, render_kpi_cards
from charts import delivery_status_pie, store_distribution_bar, cod_amount_histogram, daily_trend_line
from table import render_data_table
from exporter import to_csv_bytes, to_excel_bytes

st.set_page_config(page_title="Dispatch & Delivery Report", layout="wide")

def main():
    st.title("Dispatch & Delivery Report")
    
    st.sidebar.header("Data Source")
    uploaded = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])
    
    # Fallback default file path for local mode
    source = uploaded or r"h:\Repo\Dispatch & Deliver Analysis\deliveries_dispatc_sample.xlsx"
    
    if not source:
        st.info("Please upload an Excel file or configure a file path to begin.")
        return
        
    try:
        df = load_data(source)
    except DataLoadError as e:
        st.error(str(e))
        return
    except SchemaValidationError as e:
        st.error(f"File schema mismatch: {e}")
        return
        
    filter_state = render_sidebar_filters(df)
    filtered_df = apply_filters(df, filter_state)
    
    if filtered_df.empty:
        st.warning("No records match the current filters.")
        
    render_kpi_cards(compute_kpis(filtered_df))
    st.divider()
    
    col1, col2 = st.columns(2)
    col1.plotly_chart(delivery_status_pie(filtered_df), use_container_width=True)
    col2.plotly_chart(store_distribution_bar(filtered_df), use_container_width=True)
    
    col3, col4 = st.columns(2)
    col3.plotly_chart(cod_amount_histogram(filtered_df), use_container_width=True)
    col4.plotly_chart(daily_trend_line(filtered_df), use_container_width=True)
    
    st.divider()
    st.subheader("Data Details")
    render_data_table(filtered_df)
    
    st.sidebar.divider()
    try:
        st.sidebar.download_button("Export CSV", to_csv_bytes(filtered_df), "deliveries_filtered.csv", "text/csv")
        st.sidebar.download_button("Export Excel", to_excel_bytes(filtered_df), "deliveries_filtered.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        st.sidebar.error(f"Export failed: {e}")

if __name__ == "__main__":
    main()
