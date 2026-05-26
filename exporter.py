import io
import pandas as pd
from openpyxl.utils import get_column_letter


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Encode DataFrame as UTF-8 CSV bytes with BOM."""
    return df.to_csv(index=False).encode('utf-8-sig')


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Encode DataFrame as .xlsx bytes using openpyxl engine."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Filtered Data')
        
        # Auto-fit column widths
        worksheet = writer.sheets['Filtered Data']
        for i, col in enumerate(df.columns, 1):
            max_len = len(str(col))
            if not df.empty:
                max_len = max(max_len, df[col].astype(str).map(len).max())
            worksheet.column_dimensions[get_column_letter(i)].width = max_len + 2
            
    return output.getvalue()