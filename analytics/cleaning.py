from geopy.distance import geodesic
import pandas as pd


def clean_gpx_data(df):

    df = df.copy()

    # ==========================================
    # TIME DIFFERENCES
    # ==========================================

    df["time_diff"] = (
        df["time"]
        .diff()
        .dt.total_seconds()
    )

    # First row fix
    df.loc[0, "time_diff"] = 0

    # ==========================================
    # DISTANCE CALCULATIONS
    # ==========================================

    distances = [0]

    for i in range(1, len(df)):

        prev_point = (
            df.iloc[i - 1]["latitude"],
            df.iloc[i - 1]["longitude"]
        )

        current_point = (
            df.iloc[i]["latitude"],
            df.iloc[i]["longitude"]
        )

        distance = geodesic(
            prev_point,
            current_point
        ).meters

        distances.append(distance)

    df["distance_diff_m"] = distances

    # ==========================================
    # CUMULATIVE DISTANCE
    # ==========================================

    df["cumulative_distance_m"] = (
        df["distance_diff_m"]
        .cumsum()
    )

    # ==========================================
    # SPEED CALCULATIONS
    # ==========================================

    df["speed_mps"] = (
        df["distance_diff_m"]
        / df["time_diff"]
    )

    # Replace invalid values
    df["speed_mps"] = (
        df["speed_mps"]
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0)
    )

    # Convert to km/h
    df["speed_kph"] = df["speed_mps"] * 3.6

    # ==========================================
    # GPS JITTER FILTER
    # ==========================================

    # Remove impossible spikes
    df.loc[
        df["speed_kph"] > 30,
        "speed_kph"
    ] = 0

    # ==========================================
    # MOVING DETECTION
    # ==========================================

    # Threshold:
    # below 1 kph = stationary
    df["is_moving"] = df["speed_kph"] > 1

    # ==========================================
    # MOVING TIME
    # ==========================================

    df["moving_time_diff"] = df.apply(
        lambda row:
            row["time_diff"]
            if row["is_moving"]
            else 0,
        axis=1
    )

    return df

# speed_kph > 30
# is a temporary spike filter.

# Later:

# trail running,
# cycling support,
# sprint work

# may require dynamic thresholds.

# But for now:
# this is a very reasonable running-specific cleaner.