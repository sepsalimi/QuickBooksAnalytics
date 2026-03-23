# parse_data.py
# Reads the Istanbul Doner Shop P&L Excel report and returns structured DataFrames
# for use in the Streamlit app. The report is a hierarchical text-style export
# from QuickBooks, not a flat table, so we extract rows by their label names.

import pandas as pd

# --- Known row labels in the report ---

INCOME_ITEM_LABELS = [
    "Clover Sales",
    "Clover Suspense",
    "Refund",
    "Doordash Income",
    "Skip Income",
    "Square Income",
    "Uber Income",
    "Zomi Income",
]

COGS_ITEM_LABELS = [
    "Al Salam",
    "Aria Market",
    "Ayoub Dried Fruits",
    "Baklava",
    "Capital One",
    "Costco",
    "Drinks",
    "Falafel",
    "Fruits & Vegetables (Kin's Farm Den)",
    "Himalaya Dairy",
    "Jasmine",
    "Meat & Fat (Aman Halal Meat)",
    "Meat & Fat (Westcadia Foods)",
    "Mediterranean Speciality",
    "NoFrills",
    "Persia Foods",
    "Sucuk",
    "Tandoor Bakery",
    "Vegetables (Sunrise Market)",
    "Walmart",
    "WholeSale Club",
]

# Maps expense category name -> list of line item labels belonging to it
EXPENSE_CATEGORIES = {
    "Advertising": ["Facebook/Instagram", "Indeed", "Printing"],
    "Bank charges": ["Bank charges"],
    "Commissions and fees": ["Clover Fees", "Hinbor Kiosk Fees", "Square Fees"],
    "Cost of Labour": ["Cost of Labour"],
    "Dues and Subscriptions": ["Domain Name", "Quickbook Subscription", "Spotify"],
    "Equipment Rental": ["Dishwasher Rental", "Security Alarm"],
    "Insurance": [
        "Car Insurance",
        "IC Premium Financing Insurance",
        "Restaurant Insurance",
        "WorksafeBC",
    ],
    "Interest expense": ["Interest expense"],
    "Legal and professional fees": ["Accountant"],
    "Meals and entertainment": ["Meals and entertainment"],
    "Other General and Administrative Expenses": ["Laundry Service"],
    "Rent or lease payments": ["Car Lease", "Restaurant Lease"],
    "Repair and maintenance": ["Adam Tank", "Countertop Construction", "Lock Change", "Waterman"],
    "Shipping and delivery": ["Greencan", "Moe Ashki"],
    "Supplies": [
        "Amazon",
        "Babak Food Equipment",
        "Dollarama",
        "Home Depot",
        "Hudson Bay",
        "Medical (Shoppers)",
        "Paragon Food",
        "Rona",
        "Staples",
        "Summit Tools",
        "Temu",
        "Vancouver Restaurant Supp",
    ],
    "Taxes and Licenses": [
        "Backflow",
        "Halal License",
        "Remittance",
        "Vancouver Coastal Health",
        "Vancouver License Renewal",
    ],
    "Travel": ["Employee Uber"],
    "Utilities": ["Disposal Fees", "FortisBC", "Shaw"],
}

SUMMARY_LABELS = {
    "total_income": "Total for Income",
    "total_product_income": "Total for Sales of Product Income",
    "total_cogs": "Total for Cost of Goods",
    "total_expenses": "Total for Expenses",
    "gross_profit": "Gross Profit",
    "profit": "Profit",
}


def parse_report(file) -> dict:
    """
    Accepts a file-like object (BytesIO or path) and returns a dict of DataFrames.

    Returned keys:
        months          - list of month column names (no 'Total')
        income_items    - DataFrame: item, [months...], Total
        total_income    - Series indexed by month + Total
        cogs_items      - DataFrame: item, [months...], Total
        total_cogs      - Series indexed by month + Total
        expense_items   - DataFrame: item, category, [months...], Total
        summary         - DataFrame: label, [months...], Total (totals + profit rows)
    """
    raw = pd.read_excel(file, header=None)

    # Find the header row: it contains "Distribution account" in the first column
    header_row_idx = raw[raw[0] == "Distribution account"].index[0]
    header = raw.iloc[header_row_idx]

    # Build month column mapping: raw col index -> month label
    # Column 0 is the label; last column is "Total"
    month_cols = {}  # {col_index: month_name}
    for col_idx in range(1, len(header)):
        val = header[col_idx]
        if pd.notna(val):
            month_cols[col_idx] = str(val)

    all_month_names = list(month_cols.values())
    # Separate the "Total" column from actual months
    months = [m for m in all_month_names if m != "Total"]
    col_order = list(month_cols.keys())  # preserves order

    # Build a label -> row Series lookup for fast access
    label_index = {}
    for idx, row in raw.iterrows():
        label = str(row[0]).strip() if pd.notna(row[0]) else ""
        if label and label not in label_index:
            label_index[label] = idx

    def extract_row(label: str) -> pd.Series:
        """Returns a Series of numeric values indexed by month name for a given label."""
        if label not in label_index:
            return pd.Series(0.0, index=all_month_names)
        row = raw.iloc[label_index[label]]
        values = {}
        for col_idx, month_name in month_cols.items():
            val = row[col_idx]
            values[month_name] = float(val) if pd.notna(val) else 0.0
        return pd.Series(values)

    def build_items_df(labels: list, extra_cols: dict = None) -> pd.DataFrame:
        """
        Builds a DataFrame with one row per label.
        extra_cols: dict of {col_name: list_of_values} to insert after 'item'.
        """
        records = []
        for label in labels:
            row_data = {"item": label}
            if extra_cols:
                for col_name, values_list in extra_cols.items():
                    row_data[col_name] = values_list[labels.index(label)]
            s = extract_row(label)
            row_data.update(s.to_dict())
            records.append(row_data)
        return pd.DataFrame(records)

    # --- Income ---
    income_df = build_items_df(INCOME_ITEM_LABELS)

    # --- COGS ---
    cogs_df = build_items_df(COGS_ITEM_LABELS)

    # --- Expense items with category column ---
    expense_labels = []
    expense_categories = []
    for category, items in EXPENSE_CATEGORIES.items():
        for item in items:
            expense_labels.append(item)
            expense_categories.append(category)

    expense_df = build_items_df(expense_labels)
    expense_df.insert(1, "category", expense_categories)

    # --- Summary rows (totals + profit) ---
    summary_records = []
    for friendly_name, label in SUMMARY_LABELS.items():
        s = extract_row(label)
        row_data = {"label": label, "key": friendly_name}
        row_data.update(s.to_dict())
        summary_records.append(row_data)
    summary_df = pd.DataFrame(summary_records)

    # Convenience: total_income and total_cogs as plain Series
    total_income_row = summary_df[summary_df["key"] == "total_income"].iloc[0]
    total_income = total_income_row[all_month_names]

    total_cogs_row = summary_df[summary_df["key"] == "total_cogs"].iloc[0]
    total_cogs = total_cogs_row[all_month_names]

    return {
        "months": months,
        "income_items": income_df,
        "total_income": total_income,
        "cogs_items": cogs_df,
        "total_cogs": total_cogs,
        "expense_items": expense_df,
        "summary": summary_df,
    }
