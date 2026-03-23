# views/expenses.py
# Other Expenses tab: filter by expense category, stacked bar chart, and data table.
# COGS is excluded here since it has its own dedicated tab.

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render(data: dict, selected_months: list):
    expense_df = data["expense_items"]
    total_income = data["total_income"]
    all_categories = sorted(expense_df["category"].unique().tolist())

    all_items = sorted(expense_df["item"].tolist())

    st.subheader("Filters")
    filter_col1, filter_col2 = st.columns([1, 3])
    with filter_col1:
        group_by = st.radio(
            "View by",
            options=["Category", "Line item"],
            key="expense_group_by",
        )

    if group_by == "Category":
        with filter_col2:
            fc1, fc2 = st.columns([4, 0.5])
            with fc1:
                selected_categories = st.multiselect(
                    "Expense categories",
                    options=all_categories,
                    default=all_categories,
                    key="expense_categories",
                )
            with fc2:
                st.button(
                    "All",
                    key="expense_select_all",
                    help="Restore all categories",
                    on_click=lambda: st.session_state.update({"expense_categories": all_categories}),
                )
        if not selected_categories:
            st.warning("Select at least one category.")
            return
        filtered = expense_df[expense_df["category"].isin(selected_categories)]
        grouped = filtered.groupby("category")[selected_months].sum().astype(float)
        chart_labels = grouped.index.tolist()
        chart_data = grouped
    else:
        with filter_col2:
            fi1, fi2 = st.columns([4, 0.5])
            with fi1:
                selected_items = st.multiselect(
                    "Line items",
                    options=all_items,
                    default=all_items,
                    key="expense_items_filter",
                )
            with fi2:
                st.button(
                    "All",
                    key="expense_items_select_all",
                    help="Restore all line items",
                    on_click=lambda: st.session_state.update({"expense_items_filter": all_items}),
                )
        if not selected_items:
            st.warning("Select at least one line item.")
            return
        filtered = expense_df[expense_df["item"].isin(selected_items)]
        grouped = filtered.set_index("item")[selected_months].astype(float)
        chart_labels = grouped.index.tolist()
        chart_data = grouped

    spotlight = st.selectbox(
        "Spotlight (isolate one)",
        options=["All"] + chart_labels,
        key="expense_spotlight",
    )

    # When a spotlight is active, chart shows only that item/category
    if spotlight != "All":
        display_labels = [spotlight]
        display_data = chart_data.loc[[spotlight]]
    else:
        display_labels = chart_labels
        display_data = chart_data

    # --- Stacked Bar Chart ---
    fig = go.Figure()
    for label in display_labels:
        vals = display_data.loc[label].tolist()
        fig.add_trace(
            go.Bar(
                name=label,
                x=selected_months,
                y=vals,
            )
        )

    totals_by_month = display_data[selected_months].sum()
    y_max = totals_by_month.max() * 1.15 if totals_by_month.max() > 0 else 1

    for month, total in zip(selected_months, totals_by_month):
        fig.add_annotation(
            x=month,
            y=total,
            text=f"${total:,.0f}",
            showarrow=False,
            yshift=8,
            font=dict(size=11),
        )

    title_suffix = f" — {spotlight}" if spotlight != "All" else ""
    fig.update_layout(
        title=f"Expenses by {group_by} per Month{title_suffix}",
        barmode="stack",
        xaxis_title="Month",
        yaxis_title="CAD ($)",
        yaxis=dict(range=[0, y_max]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Line Trend Chart ($) ---
    st.subheader(f"Expense Trends by {group_by}")
    fig_line = go.Figure()
    for label in chart_labels:
        vals = chart_data.loc[label].tolist()
        fig_line.add_trace(
            go.Scatter(
                name=label,
                x=selected_months,
                y=vals,
                mode="lines+markers",
            )
        )
    fig_line.update_layout(
        title=f"Monthly Expense Trend by {group_by}",
        xaxis_title="Month",
        yaxis_title="CAD ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- % of Total Income line chart (per category/item) ---
    income_vals = total_income[selected_months].astype(float)
    st.subheader(f"Each {group_by} as % of Total Income")
    fig_pct = go.Figure()
    for label in chart_labels:
        pct_line = [
            chart_data.loc[label, m] / income_vals[m] * 100 if income_vals[m] != 0 else 0
            for m in selected_months
        ]
        fig_pct.add_trace(
            go.Scatter(
                name=label,
                x=selected_months,
                y=pct_line,
                mode="lines+markers",
            )
        )
    fig_pct.update_layout(
        title=f"Expense {group_by} as % of Total Income per Month",
        xaxis_title="Month",
        yaxis_title="% of Total Income",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_pct, use_container_width=True)

    # --- Table ---
    st.subheader("Expenses Table")

    if group_by == "Category":
        table_df = grouped.copy()
    else:
        table_df = grouped.copy()

    # Add row totals
    numeric_cols = selected_months
    table_df["Total"] = table_df[numeric_cols].sum(axis=1)

    # Totals footer row
    totals = table_df[numeric_cols + ["Total"]].sum()
    totals.name = "TOTAL"
    numeric_table = table_df[numeric_cols + ["Total"]]
    numeric_table = pd.concat([numeric_table, totals.to_frame().T])

    fmt = numeric_table.applymap(lambda v: f"${v:,.2f}")

    if group_by == "Line item":
        # Attach category column back for context
        cat_col = filtered.set_index("item")["category"].reindex(
            [i for i in numeric_table.index if i != "TOTAL"]
        )
        cat_col["TOTAL"] = ""
        fmt.insert(0, "Category", cat_col)

    st.dataframe(fmt, use_container_width=True)
