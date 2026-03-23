# views/overview.py
# Overview tab: KPI metric cards + grouped bar chart of Income vs Expenses
# with a profit line overlay, filtered by the globally selected months.

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def fmt_currency(val: float) -> str:
    prefix = "-$" if val < 0 else "$"
    return f"{prefix}{abs(val):,.0f}"


def render(data: dict, selected_months: list):
    summary = data["summary"]

    def get_summary_row(key: str) -> pd.Series:
        return summary[summary["key"] == key].iloc[0]

    total_income_row = get_summary_row("total_income")
    total_expenses_row = get_summary_row("total_expenses")
    profit_row = get_summary_row("profit")
    total_cogs_row = get_summary_row("total_cogs")

    # Aggregate over selected months only
    total_income = total_income_row[selected_months].astype(float).sum()
    total_expenses = total_expenses_row[selected_months].astype(float).sum()
    net_profit = profit_row[selected_months].astype(float).sum()
    total_cogs = total_cogs_row[selected_months].astype(float).sum()

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Revenue", fmt_currency(total_income))
    col2.metric("Total Expenses", fmt_currency(total_expenses))
    col3.metric("Cost of Goods", fmt_currency(total_cogs))
    col4.metric(
        "Net Profit / Loss",
        fmt_currency(net_profit),
        delta=None,
        delta_color="normal",
    )

    st.markdown("---")

    # Monthly chart data
    income_vals = total_income_row[selected_months].astype(float).tolist()
    expense_vals = total_expenses_row[selected_months].astype(float).tolist()
    profit_vals = profit_row[selected_months].astype(float).tolist()

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Total Revenue",
            x=selected_months,
            y=income_vals,
            marker_color="#2196F3",
        )
    )
    fig.add_trace(
        go.Bar(
            name="Total Expenses",
            x=selected_months,
            y=expense_vals,
            marker_color="#FF7043",
        )
    )
    fig.add_trace(
        go.Scatter(
            name="Net Profit / Loss",
            x=selected_months,
            y=profit_vals,
            mode="lines+markers",
            line=dict(color="#4CAF50", width=2),
            marker=dict(size=7),
            yaxis="y",
        )
    )

    fig.update_layout(
        title="Monthly Revenue vs Expenses",
        barmode="group",
        xaxis_title="Month",
        yaxis_title="CAD ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=450,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary table
    st.subheader("Monthly Summary Table")
    table_rows = {
        "Total Revenue": total_income_row[selected_months].astype(float),
        "Cost of Goods": total_cogs_row[selected_months].astype(float),
        "Total Expenses": total_expenses_row[selected_months].astype(float),
        "Net Profit / Loss": profit_row[selected_months].astype(float),
    }
    table_df = pd.DataFrame(table_rows).T
    table_df.columns = selected_months
    table_df["Total"] = table_df.sum(axis=1)

    # Format as currency strings for display
    display_df = table_df.applymap(lambda v: fmt_currency(v))
    st.dataframe(display_df, use_container_width=True)
