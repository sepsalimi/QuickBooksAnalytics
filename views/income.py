# views/income.py
# Product Income tab: filter by income source, grouped bar chart, and data table.
# "Clover Sales" covers in-store POS; the rest are delivery/online platforms.

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


# Colors assigned per income source for consistent visual identity across charts
SOURCE_COLORS = {
    "Clover Sales": "#2196F3",
    "Clover Suspense": "#90CAF9",
    "Refund": "#EF9A9A",
    "Doordash Income": "#FF7043",
    "Skip Income": "#66BB6A",
    "Square Income": "#AB47BC",
    "Uber Income": "#26C6DA",
    "Zomi Income": "#FFA726",
}


def render(data: dict, selected_months: list):
    income_df = data["income_items"]
    total_income = data["total_income"]
    all_items = income_df["item"].tolist()

    st.subheader("Filters")
    col1, col2, col3 = st.columns([3, 0.5, 1])
    with col1:
        selected_sources = st.multiselect(
            "Income sources",
            options=all_items,
            default=all_items,
            key="income_sources",
        )
    with col2:
        st.button(
            "All",
            key="income_select_all",
            help="Restore all sources",
            on_click=lambda: st.session_state.update({"income_sources": all_items}),
        )
    with col3:
        spotlight = st.selectbox(
            "Spotlight (isolate one)",
            options=["All"] + (selected_sources or []),
            key="income_spotlight",
        )

    if not selected_sources:
        st.warning("Select at least one income source.")
        return

    filtered = income_df[income_df["item"].isin(selected_sources)]

    # When a spotlight is active, chart shows only that source
    chart_data = (
        filtered[filtered["item"] == spotlight]
        if spotlight != "All"
        else filtered
    )

    # --- Stacked Bar Chart ---
    fig = go.Figure()
    for _, row in chart_data.iterrows():
        item = row["item"]
        vals = row[selected_months].astype(float).tolist()
        fig.add_trace(
            go.Bar(
                name=item,
                x=selected_months,
                y=vals,
                marker_color=SOURCE_COLORS.get(item),
            )
        )

    totals_by_month = chart_data[selected_months].astype(float).sum()
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
        title=f"Product Income by Month{title_suffix}",
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
    st.subheader("Income Source Trends")
    fig_line = go.Figure()
    for _, row in filtered.iterrows():
        item = row["item"]
        vals = row[selected_months].astype(float).tolist()
        fig_line.add_trace(
            go.Scatter(
                name=item,
                x=selected_months,
                y=vals,
                mode="lines+markers",
                line=dict(color=SOURCE_COLORS.get(item)),
            )
        )
    fig_line.update_layout(
        title="Monthly Income Trend by Source",
        xaxis_title="Month",
        yaxis_title="CAD ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- % of Total Income line chart (per source) ---
    income_vals = total_income[selected_months].astype(float)
    st.subheader("Each Source as % of Total Income")
    fig_pct = go.Figure()
    for _, row in filtered.iterrows():
        item = row["item"]
        pct_line = [
            row[m] / income_vals[m] * 100 if income_vals[m] != 0 else 0
            for m in selected_months
        ]
        fig_pct.add_trace(
            go.Scatter(
                name=item,
                x=selected_months,
                y=pct_line,
                mode="lines+markers",
                line=dict(color=SOURCE_COLORS.get(item)),
            )
        )
    fig_pct.update_layout(
        title="Income Source as % of Total Revenue per Month",
        xaxis_title="Month",
        yaxis_title="% of Total Income",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_pct, use_container_width=True)

    # --- Table ---
    st.subheader("Income Table")
    table_df = filtered.set_index("item")[selected_months].astype(float).copy()
    table_df["Total"] = table_df.sum(axis=1)

    # Totals row
    totals = table_df.sum()
    totals.name = "TOTAL"
    table_df = pd.concat([table_df, totals.to_frame().T])

    fmt = table_df.applymap(lambda v: f"${v:,.2f}")
    st.dataframe(fmt, use_container_width=True)
