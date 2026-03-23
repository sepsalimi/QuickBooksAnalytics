# views/cost_of_goods.py
# Cost of Goods tab: filter by supplier, grouped bar chart, and a table that
# includes each supplier's spend as a % of total sales for each month.
# Useful for spotting which food costs are consuming the most revenue.

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render(data: dict, selected_months: list):
    cogs_df = data["cogs_items"]
    total_income = data["total_income"]
    all_suppliers = cogs_df["item"].tolist()

    st.subheader("Filters")
    col1, col2, col3 = st.columns([3, 0.5, 1])
    with col1:
        selected_suppliers = st.multiselect(
            "Suppliers",
            options=all_suppliers,
            default=all_suppliers,
            key="cogs_suppliers",
        )
    with col2:
        st.button(
            "All",
            key="cogs_select_all",
            help="Restore all suppliers",
            on_click=lambda: st.session_state.update({"cogs_suppliers": all_suppliers}),
        )
    with col3:
        spotlight = st.selectbox(
            "Spotlight (isolate one)",
            options=["All"] + (selected_suppliers or []),
            key="cogs_spotlight",
        )

    if not selected_suppliers:
        st.warning("Select at least one supplier.")
        return

    filtered = cogs_df[cogs_df["item"].isin(selected_suppliers)]

    # When a spotlight is active, chart shows only that supplier
    chart_data = (
        filtered[filtered["item"] == spotlight]
        if spotlight != "All"
        else filtered
    )

    # --- Stacked Bar Chart ---
    fig = go.Figure()
    for _, row in chart_data.iterrows():
        vals = row[selected_months].astype(float).tolist()
        fig.add_trace(
            go.Bar(
                name=row["item"],
                x=selected_months,
                y=vals,
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
        title=f"Cost of Goods by Supplier per Month{title_suffix}",
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
    st.subheader("Supplier Cost Trends")
    fig_line = go.Figure()
    for _, row in filtered.iterrows():
        vals = row[selected_months].astype(float).tolist()
        fig_line.add_trace(
            go.Scatter(
                name=row["item"],
                x=selected_months,
                y=vals,
                mode="lines+markers",
            )
        )
    fig_line.update_layout(
        title="Monthly Cost Trend by Supplier",
        xaxis_title="Month",
        yaxis_title="CAD ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- % of Total Income line chart (per supplier) ---
    income_vals = total_income[selected_months].astype(float)
    st.subheader("Each Supplier as % of Total Income")
    fig_pct = go.Figure()
    for _, row in filtered.iterrows():
        pct_line = [
            row[m] / income_vals[m] * 100 if income_vals[m] != 0 else 0
            for m in selected_months
        ]
        fig_pct.add_trace(
            go.Scatter(
                name=row["item"],
                x=selected_months,
                y=pct_line,
                mode="lines+markers",
            )
        )
    fig_pct.update_layout(
        title="Supplier Spend as % of Total Income per Month",
        xaxis_title="Month",
        yaxis_title="% of Income",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_pct, use_container_width=True)

    # --- Table with $ and % of total sales ---
    st.subheader("Cost of Goods Table")
    st.caption("% of Total Sales = supplier spend / Total Revenue that month × 100")

    # Build display: interleave $ rows and % rows per supplier
    display_rows = {}
    for _, row in filtered.iterrows():
        item = row["item"]
        vals = row[selected_months].astype(float)
        display_rows[item] = vals.apply(lambda v: f"${v:,.2f}")

        pct_vals = {}
        for m in selected_months:
            income_m = income_vals[m]
            spend_m = vals[m]
            if income_m != 0:
                pct_vals[m] = f"{spend_m / income_m * 100:.1f}%"
            else:
                pct_vals[m] = "—"
        display_rows[f"{item} (% of sales)"] = pd.Series(pct_vals)

    # Totals row
    total_spend = filtered.set_index("item")[selected_months].astype(float).sum()
    display_rows["TOTAL COGS"] = total_spend.apply(lambda v: f"${v:,.2f}")

    total_pct = {}
    for m in selected_months:
        income_m = income_vals[m]
        if income_m != 0:
            total_pct[m] = f"{total_spend[m] / income_m * 100:.1f}%"
        else:
            total_pct[m] = "—"
    display_rows["TOTAL COGS (% of sales)"] = pd.Series(total_pct)

    display_df = pd.DataFrame(display_rows).T
    display_df.columns = selected_months
    st.dataframe(display_df, use_container_width=True)

    # --- % of total sales bar chart (aggregated across selected suppliers) ---
    st.subheader("COGS as % of Total Revenue")
    col_chart, col_ma = st.columns([4, 1])
    with col_ma:
        ma_window = st.number_input(
            "MA window (months)",
            min_value=2,
            max_value=max(2, len(selected_months)),
            value=2,
            step=1,
            key="cogs_ma_window",
        )

    pct_vals_chart = []
    for m in selected_months:
        income_m = income_vals[m]
        spend_m = total_spend[m]
        pct_vals_chart.append(spend_m / income_m * 100 if income_m != 0 else 0)

    # Compute moving average
    ma_vals = pd.Series(pct_vals_chart).rolling(window=int(ma_window)).mean().tolist()

    fig2 = go.Figure()
    fig2.add_trace(
        go.Bar(
            name="COGS %",
            x=selected_months,
            y=pct_vals_chart,
            marker_color="#FF7043",
            text=[f"{v:.1f}%" for v in pct_vals_chart],
            textposition="outside",
        )
    )
    fig2.add_trace(
        go.Scatter(
            name=f"{int(ma_window)}-Month MA",
            x=selected_months,
            y=ma_vals,
            mode="lines+markers",
            line=dict(color="#1565C0", width=2, dash="dot"),
            marker=dict(size=6),
        )
    )
    fig2.update_layout(
        title="Selected COGS as % of Total Revenue per Month",
        xaxis_title="Month",
        yaxis_title="% of Revenue",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig2, use_container_width=True)
