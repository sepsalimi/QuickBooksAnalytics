# views/cost_of_labour.py
# Cost of Labour tab: monthly bar chart, % of total income, and summary table.

import streamlit as st
import plotly.graph_objects as go
import pandas as pd


def render(data: dict, selected_months: list):
    expense_df = data["expense_items"]
    total_income = data["total_income"]

    labour_df = expense_df[expense_df["category"] == "Cost of Labour"]

    if labour_df.empty:
        st.warning("No 'Cost of Labour' data found in the uploaded report.")
        return

    labour_by_month = labour_df[selected_months].astype(float).sum()
    income_by_month = total_income[selected_months].astype(float)
    pct_by_month = (labour_by_month / income_by_month.replace(0, float("nan")) * 100).fillna(0)

    # --- KPI cards ---
    total_labour = labour_by_month.sum()
    total_income_val = income_by_month.sum()
    avg_pct = (total_labour / total_income_val * 100) if total_income_val else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Labour Cost", f"${total_labour:,.2f}")
    k2.metric("Total Income (selected months)", f"${total_income_val:,.2f}")
    k3.metric("Labour as % of Income", f"{avg_pct:.1f}%")

    # --- Bar chart with % line ---
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Cost of Labour",
            x=selected_months,
            y=labour_by_month.tolist(),
            marker_color="#EF5350",
            yaxis="y1",
        )
    )

    fig.add_trace(
        go.Scatter(
            name="% of Income",
            x=selected_months,
            y=pct_by_month.tolist(),
            mode="lines+markers+text",
            text=[f"{v:.1f}%" for v in pct_by_month],
            textposition="top center",
            line=dict(color="#FFA726", width=2),
            yaxis="y2",
        )
    )

    fig.update_layout(
        title="Cost of Labour by Month",
        xaxis_title="Month",
        yaxis=dict(title="CAD ($)"),
        yaxis2=dict(title="% of Income", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Line Trend Chart ($, per labour line item) ---
    st.subheader("Labour Cost Trends by Line Item")
    fig_line = go.Figure()
    if len(labour_df) > 1:
        for _, row in labour_df.iterrows():
            vals = row[selected_months].astype(float).tolist()
            fig_line.add_trace(
                go.Scatter(
                    name=row["item"],
                    x=selected_months,
                    y=vals,
                    mode="lines+markers",
                )
            )
    else:
        fig_line.add_trace(
            go.Scatter(
                name="Cost of Labour",
                x=selected_months,
                y=labour_by_month.tolist(),
                mode="lines+markers",
                line=dict(color="#EF5350", width=2),
            )
        )
    fig_line.update_layout(
        title="Monthly Labour Cost Trend",
        xaxis_title="Month",
        yaxis_title="CAD ($)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_line, use_container_width=True)

    # --- % of Total Income line chart (per labour line item) ---
    st.subheader("Labour Lines as % of Total Income")
    fig_pct = go.Figure()
    if len(labour_df) > 1:
        for _, row in labour_df.iterrows():
            pct_line = [
                row[m] / income_by_month[m] * 100 if income_by_month[m] != 0 else 0
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
    else:
        fig_pct.add_trace(
            go.Scatter(
                name="Cost of Labour",
                x=selected_months,
                y=pct_by_month.tolist(),
                mode="lines+markers",
                line=dict(color="#FFA726", width=2),
            )
        )
    fig_pct.update_layout(
        title="Labour Cost as % of Total Income per Month",
        xaxis_title="Month",
        yaxis_title="% of Total Income",
        yaxis=dict(ticksuffix="%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig_pct, use_container_width=True)

    # --- Table ---
    st.subheader("Cost of Labour Table")
    table_data = {
        "Month": selected_months,
        "Cost of Labour": [f"${v:,.2f}" for v in labour_by_month],
        "Total Income": [f"${v:,.2f}" for v in income_by_month],
        "% of Income": [f"{v:.1f}%" for v in pct_by_month],
    }
    table_df = pd.DataFrame(table_data).set_index("Month")

    # Totals row
    totals = pd.Series(
        {
            "Cost of Labour": f"${total_labour:,.2f}",
            "Total Income": f"${total_income_val:,.2f}",
            "% of Income": f"{avg_pct:.1f}%",
        },
        name="TOTAL",
    )
    table_df = pd.concat([table_df, totals.to_frame().T])

    st.dataframe(table_df, use_container_width=True)
