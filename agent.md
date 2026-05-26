# AI Agent Instructions

This file provides context and guidelines for AI assistants working in this repository.

## Project Details
- **Project Name**: Dispatch & Deliver Analysis
- **Domain**: Logistics and Delivery Performance Reporting
- **Core Technologies**: Python 3.10+, Streamlit, Pandas, Plotly (Express & Graph Objects), OpenPyXL

## Architecture & Organization
- **Modular Design**: Logic is decoupled into functional modules (`data_loader.py`, `filters.py`, `kpi.py`, `charts.py`, `table.py`, `exporter.py`).
- **Multi-Module Support**: The app features distinct modules for "Dispatch Analysis" and "Issue Tracking" (`issue_dashboard.py`).
- **Specification Driven**: Development should align with the requirements and design docs located in `.kiro/specs/`.

## Code Guidelines
- Prioritize clean, readable, and well-documented Python code.
- **Type Hinting**: Use type hints for all function signatures and data structures (e.g., `dataclasses`).
- **Streamlit Optimization**: Utilize `@st.cache_data` for data ingestion and heavy computations to ensure UI responsiveness.
- **Robust Error Handling**: Implement custom exceptions (like `SchemaValidationError`) and handle data quality issues (NaT dates, numeric coercion) gracefully.
- Follow PEP 8 style guidelines.
- Keep functions focused on a single responsibility.
- **Functional Purity**: Keep backend logic (e.g., `exporter.py`) free of Streamlit `st.*` calls to facilitate testing.

## UI/UX Standards
- **Visual Hierarchy**: Use card-based layouts with `st.container(border=True)` for metrics and visualizations.
- **Sidebar Organization**: Group filters, summaries, and export actions into expanders or dedicated containers to prevent vertical clutter.
- **Branding & Consistency**: Use the `Pastel` color sequence for all Plotly charts.
- **Information Density**: Provide immediate data feedback (e.g., "Data Summary" and "Freshness" indicators) in the sidebar.

## Data & Performance
- **Vectorization**: Prefer Pandas vectorized operations over manual iteration for filtering and KPI calculations.
- **Schema Validation**: Explicitly validate incoming data against the expected 14-column schema.

## Testing Strategy
- **Unit Testing**: Use `pytest` for functional validation.
- **Property-Based Testing**: Use `hypothesis` for verifying filter and export round-trip logic.