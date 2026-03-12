import streamlit as st
import pandas as pd
import plotly.express as px

from optimizer import schedule_transactions, compute_total_cost, compute_tx_cost

st.set_page_config(page_title="SmartSettle Dashboard", layout="wide")

st.title("SmartSettle – Payment Routing Optimizer")

st.write("Upload a dataset to simulate optimized payment routing across settlement channels.")

uploaded_file = st.file_uploader("Upload transactions.csv", type=["csv"])

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.subheader("Input Dataset")
    st.dataframe(df)

    assignments = schedule_transactions(df.copy())

    results = pd.DataFrame(assignments)

    merged = results.merge(df, on="tx_id")

    cost = compute_total_cost(assignments, df)

    st.metric("Total System Cost", round(cost,2))

    st.subheader("Transaction Assignments")

    st.dataframe(results)

    # Channel distribution

    st.subheader("Channel Distribution")

    channel_counts = merged["channel_id"].value_counts()

    fig = px.pie(
        values=channel_counts.values,
        names=channel_counts.index,
        title="Channel Usage Distribution"
    )

    st.plotly_chart(fig, use_container_width=True)

    # Arrival vs start time

    st.subheader("Scheduling Timeline")

    fig2 = px.scatter(
        merged,
        x="arrival_time",
        y="start_time",
        color="channel_id",
        size="amount",
        title="Arrival Time vs Scheduled Start Time",
        hover_data=["amount","priority"]
    )

    st.plotly_chart(fig2, use_container_width=True)

    # Amount distribution

    st.subheader("Transaction Amount vs Channel")

    fig3 = px.box(
        merged,
        x="channel_id",
        y="amount",
        color="channel_id",
        title="Amount Distribution by Channel"
    )

    st.plotly_chart(fig3, use_container_width=True)

    # Delay analysis

    merged["delay"] = merged["start_time"] - merged["arrival_time"]

    st.subheader("Delay Distribution")

    fig4 = px.histogram(
        merged,
        x="delay",
        nbins=20,
        title="Transaction Delay Distribution"
    )

    st.plotly_chart(fig4, use_container_width=True)

    # Cost breakdown

    fees = []
    penalties = []

    for _, row in merged.iterrows():

        fee = {"Channel_F":5,"Channel_S":1,"Channel_B":0.2}[row["channel_id"]]

        delay = row["start_time"] - row["arrival_time"]

        penalty = 0.001 * row["amount"] * delay

        fees.append(fee)
        penalties.append(penalty)

    merged["fee"] = fees
    merged["penalty"] = penalties

    cost_df = pd.DataFrame({
        "Cost Type":["Channel Fees","Delay Penalties"],
        "Value":[sum(fees), sum(penalties)]
    })

    st.subheader("Cost Breakdown")

    fig5 = px.bar(
        cost_df,
        x="Cost Type",
        y="Value",
        color="Cost Type",
        title="System Cost Components"
    )

    st.plotly_chart(fig5, use_container_width=True)

    st.success("Optimization Complete")