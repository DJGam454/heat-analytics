import numpy as np


# ==========================================
# TIME METRICS
# ==========================================

def calculate_elapsed_time(df):

    start_time = df.iloc[0]["time"]
    end_time = df.iloc[-1]["time"]

    elapsed_seconds = (
        end_time - start_time
    ).total_seconds()

    return elapsed_seconds


def calculate_moving_time(df):

    moving_seconds = (
        df["moving_time_diff"]
        .sum()
    )

    return moving_seconds


# ==========================================
# DISTANCE METRICS
# ==========================================

def calculate_distance(df):

    total_distance_m = (
        df["distance_diff_m"]
        .sum()
    )

    return total_distance_m / 1000


# ==========================================
# PACE METRICS
# ==========================================

def calculate_pace(
    distance_km,
    moving_time_seconds
):

    if distance_km == 0:
        return "0:00 /km"

    pace_seconds = (
        moving_time_seconds
        / distance_km
    )

    minutes = int(pace_seconds // 60)
    seconds = int(pace_seconds % 60)

    return f"{minutes}:{seconds:02d} /km"


# ==========================================
# HEART RATE METRICS
# ==========================================

def calculate_avg_hr(df):

    return int(
        df["heart_rate"]
        .dropna()
        .mean()
    )


def calculate_max_hr(df):

    return int(
        df["heart_rate"]
        .dropna()
        .max()
    )


# ==========================================
# RUN SPLITTING
# ==========================================

def split_run(df):

    midpoint = len(df) // 2

    first_half = df.iloc[:midpoint]
    second_half = df.iloc[midpoint:]

    return first_half, second_half


# ==========================================
# HR DRIFT
# ==========================================

def calculate_hr_drift(df):

    first_half, second_half = split_run(df)

    first_avg_hr = (
        first_half["heart_rate"]
        .mean()
    )

    second_avg_hr = (
        second_half["heart_rate"]
        .mean()
    )

    drift = (
        (
            second_avg_hr
            - first_avg_hr
        )
        / first_avg_hr
    ) * 100

    return round(drift, 2)


# ==========================================
# AEROBIC DECOUPLING
# ==========================================

def calculate_aerobic_decoupling(df):

    first_half, second_half = split_run(df)

    first_distance = (
        first_half["distance_diff_m"]
        .sum()
    )

    second_distance = (
        second_half["distance_diff_m"]
        .sum()
    )

    first_time = (
        first_half["moving_time_diff"]
        .sum()
    )

    second_time = (
        second_half["moving_time_diff"]
        .sum()
    )

    first_hr = (
        first_half["heart_rate"]
        .mean()
    )

    second_hr = (
        second_half["heart_rate"]
        .mean()
    )

    if first_distance == 0 or second_distance == 0:
        return 0

    first_pace_efficiency = (
        (first_time / first_distance)
        / first_hr
    )

    second_pace_efficiency = (
        (second_time / second_distance)
        / second_hr
    )

    decoupling = (
        (
            second_pace_efficiency
            - first_pace_efficiency
        )
        / first_pace_efficiency
    ) * 100

    return round(abs(decoupling), 2)


# ==========================================
# HR STABILITY
# ==========================================

def calculate_hr_stability(df):

    hr_std = np.std(
        df["heart_rate"]
        .dropna()
    )

    return round(hr_std, 2)


# ==========================================
# DRIFT ONSET
# ==========================================

def calculate_drift_onset(df):

    rolling_hr = (
        df["heart_rate"]
        .rolling(window=30)
        .mean()
    )

    rolling_hr = rolling_hr.dropna()

    if len(rolling_hr) == 0:
        return "N/A"

    baseline = rolling_hr.iloc[0]

    threshold = baseline * 1.05

    onset_indices = rolling_hr[
        rolling_hr > threshold
    ]

    if len(onset_indices) == 0:
        return "No Drift"

    onset_index = onset_indices.index[0]

    onset_time_minutes = (
        df.iloc[onset_index]["time"]
        - df.iloc[0]["time"]
    ).total_seconds() / 60

    return f"{int(onset_time_minutes)} min"
# ==========================================
# ENVIRONMENTAL AVERAGES
# ==========================================

def calculate_environmental_average(
    start_value,
    end_value
):

    return round(
        (start_value + end_value) / 2,
        2
    )


# ==========================================
# SWEAT LOSS
# ==========================================

def calculate_sweat_loss(
    pre_weight,
    post_weight,
    fluid_consumed,
    urine_output=0
):

    sweat_loss = (
        (pre_weight - post_weight)
        + fluid_consumed
        - urine_output
    )

    return round(sweat_loss, 2)


# ==========================================
# SWEAT RATE
# ==========================================

def calculate_sweat_rate(
    sweat_loss,
    moving_time_seconds
):

    moving_hours = (
        moving_time_seconds / 3600
    )

    if moving_hours == 0:
        return 0

    sweat_rate = (
        sweat_loss / moving_hours
    )

    return round(sweat_rate, 2)


# ==========================================
# BODY MASS LOSS %
# ==========================================

def calculate_body_mass_loss_percentage(
    pre_weight,
    post_weight
):

    if pre_weight == 0:
        return 0

    percentage = (
        (
            pre_weight - post_weight
        )
        / pre_weight
    ) * 100

    return round(percentage, 2)


# ==========================================
# FLUID INTAKE RATE
# ==========================================

def calculate_fluid_intake_rate(
    fluid_consumed,
    moving_time_seconds
):

    moving_hours = (
        moving_time_seconds / 3600
    )

    if moving_hours == 0:
        return 0

    rate = (
        fluid_consumed / moving_hours
    )

    return round(rate, 2)


# ==========================================
# CARB INTAKE RATE
# ==========================================

def calculate_carb_intake_rate(
    carbs_consumed,
    moving_time_seconds
):

    moving_hours = (
        moving_time_seconds / 3600
    )

    if moving_hours == 0:
        return 0

    rate = (
        carbs_consumed / moving_hours
    )

    return round(rate, 2)


# ==========================================
# SODIUM INTAKE RATE
# ==========================================

def calculate_sodium_intake_rate(
    sodium_consumed,
    moving_time_seconds
):

    moving_hours = (
        moving_time_seconds / 3600
    )

    if moving_hours == 0:
        return 0

    rate = (
        sodium_consumed / moving_hours
    )

    return round(rate, 2)