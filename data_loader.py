import pandas as pd
import streamlit as st
from datetime import datetime

class SchemaValidationError(Exception):
    pass

class DataLoadError(Exception):
    pass

REQUIRED_COLS = [
    "Consignment ID", "Type", "Order ID", "Store",
    "Recipient Name", "Address", "Phone", "Delivery Status",
    "Status Updated On", "COD Amount", "Charge", "Discount",
    "Payment Status", "Action"
]

KNOWN_DELIVERY_STATUSES = {"Pending", "Waiting for Pickup", "Pickup Requested", "Pickup On Hold"}

def validate_schema(df: pd.DataFrame) -> None:
    missing = set(REQUIRED_COLS) - set(df.columns)
    if missing:
        raise SchemaValidationError(f"Missing columns: {', '.join(missing)}")

def coerce_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    # Strip leading/trailing whitespace from strings
    string_cols = df.select_dtypes(include=['object', 'string']).columns
    for col in string_cols:
        df[col] = df[col].astype(str).str.strip()
    
    # Parse Dates and detect issues
    original_dates = df["Status Updated On"].copy()
    df["Status Updated On"] = pd.to_datetime(df["Status Updated On"], format="%d/%m/%Y", errors="coerce")
    
    nat_mask = df["Status Updated On"].isna() & original_dates.notna() & (original_dates != "") & (original_dates != "nan")
    if nat_mask.any():
        bad_indices = df[nat_mask].index.tolist()
        st.warning(f"Could not parse 'Status Updated On' for row indices (coerced to NaT): {bad_indices}")

    # Warn on unknown Delivery Status values
    unknown_statuses = set(df["Delivery Status"]) - KNOWN_DELIVERY_STATUSES
    if unknown_statuses:
        st.warning(f"Unknown Delivery Status values found: {', '.join(unknown_statuses)}")

    # Cast numerics
    for col in ["COD Amount", "Charge", "Discount"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        
    return df

@st.cache_data
def load_data(source) -> tuple[pd.DataFrame, datetime]:
    try:
        # Works for both string path and UploadedFile object via pandas
        raw_df = pd.read_excel(source, engine="openpyxl")
    except FileNotFoundError:
        raise DataLoadError(f"File not found: {source}")
    except ValueError:
        raise DataLoadError("Invalid file format: expected .xlsx")
    except Exception as e:
        raise DataLoadError(f"File is corrupt or unreadable: {e}")
    
    validate_schema(raw_df)
    df = coerce_types(raw_df)
    return df, datetime.now()