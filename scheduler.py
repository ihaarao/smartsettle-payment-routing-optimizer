import pandas as pd

channels = {
    "Channel_F": {"fee": 5, "latency": 1, "capacity": 2},
    "Channel_S": {"fee": 1, "latency": 3, "capacity": 4},
    "Channel_B": {"fee": 0.2, "latency": 10, "capacity": 10}
}

P = 0.001


def earliest_start(channel_usage, channel, arrival):

    latency = channels[channel]["latency"]
    capacity = channels[channel]["capacity"]

    t = arrival

    while True:

        active = 0

        for start, end in channel_usage[channel]:
            if not (end <= t or start >= t + latency):
                active += 1

        if active < capacity:
            return t

        t += 1


def compute_cost(channel, start_time, tx):

    fee = channels[channel]["fee"]

    delay = start_time - tx["arrival_time"]

    penalty = P * tx["amount"] * delay

    return fee + penalty


def schedule_transactions(df):

    channel_usage = {
        "Channel_F": [],
        "Channel_S": [],
        "Channel_B": []
    }

    assignments = []

    df["deadline"] = df["arrival_time"] + df["max_delay"]

    df["urgency"] = (df["priority"] * df["amount"]) / (df["max_delay"] + 1)

    df = df.sort_values(by="urgency", ascending=False)

    for _, tx in df.iterrows():

        best_channel = None
        best_start = None
        best_score = float("inf")

        for channel in channels:

            start = earliest_start(channel_usage, channel, tx["arrival_time"])

            if start > tx["deadline"]:
                continue

            base_cost = compute_cost(channel, start, tx)

            # congestion factor encourages distribution
            current_load = len(channel_usage[channel])
            capacity = channels[channel]["capacity"]

            congestion_penalty = (current_load / capacity) * 0.05

            score = base_cost + congestion_penalty

            if score < best_score:
                best_score = score
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