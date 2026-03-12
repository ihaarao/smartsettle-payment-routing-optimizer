import pandas as pd
import json

# Channel configuration
channels = {
    "Channel_F": {"fee": 5, "latency": 1, "capacity": 2},
    "Channel_S": {"fee": 1, "latency": 3, "capacity": 4},
    "Channel_B": {"fee": 0.2, "latency": 10, "capacity": 10}
}

# Active usage tracking
channel_usage = {
    "Channel_F": [],
    "Channel_S": [],
    "Channel_B": []
}

P = 0.001
F = 0.5


def earliest_start(channel, arrival):
    usage = channel_usage[channel]
    capacity = channels[channel]["capacity"]
    t = arrival

    while True:
        active = [u for u in usage if not (u[1] <= t or u[0] > t)]

        if len(active) < capacity:
            return t

        t += 1


def compute_tx_cost(channel, start_time, tx):
    fee = channels[channel]["fee"]
    delay = start_time - tx["arrival_time"]
    penalty = P * tx["amount"] * delay
    return fee + penalty


def schedule_transactions(df):

    assignments = []

    # Deadline
    df["deadline"] = df["arrival_time"] + df["max_delay"]

    # Urgency score
    df["urgency"] = (df["priority"] * df["amount"]) / (df["max_delay"] + 1)

    # Sort by urgency
    df = df.sort_values(by="urgency", ascending=False)

    for _, tx in df.iterrows():

        best_channel = None
        best_start = None
        best_cost = float("inf")

        for channel in channels:

            start = earliest_start(channel, tx["arrival_time"])

            if start > tx["deadline"]:
                continue

            cost = compute_tx_cost(channel, start, tx)

            if cost < best_cost:
                best_cost = cost
                best_channel = channel
                best_start = start

        if best_channel:

            latency = channels[best_channel]["latency"]

            channel_usage[best_channel].append(
                (best_start, best_start + latency)
            )

            assignments.append({
                "tx_id": tx["tx_id"],
                "channel_id": best_channel,
                "start_time": int(best_start)
            })

        else:

            assignments.append({
                "tx_id": tx["tx_id"],
                "channel_id": None,
                "start_time": None,
                "failed": True
            })

    return assignments


def compute_total_cost(assignments, df):

    total_cost = 0

    for a in assignments:

        tx = df[df.tx_id == a["tx_id"]].iloc[0]

        if "failed" in a:
            total_cost += F * tx["amount"]
            continue

        delay = a["start_time"] - tx["arrival_time"]
        fee = channels[a["channel_id"]]["fee"]
        penalty = P * tx["amount"] * delay

        total_cost += fee + penalty

    return total_cost


def main():

    df = pd.read_csv("transactions.csv")

    assignments = schedule_transactions(df)

    cost = compute_total_cost(assignments, df)

    cost = round(cost, 2)

    output = {
        "assignments": assignments,
        "total_system_cost_estimate": cost
    }

    with open("submission.json", "w") as f:
        json.dump(output, f, indent=4)

    print("Submission generated!")
    print("Total system cost:", cost)


if __name__ == "__main__":
    main()