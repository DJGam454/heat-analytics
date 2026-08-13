import streamlit as st

from analytics.gpx_parser import parse_gpx
from analytics.cleaning import clean_gpx_data
from analytics.weather import get_weather_data
from database import (
    create_table,
    insert_run_data
)

from analytics.metrics import (
    calculate_elapsed_time,
    calculate_moving_time,
    calculate_distance,
    calculate_pace,
    calculate_avg_hr,
    calculate_max_hr,
    calculate_hr_drift,
    calculate_aerobic_decoupling,
    calculate_hr_stability,
    calculate_drift_onset,
    calculate_environmental_average,
    calculate_sweat_loss,
    calculate_sweat_rate,
    calculate_body_mass_loss_percentage,
    calculate_fluid_intake_rate,
    calculate_carb_intake_rate,
    calculate_sodium_intake_rate
)

# ==========================================
# PAGE CONFIG
# ==========================================

st.set_page_config(
    page_title="Heat Analytics",
    layout="wide"
)

st.title("Heat Analytics Dashboard")

create_table()

# ==========================================
# GPX UPLOAD
# ==========================================

uploaded_file = st.file_uploader(
    "Upload GPX File",
    type=["gpx"]
)

# ==========================================
# MAIN PIPELINE
# ==========================================

if uploaded_file:

    # --------------------------------------
    # RAW GPX PARSING
    # --------------------------------------

    raw_df = parse_gpx(uploaded_file)

    # --------------------------------------
    # CLEANING LAYER
    # --------------------------------------

    cleaned_df = clean_gpx_data(raw_df)

    # ======================================
    # USER INPUTS
    # ======================================

    st.sidebar.header("Hydration Inputs")

    pre_weight = st.sidebar.number_input(
        "Pre-Run Weight (kg)",
        min_value=0.0,
        step=0.1,
        value=None,
        placeholder="Optional"
    )

    post_weight = st.sidebar.number_input(
        "Post-Run Weight (kg)",
        min_value=0.0,
        step=0.1,
        value=None,
        placeholder="Optional"
    )

    fluid_consumed = st.sidebar.number_input(
        "Fluid Consumed (L)",
        min_value=0.0,
        step=0.1,
        value=None,
        placeholder="Optional"
    )

    carbs_consumed = st.sidebar.number_input(
        "Carbs Consumed (g)",
        min_value=0.0,
        step=1.0,
        value=None,
        placeholder="Optional"
    )

    sodium_consumed = st.sidebar.number_input(
        "Sodium Consumed (mg)",
        min_value=0.0,
        step=50.0,
        value=None,
        placeholder="Optional"
    )

    urine_output = st.sidebar.number_input(
        "Urine Output (L)",
        min_value=0.0,
        step=0.1,
        value=None,
        placeholder="Optional"
    )

    recovery_hr = st.sidebar.number_input(
        "Recovery HR After 1 min",
        min_value=0,
        step=1,
        value=None,
        placeholder="Optional"
    )

    rpe = st.sidebar.slider(
        "RPE",
        1,
        10,
        5
    )

    # --------------------------------------
    # OPTIONAL INPUT FIXES
    # --------------------------------------

    if urine_output is None:
        urine_output = 0

    if carbs_consumed is None:
        carbs_consumed = 0

    if sodium_consumed is None:
        sodium_consumed = 0

    # --------------------------------------
    # METADATA
    # --------------------------------------

    first_row = cleaned_df.iloc[0]
    last_row = cleaned_df.iloc[-1]

    lat = first_row["latitude"]
    lon = first_row["longitude"]

    start_time = first_row["time"]
    end_time = last_row["time"]

    run_date = start_time.strftime("%Y-%m-%d")

    start_hour = (
        start_time
        .tz_convert("Asia/Kolkata")
        .hour
    )

    end_hour = (
        end_time
        .tz_convert("Asia/Kolkata")
        .hour
    )

    # --------------------------------------
    # WEATHER
    # --------------------------------------

    start_weather = get_weather_data(
        lat,
        lon,
        run_date,
        start_hour
    )

    end_weather = get_weather_data(
        lat,
        lon,
        run_date,
        end_hour
    )

    # ======================================
    # ENVIRONMENTAL AVERAGES
    # ======================================

    weather_available = (
        start_weather is not None
        and end_weather is not None
    )

    avg_temp = avg_feels_like = None
    avg_humidity = avg_wind = None

    if weather_available:

        avg_temp = calculate_environmental_average(
            start_weather["temp_c"],
            end_weather["temp_c"]
        )

        avg_feels_like = calculate_environmental_average(
            start_weather["feelslike_c"],
            end_weather["feelslike_c"]
        )

        avg_humidity = calculate_environmental_average(
            start_weather["humidity"],
            end_weather["humidity"]
        )

        avg_wind = calculate_environmental_average(
            start_weather["wind_kph"],
            end_weather["wind_kph"]
        )

    # --------------------------------------
    # METRICS
    # --------------------------------------

    elapsed_time_seconds = calculate_elapsed_time(
        cleaned_df
    )

    moving_time_seconds = calculate_moving_time(
        cleaned_df
    )

    distance_km = calculate_distance(
        cleaned_df
    )

    avg_pace = calculate_pace(
        distance_km,
        moving_time_seconds
    )

    avg_hr = calculate_avg_hr(
        cleaned_df
    )

    max_hr = calculate_max_hr(
        cleaned_df
    )

    hr_drift = calculate_hr_drift(
        cleaned_df
    )

    aerobic_decoupling = (
        calculate_aerobic_decoupling(
            cleaned_df
        )
    )

    hr_stability = calculate_hr_stability(
        cleaned_df
    )

    drift_onset = calculate_drift_onset(
        cleaned_df
    )

    # ======================================
    # HYDRATION METRICS
    # ======================================

    hydration_data_available = all([
        pre_weight is not None,
        post_weight is not None,
        fluid_consumed is not None
    ])

    if hydration_data_available:

        sweat_loss = calculate_sweat_loss(
            pre_weight,
            post_weight,
            fluid_consumed,
            urine_output
        )

        sweat_rate = calculate_sweat_rate(
            sweat_loss,
            moving_time_seconds
        )

        body_mass_loss_percentage = (
            calculate_body_mass_loss_percentage(
                pre_weight,
                post_weight
            )
        )

        fluid_intake_rate = (
            calculate_fluid_intake_rate(
                fluid_consumed,
                moving_time_seconds
            )
        )

        carb_intake_rate = (
            calculate_carb_intake_rate(
                carbs_consumed,
                moving_time_seconds
            )
        )

        sodium_intake_rate = (
            calculate_sodium_intake_rate(
                sodium_consumed,
                moving_time_seconds
            )
        )

    # ======================================
    # WEATHER UI
    # ======================================

    if start_weather or end_weather:

        st.subheader("Run Conditions")

        w1, w2 = st.columns(2)

        with w1:

            st.markdown("### Start")

            if start_weather:

                st.metric(
                    "Temperature",
                    f"{start_weather['temp_c']} °C"
                )

                st.metric(
                    "Feels Like",
                    f"{start_weather['feelslike_c']} °C"
                )

                st.metric(
                    "Humidity",
                    f"{start_weather['humidity']} %"
                )

                st.metric(
                    "Wind",
                    f"{start_weather['wind_kph']} kph"
                )

                st.write(
                    start_weather["condition"]
                )

        with w2:

            st.markdown("### End")

            if end_weather:

                st.metric(
                    "Temperature",
                    f"{end_weather['temp_c']} °C"
                )

                st.metric(
                    "Feels Like",
                    f"{end_weather['feelslike_c']} °C"
                )

                st.metric(
                    "Humidity",
                    f"{end_weather['humidity']} %"
                )

                st.metric(
                    "Wind",
                    f"{end_weather['wind_kph']} kph"
                )

                st.write(
                    end_weather["condition"]
                )

    # ======================================
    # ENVIRONMENTAL SUMMARY
    # ======================================

    if weather_available:

        st.subheader("Environmental Summary")

        e1, e2, e3, e4 = st.columns(4)

        with e1:
            st.metric(
                "Average Temp",
                f"{avg_temp} °C"
            )

        with e2:
            st.metric(
                "Average Feels Like",
                f"{avg_feels_like} °C"
            )

        with e3:
            st.metric(
                "Average Humidity",
                f"{avg_humidity} %"
            )

        with e4:
            st.metric(
                "Average Wind",
                f"{avg_wind} kph"
            )

    # ======================================
    # CORE METRICS
    # ======================================

    st.subheader("Core Metrics")

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        st.metric(
            "Distance",
            f"{distance_km:.2f} km"
        )

    with m2:
        st.metric(
            "Average Pace",
            avg_pace
        )

    with m3:
        st.metric(
            "Average HR",
            f"{avg_hr} bpm"
        )

    with m4:
        st.metric(
            "Max HR",
            f"{max_hr} bpm"
        )

    # ======================================
    # TIME METRICS
    # ======================================

    st.subheader("Time Metrics")

    t1, t2 = st.columns(2)

    with t1:

        st.metric(
            "Elapsed Time",
            f"{elapsed_time_seconds/60:.1f} min"
        )

    with t2:

        st.metric(
            "Moving Time",
            f"{moving_time_seconds/60:.1f} min"
        )

    # ======================================
    # CARDIOVASCULAR ANALYTICS
    # ======================================

    st.subheader(
        "Cardiovascular Analytics"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "HR Drift",
            f"{hr_drift} %"
        )

    with c2:
        st.metric(
            "Aerobic Decoupling",
            f"{aerobic_decoupling} %"
        )

    with c3:
        st.metric(
            "HR Stability",
            f"{hr_stability}"
        )

    with c4:
        st.metric(
            "Drift Onset",
            drift_onset
        )

    # ======================================
    # HYDRATION ANALYTICS
    # ======================================

    if hydration_data_available:

        st.subheader("Hydration Analytics")

        h1, h2, h3 = st.columns(3)

        with h1:
            st.metric(
                "Sweat Loss",
                f"{sweat_loss:.2f} L"
            )

        with h2:
            st.metric(
                "Sweat Rate",
                f"{sweat_rate:.2f} L/hr"
            )

        with h3:
            st.metric(
                "Body Mass Loss",
                f"{body_mass_loss_percentage:.2f} %"
            )

        st.subheader("Fueling Analytics")

        f1, f2, f3 = st.columns(3)

        with f1:
            st.metric(
                "Fluid Intake Rate",
                f"{fluid_intake_rate:.2f} L/hr"
            )

        with f2:
            st.metric(
                "Carb Intake Rate",
                f"{carb_intake_rate:.2f} g/hr"
            )

        with f3:
            st.metric(
                "Sodium Intake Rate",
                f"{sodium_intake_rate:.2f} mg/hr"
            )
if uploaded_file and hydration_data_available and weather_available:
    insert_run_data(

    run_date=start_time,

    avg_temp=avg_temp,
    avg_humidity=avg_humidity,
    avg_wind=avg_wind,

    sweat_rate=sweat_rate,
    sweat_loss=sweat_loss,

    body_mass_loss_pct=body_mass_loss_percentage,

    hr_drift=hr_drift,

    avg_hr=avg_hr,

    avg_pace=avg_pace)