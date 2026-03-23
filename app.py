# app.py
# Istanbul Doner Shop - P&L Analysis Dashboard
# Entry point for the Streamlit app. Handles file upload, month range filtering
# in the sidebar, and routes to the four analysis tabs.

import io
import streamlit as st

from parse_data import parse_report
from views import overview, income, cost_of_goods, expenses, cost_of_labour

st.set_page_config(
    page_title="Istanbul Doner Shop - P&L Analysis",
    page_icon="",
    layout="wide",
)

st.title("Istanbul Doner Shop - P&L Analysis")

# --- Sidebar ---
with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader(
        "Upload P&L Excel file (.xlsx)",
        type=["xlsx"],
        help="Drag and drop or click to upload the QuickBooks P&L by Month export.",
    )

    if uploaded_file:
        file_bytes = io.BytesIO(uploaded_file.read())
        data = parse_report(file_bytes)

        st.markdown("---")
        st.header("Month Filter")
        all_months = data["months"]
        selected_months = st.multiselect(
            "Select months to include",
            options=all_months,
            default=all_months,
            key="month_filter",
        )

        if not selected_months:
            st.warning("Select at least one month.")
            st.stop()

        st.caption(f"{len(selected_months)} of {len(all_months)} months selected")
    else:
        st.info("Upload a P&L Excel file to get started.")

# --- Main content ---
if not uploaded_file:
    st.markdown(
        """
        ### Getting Started
        Upload the QuickBooks **Profit and Loss by Month** Excel export using the
        sidebar to begin. The app supports:

        - **Overview** - monthly revenue vs expenses chart with KPI summary cards
        - **Product Income** - filter by income source (Doordash, Uber, Square, etc.)
        - **Cost of Goods** - filter by supplier with spend as % of total sales
        - **Cost of Labour** - monthly labour cost vs income with % ratio
        - **Other Expenses** - filter by expense category
        """
    )
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Overview", "Product Income", "Cost of Goods", "Cost of Labour", "Other Expenses"]
)

with tab1:
    overview.render(data, selected_months)

with tab2:
    income.render(data, selected_months)

with tab3:
    cost_of_goods.render(data, selected_months)

with tab4:
    cost_of_labour.render(data, selected_months)

with tab5:
    expenses.render(data, selected_months)
