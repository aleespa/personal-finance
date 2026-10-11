"""Pandera schemas for the workbook sheets and user-facing error reporting.

Sheets are validated after their headers are normalized to snake_case, so the
schema column names are snake_case. Errors are reported with the human header
(``account_id`` -> ``Account id``) and the one-based Excel row number.
"""
import pandas as pd
import pandera.pandas as pa

ACCOUNT_TYPES = ["Current", "Savings", "Credit Card", "Loan", "Investment"]
CURRENCIES = ["GBP", "MXN"]
STATUSES = ["Active", "Closed"]


class WorkbookValidationError(ValueError):
    """A sheet in the uploaded workbook does not match the expected format."""


ACCOUNTS_SCHEMA = pa.DataFrameSchema(
    {
        "account_id": pa.Column(str, coerce=True, unique=True),
        "bank": pa.Column(str, coerce=True, nullable=True),
        "account_number": pa.Column(nullable=True, required=False),
        "type": pa.Column(str, pa.Check.isin(ACCOUNT_TYPES)),
        "currency": pa.Column(str, pa.Check.isin(CURRENCIES)),
        "status": pa.Column(str, pa.Check.isin(STATUSES), nullable=True, required=False),
        "closed_date": pa.Column(pa.DateTime, nullable=True, required=False),
    },
    strict=False,
)

BALANCES_SCHEMA = pa.DataFrameSchema(
    {
        "date": pa.Column(pa.DateTime),
        "balance": pa.Column(float, coerce=True),
        "transaction_number": pa.Column(float, coerce=True, nullable=True),
    },
    strict=False,
)

HOLDINGS_SCHEMA = pa.DataFrameSchema(
    {
        "date": pa.Column(pa.DateTime),
        "full_name": pa.Column(str, coerce=True),
        "isin": pa.Column(str, coerce=True),
        "yf_name": pa.Column(str, coerce=True, nullable=True),
        "shares": pa.Column(float, coerce=True),
        "price": pa.Column(float, pa.Check.ge(0), coerce=True),
    },
    strict=False,
)


def validate_sheet(df: pd.DataFrame, schema: pa.DataFrameSchema, sheet: str) -> pd.DataFrame:
    """Validate a normalized sheet, raising WorkbookValidationError listing every problem."""
    try:
        return schema.validate(df, lazy=True)
    except pa.errors.SchemaErrors as errors:
        raise WorkbookValidationError(
            format_failures(errors.failure_cases, sheet)
        ) from None


def parse_dates(
    df: pd.DataFrame, sheet: str, column: str = "date", required: bool = True
) -> pd.DataFrame:
    """Parse a date column day-first, reporting unreadable dates by row.

    With ``required=False`` the column may be absent and cells may be blank,
    but any non-blank cell must still be a readable date.
    """
    header = _header(column)
    if column not in df.columns:
        if not required:
            return df
        raise WorkbookValidationError(
            f"Sheet '{sheet}' is missing the required '{header}' column."
        )
    df = df.copy()
    original = df[column]
    df[column] = pd.to_datetime(original, dayfirst=True, errors="coerce")
    invalid = df[column].isna() if required else df[column].isna() & original.notna()
    if invalid.any():
        problem = "a blank or invalid" if required else "an invalid"
        raise WorkbookValidationError(
            f"Sheet '{sheet}' has {problem} '{header}' in Excel row(s) "
            f"{excel_rows(df.index[invalid])}. Fill in the date or remove those rows."
        )
    return df


def format_failures(failures: pd.DataFrame, sheet: str) -> str:
    lines = []
    failures = failures.copy()
    failures["check"] = failures["check"].astype(str)

    # A failed coercion is also reported as a dtype failure; keep only the first.
    coerce_failed = failures["check"].str.startswith("coerce_dtype")
    failed_cols = set(failures.loc[coerce_failed, "column"])
    failures = failures[
        ~(failures["check"].str.startswith("dtype") & failures["column"].isin(failed_cols))
    ]

    for (column, check), group in failures.groupby(["column", "check"], dropna=False, sort=False):
        header = _header(column)
        values = _values(group["failure_case"])
        rows = excel_rows(group["index"].dropna())
        where = f" in Excel row(s) {rows}" if rows else ""

        if check == "column_in_dataframe":
            missing = ", ".join(f"'{_header(c)}'" for c in group["failure_case"])
            lines.append(f"missing required column(s) {missing}")
        elif check == "not_nullable":
            lines.append(f"'{header}' is blank{where}")
        elif check.startswith("coerce_dtype") or check.startswith("dtype"):
            lines.append(f"'{header}' must be a {_kind(check)}{where} (got {values})")
        elif check.startswith("isin"):
            allowed = _allowed(column)
            lines.append(f"'{header}' must be one of {allowed}{where} (got {values})")
        elif check == "field_uniqueness":
            lines.append(f"'{header}' must be unique; duplicated value(s) {values}{where}")
        elif check.startswith("greater_than_or_equal_to"):
            lines.append(f"'{header}' must not be negative{where} (got {values})")
        else:
            lines.append(f"'{header}' fails {check}{where} (got {values})")

    return f"Sheet '{sheet}' has problems:\n" + "\n".join(f"- {line}" for line in lines)


def _header(column) -> str:
    if column is None or (isinstance(column, float) and pd.isna(column)):
        return "?"
    special = {"isin": "ISIN", "yf_name": "YF name"}
    return special.get(column, str(column).replace("_", " ").capitalize())


def excel_rows(index) -> str:
    # pandas index is zero-based; Excel rows are one-based with a header row.
    rows = sorted({int(i) + 2 for i in index})
    shown = ", ".join(str(r) for r in rows[:10])
    return shown + (f" and {len(rows) - 10} more" if len(rows) > 10 else "")


def _values(cases: pd.Series) -> str:
    unique = list(dict.fromkeys(str(c) for c in cases))
    shown = ", ".join(f"'{v}'" for v in unique[:5])
    return shown + (" ..." if len(unique) > 5 else "")


def _kind(check: str) -> str:
    if "float" in check or "int" in check:
        return "number"
    if "datetime" in check:
        return "date"
    return "text"


def _allowed(column) -> str:
    options = {"type": ACCOUNT_TYPES, "currency": CURRENCIES, "status": STATUSES}
    return ", ".join(options.get(column, []))
