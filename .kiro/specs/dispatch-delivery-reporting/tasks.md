# Implementation Plan: Dispatch & Delivery Reporting System

## Overview

Build a Streamlit-based interactive reporting dashboard in Python. The implementation follows the modular architecture defined in the design: `data_loader.py`, `filters.py`, `kpi.py`, `charts.py`, `table.py`, `exporter.py`, and `app.py`. All data processing uses pandas; all visualisations use Plotly. Property-based tests use Hypothesis; unit tests use pytest.

## Tasks

- [ ] 1. Set up project structure and dependencies
  - Create `requirements.txt` with pinned versions: `streamlit>=1.32`, `pandas>=2.0`, `plotly>=5.18`, `openpyxl>=3.1`, `hypothesis>=6.0`, `pytest>=8.0`
  - Create the `tests/` directory with empty `__init__.py` and placeholder test files: `test_data_loader.py`, `test_filters.py`, `test_kpi.py`, `test_charts.py`, `test_exporter.py`
  - Create empty module stubs: `data_loader.py`, `filters.py`, `kpi.py`, `charts.py`, `table.py`, `exporter.py`, `app.py`
  - _Requirements: 1.1, 2.1_

- [ ] 2. Implement DataLoader (`data_loader.py`)
  - [ ] 2.1 Define custom exceptions and `load_data` function
    - Define `SchemaValidationError` and `DataLoadError` exception classes
    - Implement `load_data(source: str | UploadedFile) -> pd.DataFrame` accepting both a file path string and a Streamlit `UploadedFile` object
    - Apply `@st.cache_data` keyed on file content hash / mtime
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

  - [ ] 2.2 Implement `validate_schema` and `coerce_types`
    - Implement `validate_schema(df)` asserting all 14 required columns are present; raise `SchemaValidationError` listing missing columns if any are absent
    - Implement `coerce_types(df)`: parse `Status Updated On` as `datetime` with format `%d/%m/%Y` (errors → `NaT`); cast `COD Amount`, `Charge`, `Discount` to numeric (errors → 0); strip whitespace from all string columns
    - Emit a warning (return list of affected row indices) when `Status Updated On` values coerce to `NaT`
    - Emit a warning when `Delivery Status` contains values outside the 4 known values
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7_

  - [ ]* 2.3 Write unit tests for DataLoader
    - `test_load_data_valid_file` — loads sample file, asserts shape (93 rows × 14 cols) and dtypes
    - `test_load_data_missing_column` — asserts `SchemaValidationError` raised with correct message
    - `test_load_data_corrupt_file` — asserts `DataLoadError` raised
    - `test_coerce_types_dates` — valid dates parsed, unparseable → `NaT`
    - `test_coerce_types_numerics` — non-numeric values coerced to 0
    - `test_coerce_types_whitespace` — leading/trailing whitespace stripped
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6_

  - [ ]* 2.4 Write property test for schema tolerance (Property 7)
    - **Property 7: Schema Tolerance**
    - For any DataFrame, `load_data` raises `SchemaValidationError` if and only if at least one of the 14 required columns is absent
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 2.5 Write property test for date parse safety (Property 8)
    - **Property 8: Date Parse Safety**
    - For any DataFrame containing unparseable `Status Updated On` values, `load_data` coerces those values to `NaT` without raising an exception
    - **Validates: Requirements 2.3, 2.4**

- [ ] 3. Implement FilterEngine (`filters.py`)
  - [ ] 3.1 Define `FilterState` dataclass and `render_sidebar_filters`
    - Define `FilterState` dataclass with fields: `stores: list[str]`, `statuses: list[str]`, `payment_statuses: list[str]`, `date_from: date | None`, `date_to: date | None`, `search_text: str`
    - Implement `render_sidebar_filters(df: pd.DataFrame) -> FilterState` deriving all option lists dynamically from the DataFrame (no hardcoded values); default to "Select All" for multi-selects and full date extent for date range
    - _Requirements: 3.1, 3.2_

  - [ ] 3.2 Implement `apply_filters`
    - Implement `apply_filters(df: pd.DataFrame, state: FilterState) -> pd.DataFrame` applying all active filter conditions as a combined boolean mask
    - Store filter: `df["Store"].isin(state.stores)` when non-empty
    - Delivery status filter: `df["Delivery Status"].isin(state.statuses)` when non-empty
    - Payment status filter: `df["Payment Status"].isin(state.payment_statuses)` when non-empty
    - Date range filter: inclusive bounds; exclude `NaT` rows when date filter is active; handle one-sided bounds; return empty DataFrame when start > end
    - Free-text search: case-insensitive substring match on `Consignment ID` and `Recipient Name`
    - Return empty DataFrame (not error) when zero rows match; reset index
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11_

  - [ ]* 3.3 Write unit tests for FilterEngine
    - `test_apply_filters_no_filters` — returns full DataFrame unchanged
    - `test_apply_filters_store` — single store filter returns only matching rows
    - `test_apply_filters_date_range` — inclusive bounds, one-sided bounds, start > end → empty
    - `test_apply_filters_empty_result` — returns empty DataFrame, not error
    - `test_apply_filters_search_text` — case-insensitive substring match
    - `test_apply_filters_combined` — multiple active filters return intersection
    - `test_apply_filters_nat_dates` — NaT rows excluded when date filter active
    - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 3.11_

  - [ ]* 3.4 Write property test for filter completeness (Property 1)
    - **Property 1: Filter Completeness**
    - For any `FilterState` and any DataFrame, every row in `apply_filters(df, state)` satisfies all active filter predicates simultaneously
    - **Validates: Requirements 3.3, 3.4, 3.5, 3.6, 3.7, 3.8**

  - [ ]* 3.5 Write property test for filter subset (Property 2)
    - **Property 2: Filter Subset**
    - For any `FilterState` and any DataFrame, `len(apply_filters(df, state)) <= len(df)`
    - **Validates: Requirements 3.2, 3.8, 3.9**

- [ ] 4. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement KPIEngine (`kpi.py`)
  - [ ] 5.1 Define `KPIMetrics` dataclass and `compute_kpis`
    - Define `KPIMetrics` dataclass with fields: `total_parcels: int`, `total_cod: float`, `total_charges: float`, `total_discounts: float`, `net_revenue: float`, `pending_count: int`, `pickup_requested_count: int`
    - Implement `compute_kpis(df: pd.DataFrame) -> KPIMetrics`; handle empty DataFrame by returning all-zero metrics; compute `net_revenue = total_charges - total_discounts`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 5.2 Implement `render_kpi_cards`
    - Implement `render_kpi_cards(metrics: KPIMetrics) -> None` rendering 7 metrics as `st.metric` cards in a 4-column layout
    - Format currency values with ৳ prefix and comma separators (e.g. ৳1,747); format integer counts with comma separators for values ≥ 1,000
    - Display `net_revenue` in red when negative
    - _Requirements: 4.5, 4.6, 4.7_

  - [ ]* 5.3 Write unit tests for KPIEngine
    - `test_compute_kpis_empty_df` — all metrics are 0
    - `test_compute_kpis_consistency` — `total_parcels == len(df)`
    - `test_compute_kpis_net_revenue` — `net_revenue == total_charges - total_discounts`
    - `test_compute_kpis_pending_count` — counts only rows with `Delivery Status == "Pending"`
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ]* 5.4 Write property test for KPI consistency (Property 3)
    - **Property 3: KPI Consistency**
    - For any DataFrame with the required columns, `compute_kpis(df).total_parcels == len(df)` always holds
    - **Validates: Requirements 4.3**

  - [ ]* 5.5 Write property test for KPI non-negativity (Property 4)
    - **Property 4: KPI Non-Negativity**
    - For any DataFrame with non-negative numeric columns, all numeric fields in `compute_kpis(df)` are ≥ 0
    - **Validates: Requirements 4.1, 4.2**

- [ ] 6. Implement ChartEngine (`charts.py`)
  - [ ] 6.1 Implement `delivery_status_pie` and `store_distribution_bar`
    - Implement `delivery_status_pie(df: pd.DataFrame) -> go.Figure`: pie/donut chart of parcel count by `Delivery Status`; return "No data" annotated figure for empty DataFrame
    - Implement `store_distribution_bar(df: pd.DataFrame) -> go.Figure`: horizontal bar chart of parcel count by `Store`, sorted descending; return "No data" annotated figure for empty DataFrame
    - Apply the shared `Pastel` colour palette to both figures
    - _Requirements: 5.1, 5.2, 5.5, 5.6, 5.7_

  - [ ] 6.2 Implement `cod_amount_histogram` and `daily_trend_line`
    - Implement `cod_amount_histogram(df: pd.DataFrame) -> go.Figure`: histogram of `COD Amount` distribution, excluding null/non-numeric rows; return "No data" annotated figure for empty DataFrame
    - Implement `daily_trend_line(df: pd.DataFrame) -> go.Figure`: line chart of parcel count grouped by calendar day of `Status Updated On`, excluding `NaT` rows; return "No data" annotated figure for empty DataFrame
    - Apply the shared `Pastel` colour palette to both figures
    - _Requirements: 5.3, 5.4, 5.5, 5.6, 5.7_

  - [ ]* 6.3 Write property test for chart safety (Property 5)
    - **Property 5: Chart Safety**
    - For any DataFrame (including empty), all four chart factory functions return a valid `go.Figure` without raising an exception
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.4, 5.5**

  - [ ]* 6.4 Write unit tests for ChartEngine
    - `test_delivery_status_pie_empty` — returns `go.Figure` with "No data" annotation
    - `test_store_distribution_bar_sorted` — bars are in descending order by count
    - `test_cod_histogram_excludes_nulls` — null COD rows not included
    - `test_daily_trend_excludes_nat` — NaT date rows not included
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7. Implement DataTable (`table.py`)
  - [ ] 7.1 Implement `render_data_table`
    - Implement `render_data_table(df: pd.DataFrame) -> None`
    - Display row count above the table in the format "Showing N record(s)"
    - Render using `st.dataframe` with `column_config`: `COD Amount`, `Charge`, `Discount` as `NumberColumn` with format `৳%.2f`; `Status Updated On` as `DateColumn` with format `DD/MM/YYYY`
    - Default visible columns: `Consignment ID`, `Store`, `Recipient Name`, `Delivery Status`, `Status Updated On`, `COD Amount`
    - Provide a "Show all columns" toggle to render all 14 columns
    - Highlight rows where `Delivery Status == "Pending"` with a visually distinct background
    - Display "No records found." and skip the table widget when DataFrame is empty
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [ ] 8. Implement Exporter (`exporter.py`)
  - [ ] 8.1 Implement `to_csv_bytes` and `to_excel_bytes`
    - Implement `to_csv_bytes(df: pd.DataFrame) -> bytes`: encode DataFrame as UTF-8 CSV with BOM; include column headers as first row; handle empty DataFrame (headers only)
    - Implement `to_excel_bytes(df: pd.DataFrame) -> bytes`: encode DataFrame as `.xlsx` using openpyxl engine; single sheet named `Filtered Data`; auto-fit column widths; include column headers; handle empty DataFrame (headers only)
    - Both functions must be pure: no file writes to disk, no `st.*` calls
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 8.2 Write unit tests for Exporter
    - `test_to_csv_bytes_roundtrip` — re-read CSV equals original DataFrame
    - `test_to_excel_bytes_roundtrip` — re-read Excel equals original DataFrame
    - `test_to_csv_bytes_empty` — returns header-only bytes, no error
    - `test_to_excel_bytes_empty` — returns header-only bytes, no error
    - `test_exporter_no_side_effects` — no files written to disk
    - _Requirements: 7.3, 7.4, 7.5_

  - [ ]* 8.3 Write property test for export round-trip (Property 6)
    - **Property 6: Export Round-Trip**
    - For any DataFrame, exporting to Excel bytes with `to_excel_bytes` and re-reading with `pd.read_excel` produces a DataFrame with the same shape and values as the original
    - **Validates: Requirements 7.1, 7.2, 7.3, 7.4**

- [ ] 9. Checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implement main application (`app.py`)
  - [ ] 10.1 Wire file source selection and data loading
    - Call `st.set_page_config(title="Dispatch & Delivery Report", layout="wide")`
    - Render a sidebar file uploader (`st.file_uploader`) and fall back to the pre-configured file path when no file is uploaded
    - Display "Please upload an Excel file or configure a file path to begin." and halt rendering when no source is available
    - Call `load_data(source)` inside a try/except block; display `st.error` for `DataLoadError` and `SchemaValidationError` (with missing column list) and halt rendering on error
    - Display a `st.warning` banner listing affected row indices when `Status Updated On` values coerce to `NaT`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.4, 8.1, 8.2, 8.4_

  - [ ] 10.2 Wire sidebar filters and dashboard sections
    - Call `render_sidebar_filters(df)` to obtain `FilterState`; call `apply_filters(df, state)` to obtain `filtered_df`
    - Display "No records match the current filters." when `filtered_df` is empty
    - Call `render_kpi_cards(compute_kpis(filtered_df))` to render the KPI section
    - Render four charts in a 2-column layout (2 rows × 2 cols) using `st.columns(2)` and `plotly_chart(..., use_container_width=True)`
    - Call `render_data_table(filtered_df)` to render the data table section
    - _Requirements: 3.9, 4.5, 5.6, 6.1, 8.3_

  - [ ] 10.3 Wire export buttons
    - Call `to_csv_bytes(filtered_df)` and `to_excel_bytes(filtered_df)` and pass results to `st.download_button`
    - CSV button: label "Export CSV", filename `deliveries_filtered.csv`, mime `text/csv`
    - Excel button: label "Export Excel", filename `deliveries_filtered.xlsx`, mime `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
    - Wrap export calls in try/except; display `st.error("Export failed: {reason}")` and suppress the download button on failure
    - _Requirements: 7.1, 7.2, 7.6, 8.5_

- [ ] 11. Integration end-to-end validation
  - [ ] 11.1 Write integration tests using the sample file
    - Load `deliveries_dispatc_sample.xlsx` end-to-end through all components
    - Assert DataFrame shape is 93 rows × 14 columns after loading
    - Assert KPI values match manually computed expected values from the known data profile
    - Assert all 4 chart figures are generated without error
    - Assert CSV and Excel exports are non-empty and re-readable with correct shape
    - _Requirements: 1.1, 1.2, 4.1, 5.1, 5.2, 5.3, 5.4, 7.1, 7.2_

- [ ] 12. Final checkpoint — Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at logical boundaries
- Property tests (Properties 1–8) validate universal correctness guarantees using Hypothesis
- Unit tests validate specific examples and edge cases using pytest
- The sample file (`deliveries_dispatc_sample.xlsx`) is used as the integration test fixture

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "2.2"] },
    { "id": 2, "tasks": ["2.3", "2.4", "2.5", "3.1"] },
    { "id": 3, "tasks": ["3.2"] },
    { "id": 4, "tasks": ["3.3", "3.4", "3.5", "5.1"] },
    { "id": 5, "tasks": ["5.2", "6.1", "8.1"] },
    { "id": 6, "tasks": ["5.3", "5.4", "5.5", "6.2", "7.1", "8.2", "8.3"] },
    { "id": 7, "tasks": ["6.3", "6.4", "10.1"] },
    { "id": 8, "tasks": ["10.2"] },
    { "id": 9, "tasks": ["10.3"] },
    { "id": 10, "tasks": ["11.1"] }
  ]
}
```
