# Requirements Document

## Introduction

The Dispatch & Delivery Reporting System is a self-contained Streamlit dashboard that ingests a dispatch and delivery Excel file, applies multi-dimensional filters, displays KPI summary cards and interactive charts, renders a searchable data table, and allows export of filtered results to CSV or Excel. The system is designed for operational reporting on parcel delivery data and requires no backend beyond the Streamlit process itself.

## Glossary

- **Dashboard**: The Streamlit web application that renders all reporting components.
- **DataLoader**: The `data_loader.py` module responsible for ingesting, validating, and type-coercing the Excel file.
- **FilterEngine**: The `filters.py` module responsible for applying sidebar filter state to the loaded DataFrame.
- **KPIEngine**: The `kpi.py` module responsible for computing aggregate metrics from the filtered DataFrame.
- **ChartEngine**: The `charts.py` module responsible for producing Plotly figures for all chart types.
- **DataTable**: The `table.py` module responsible for rendering the searchable, sortable data table.
- **Exporter**: The `exporter.py` module responsible for converting a DataFrame to downloadable CSV or Excel bytes.
- **FilterState**: A data structure capturing the current values of all active sidebar filters (stores, statuses, date range, search text).
- **KPIMetrics**: A data structure holding all computed aggregate metric values (total parcels, total COD, charges, discounts, net revenue, pending count).
- **DeliveryRecord**: A single row of the delivery Excel file, representing one parcel consignment.
- **SchemaValidationError**: A typed exception raised when the loaded file is missing one or more required columns.
- **DataLoadError**: A typed exception raised when the file cannot be read (e.g. corrupt file, wrong format).
- **NaT**: Pandas "Not a Time" — the null value for datetime columns, used when a date string cannot be parsed.
- **COD**: Cash on Delivery — the monetary amount collected from the recipient upon delivery.

---

## Requirements

### Requirement 1: File Ingestion

**User Story:** As a logistics analyst, I want to load delivery data from an Excel file by uploading it or specifying a file path, so that I can analyse the latest dispatch and delivery records without manual data entry.

#### Acceptance Criteria

1. WHEN a user uploads a file via the file uploader, IF the file has a `.xlsx` extension, is readable by openpyxl, and is no larger than 50 MB, THEN THE DataLoader SHALL read the file into a DataFrame and return it to the Dashboard.
2. WHEN a pre-configured file path is provided and the file exists, THE DataLoader SHALL read the file from that path and return a DataFrame that has been validated for required column presence.
3. WHEN a file is loaded successfully, THE DataLoader SHALL cache the result keyed on the file content hash, and SHALL invalidate the cache when a new file is loaded.
4. IF a file path does not exist or the file extension is not `.xlsx`, THEN THE DataLoader SHALL raise a `DataLoadError` with the message "File not found or unsupported format" and THE Dashboard SHALL display that message to the user.
5. IF a file with a `.xlsx` extension cannot be read or parsed by openpyxl, THEN THE DataLoader SHALL raise a `DataLoadError` with the message "File is corrupt or unreadable" and THE Dashboard SHALL display that message to the user.
6. WHEN no file has been uploaded or configured, THE Dashboard SHALL display the prompt "Please upload an Excel file or configure a file path to begin." and SHALL NOT render any KPI cards, charts, or data table.
7. IF a loaded file is missing one or more required columns, THEN THE DataLoader SHALL raise a `SchemaValidationError` listing the missing column names and THE Dashboard SHALL display the missing column names without rendering any dashboard components.

---

### Requirement 2: Schema Validation and Type Coercion

**User Story:** As a logistics analyst, I want the system to validate and normalise the loaded data automatically, so that I can trust the accuracy of all metrics and filters without manually inspecting the raw file.

#### Acceptance Criteria

1. THE DataLoader SHALL validate that all 14 required columns are present in the loaded file: `Consignment ID`, `Type`, `Order ID`, `Store`, `Recipient Name`, `Address`, `Phone`, `Delivery Status`, `Status Updated On`, `COD Amount`, `Charge`, `Discount`, `Payment Status`, `Action`.
2. IF one or more required columns are absent, THEN THE DataLoader SHALL raise a `SchemaValidationError` listing the missing column names, abort loading, and THE Dashboard SHALL display the missing column names to the user.
3. IF the file passes schema validation, THEN THE DataLoader SHALL parse the `Status Updated On` column as `datetime` using the format `dd/mm/yyyy`.
4. WHEN a `Status Updated On` value cannot be parsed as a date, THE DataLoader SHALL coerce it to `NaT` and THE Dashboard SHALL display a warning listing the row indices of the affected rows.
5. IF the file passes schema validation, THEN THE DataLoader SHALL cast `COD Amount`, `Charge`, and `Discount` columns to numeric, coercing non-numeric values to `0`.
6. IF the file passes schema validation, THEN THE DataLoader SHALL strip leading and trailing whitespace from all string columns.
7. IF a `Delivery Status` value is not one of the four known values (`Pending`, `Waiting for Pickup`, `Pickup Requested`, `Pickup On Hold`), THEN THE DataLoader SHALL emit a warning via the Dashboard warning banner and SHALL NOT raise an error.

---

### Requirement 3: Multi-Dimensional Filtering

**User Story:** As a logistics analyst, I want to filter the delivery data by store, delivery status, payment status, date range, and free-text search, so that I can focus on specific subsets of records relevant to my analysis.

#### Acceptance Criteria

1. THE FilterEngine SHALL derive option lists for the Store, Delivery Status, and Payment Status filters dynamically from the unique values present in the loaded DataFrame, with no hardcoded values.
2. WHEN no filter selections are active, THE FilterEngine SHALL return the full unmodified DataFrame.
3. WHEN one or more stores are selected, THE FilterEngine SHALL return only rows where `Store` matches one of the selected values.
4. WHEN one or more delivery statuses are selected, THE FilterEngine SHALL return only rows where `Delivery Status` matches one of the selected values.
5. WHEN one or more payment statuses are selected, THE FilterEngine SHALL return only rows where `Payment Status` matches one of the selected values.
6. WHEN a date range is specified with a valid start date ≤ end date, THE FilterEngine SHALL return only rows where `Status Updated On` falls within the range, inclusive of both the start and end dates. IF only a start date is provided, THE FilterEngine SHALL return rows on or after the start date. IF only an end date is provided, THE FilterEngine SHALL return rows on or before the end date. IF start date > end date, THE FilterEngine SHALL return an empty DataFrame.
7. WHEN a free-text search string of 1–200 characters is entered, THE FilterEngine SHALL return only rows where `Consignment ID` or `Recipient Name` contains the search string as a case-insensitive substring.
8. WHEN multiple filters are active simultaneously, THE FilterEngine SHALL return only rows that satisfy all active filter conditions.
9. IF active filters produce zero matching rows, THEN THE FilterEngine SHALL return an empty DataFrame and THE Dashboard SHALL display the message "No records match the current filters." without raising an error.
10. WHEN a date range filter is active, THE FilterEngine SHALL exclude rows with `NaT` dates from the filtered result.
11. WHEN a one-sided date filter is active (start date only or end date only), THE FilterEngine SHALL apply only the specified bound and treat the other bound as unbounded.

---

### Requirement 4: KPI Summary Cards

**User Story:** As a logistics analyst, I want to see key performance indicators summarised at the top of the dashboard, so that I can quickly assess the overall state of the filtered delivery data.

#### Acceptance Criteria

1. WHEN the filtered DataFrame is available for computation, THE KPIEngine SHALL compute the following metrics: total parcels, total COD amount, total charges, total discounts, net revenue, pending count, and pickup-requested count.
2. THE KPIEngine SHALL compute `net_revenue` as `total_charges − total_discounts`.
3. THE KPIEngine SHALL compute `total_parcels` as the row count of the filtered DataFrame.
4. WHEN the filtered DataFrame is empty, THE KPIEngine SHALL return all numeric metrics as `0`.
5. WHEN KPI metrics are available, THE Dashboard SHALL render them as formatted cards in a 4-column layout using `st.metric`.
6. THE Dashboard SHALL format `total_cod`, `total_charges`, `total_discounts`, and `net_revenue` with the ৳ prefix and comma separators (e.g. ৳1,747). `total_parcels`, `pending_count`, and `pickup_requested_count` SHALL be formatted as integers with comma separators for values ≥ 1,000.
7. IF `net_revenue` is negative, THE Dashboard SHALL display the value in red to indicate a loss.

---

### Requirement 5: Interactive Charts

**User Story:** As a logistics analyst, I want to see interactive charts visualising delivery status distribution, store distribution, COD amount distribution, and daily delivery trends, so that I can identify patterns and anomalies in the data.

#### Acceptance Criteria

1. THE ChartEngine SHALL produce a pie or donut chart showing parcel count by `Delivery Status` from the filtered DataFrame.
2. THE ChartEngine SHALL produce a horizontal bar chart showing parcel count by `Store` from the filtered DataFrame, sorted in descending order by parcel count.
3. THE ChartEngine SHALL produce a histogram showing the distribution of `COD Amount` values from the filtered DataFrame, excluding rows where `COD Amount` is null or non-numeric.
4. THE ChartEngine SHALL produce a line chart showing parcel count grouped by calendar day of `Status Updated On` from the filtered DataFrame, excluding rows where `Status Updated On` is `NaT`.
5. WHEN the filtered DataFrame is empty, THE ChartEngine SHALL return a valid `go.Figure` containing a centred "No data" annotation for each chart type, without raising an exception.
6. THE Dashboard SHALL render the four charts in a 2-column layout: row 1 contains the delivery status pie chart (left) and store distribution bar chart (right); row 2 contains the COD histogram (left) and daily trend line chart (right). Each chart SHALL use `use_container_width=True`.
7. THE ChartEngine SHALL apply the same named discrete colour sequence (e.g. Plotly's `Pastel` palette) to all four chart figures.

---

### Requirement 6: Searchable Data Table

**User Story:** As a logistics analyst, I want to view the filtered delivery records in a sortable, searchable table, so that I can inspect individual records and verify the data underlying the KPIs and charts.

#### Acceptance Criteria

1. THE DataTable SHALL render the filtered DataFrame using `st.dataframe` with `column_config` applied: `COD Amount`, `Charge`, and `Discount` SHALL use `NumberColumn` with format `৳%.2f`; `Status Updated On` SHALL use `DateColumn` with format `DD/MM/YYYY`.
2. THE DataTable SHALL display the row count of the filtered DataFrame above the table in the format "Showing N record(s)".
3. IF a row's `Delivery Status` equals `Pending`, THEN THE DataTable SHALL render that row with a visually distinct background colour that differs from the default row background.
4. THE DataTable SHALL display the following 6 columns by default: `Consignment ID`, `Store`, `Recipient Name`, `Delivery Status`, `Status Updated On`, `COD Amount`.
5. WHEN the user selects "Show all columns", THE DataTable SHALL render all 14 columns.
6. IF the filtered DataFrame contains zero rows, THEN THE DataTable SHALL display the message "No records found." and SHALL NOT render the table widget.

---

### Requirement 7: Data Export

**User Story:** As a logistics analyst, I want to export the currently filtered data to CSV or Excel, so that I can share results with stakeholders or perform further analysis in external tools.

#### Acceptance Criteria

1. WHEN the user clicks the "Export CSV" button, THE Dashboard SHALL initiate a browser file download of the filtered DataFrame as a UTF-8 CSV file with BOM, named `deliveries_filtered.csv`.
2. WHEN the user clicks the "Export Excel" button, THE Dashboard SHALL initiate a browser file download of the filtered DataFrame as an `.xlsx` file with a single sheet named `Filtered Data`, named `deliveries_filtered.xlsx`.
3. THE Exporter SHALL produce bytes that are non-empty, parseable by standard CSV/Excel readers without error, and contain the column headers as the first row, for any DataFrame including an empty one.
4. THE Exporter SHALL be a pure function with no side effects: it SHALL NOT write files to disk and SHALL NOT call any `st.*` functions.
5. WHEN the filtered DataFrame is empty, THE Exporter SHALL return a header-only file for both CSV and Excel formats without raising an error.
6. IF THE Exporter raises an exception during export, THEN THE Dashboard SHALL display an error message "Export failed: {reason}" and SHALL NOT initiate a file download.

---

### Requirement 8: Error Handling and Resilience

**User Story:** As a logistics analyst, I want the dashboard to handle data quality issues and user errors gracefully, so that I can continue working without the application crashing or losing my filter state.

#### Acceptance Criteria

1. IF a file path does not exist, THEN THE Dashboard SHALL display the error "File not found: {path}" and the file upload control SHALL remain enabled. IF the file exists but is not a valid `.xlsx` workbook, THEN THE Dashboard SHALL display the error "Invalid file format: expected .xlsx" and the file upload control SHALL remain enabled.
2. WHEN schema validation fails, THE Dashboard SHALL display the list of missing column names and SHALL NOT render any KPI cards, charts, or data table until a valid file is provided.
3. WHEN all rows are filtered out, THE Dashboard SHALL display zero-value KPI cards, "No data" chart annotations, and the message "No records found." in the table area, and SHALL NOT raise an error.
4. WHEN unparseable date values are present, THE Dashboard SHALL display a warning banner listing the row numbers of the affected rows and SHALL continue rendering KPI cards, charts, and the data table for all non-date-filtered views normally.
5. WHEN the user clicks an export button while the filtered DataFrame is empty, THE Exporter SHALL return a valid header-only file and THE Dashboard SHALL complete the download without error.
