import io

import pandas as pd


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Encode DataFrame as UTF-8 CSV bytes with BOM."""
    output = io.BytesIO()
    df.to_csv(output, index=False, encoding="utf-8-sig")
    return output.getvalue()


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    """Encode DataFrame as .xlsx bytes using openpyxl engine with auto-fit columns."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Filtered Data", index=False)
        # Auto-fit column widths
        worksheet = writer.sheets["Filtered Data"]
        for col_idx, col in enumerate(df.columns, 1):
            max_len = max(
                df[col].astype(str).map(len).max() if not df.empty else 0,
                len(str(col)),
            )
            # Cap width at 50 to avoid excessively wide columns
            worksheet.column_dimensions[worksheet.cell(row=1, column=col_idx).column_letter].width = min(max_len + 2, 50)
    return output.getvalue()
