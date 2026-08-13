# Heat Analytics

A Streamlit dashboard that turns a GPX run file into a full heat-and-hydration analysis: sweat rate, sweat loss, heart-rate drift, aerobic decoupling, and fueling rates, all cross-referenced against the weather conditions of the run.

![Dashboard](docs/screenshot-dashboard-full.png)

## What it does

Upload a GPX activity (GPS track + heart rate data). The app:

1. **Parses** the GPX into a time series of position, elevation and heart rate
2. **Cleans** the data - removes GPS spikes, detects moving vs stationary time
3. **Pulls weather** (temperature, humidity, wind, feels-like) for the run's date and location
4. **Computes** performance metrics from the GPS/HR data
5. **Computes** hydration and fueling metrics from your pre/post run weights and intake
6. **Stores** every analysed run in PostgreSQL for a growing personal heat-stress dataset

## Why it matters (heat stress in a warming climate)

Heat is the deadliest weather-related hazard in the world, and climate change is making hot days hotter, longer and more frequent. For anyone who runs, cycles or works outdoors, heat stress is not a niche concern:

- As air temperature and humidity rise, sweat rate rises with them. In hot and humid conditions a runner can lose **1 to 3 litres of sweat per hour**.
- Losing just **2% of body mass** through sweat measurably impairs endurance performance (ACSM guidance) and increases heart-rate drift.
- **Cardiac drift** - heart rate climbing while pace stays constant - is one of the earliest, most visible signs of heat strain. This app quantifies it.
- Replacing sweat with plain water alone can cause **hyponatremia** (dangerously low blood sodium). Tracking sodium intake rate matters just as much as tracking water.
- Personalising hydration from your *actual* measured sweat rate is the difference between guessing and knowing.

This tool is a small, practical adaptation to a hotter world: it converts a single run file into the numbers an athlete needs to hydrate safely under heat stress.

## Screenshot (metrics view)

![Core, time and cardiovascular metrics](docs/screenshot-dashboard-viewport.png)

## Metrics and formulas

All formulas live in `analytics/metrics.py` and are unit-tested against real GPX data.

### Core run metrics

| Metric | Formula | Notes |
|---|---|---|
| Distance | Sum of `geodesic(lat,lon)` between consecutive GPS points | WGS84 ellipsoid distance via `geopy`, reported in km |
| Elapsed time | `last_timestamp - first_timestamp` | Wall-clock duration |
| Moving time | Sum of `time_diff` where speed > 1 km/h | Points below 1 km/h count as stationary |
| Pace | `moving_time / distance` | Reported as `mm:ss /km` |

### Cardiovascular metrics

| Metric | Formula | What it reveals |
|---|---|---|
| Average HR | Mean of all heart-rate samples | Overall effort |
| Max HR | Max of all heart-rate samples | Peak intensity |
| HR drift | `(avg_HR_2nd_half - avg_HR_1st_half) / avg_HR_1st_half * 100` | Cardiac drift. Above ~10% indicates heat strain or dehydration |
| Aerobic decoupling | `(pace_efficiency_2nd_half - pace_efficiency_1st_half) / pace_efficiency_1st_half * 100`, where `pace_efficiency = (time / distance) / avg_HR` | "Fitness-metabolism" coupling; low values mean a stable, efficient run |
| HR stability | Standard deviation of heart rate | Low = steady effort, high = surges/heat impact |
| Drift onset | First minute where the 30-sample rolling HR mean exceeds the baseline by 5% | When the heat started to take its toll |

### Hydration metrics (the core of the app)

| Metric | Formula | Notes |
|---|---|---|
| **Sweat loss** | `(pre_weight - post_weight) + fluid_consumed - urine_output` | Litres of sweat lost during the run |
| **Sweat rate** | `sweat_loss / moving_time_hours` | L/hr. The number hydration plans are built around |
| Body mass loss % | `(pre_weight - post_weight) / pre_weight * 100` | Above ~2% is where performance drops |
| Fluid intake rate | `fluid_consumed / moving_time_hours` | L/hr actually replaced |
| Carb intake rate | `carbs_consumed / moving_time_hours` | g/hr. Reference range ~30-60 g/hr for endurance |
| Sodium intake rate | `sodium_consumed / moving_time_hours` | mg/hr. Guards against hyponatremia |

### Environmental metrics

Temperature, humidity, wind and feels-like for the start and end of the run, averaged:
`(start_value + end_value) / 2`. Weather comes from the [WeatherAPI](https://www.weatherapi.com) history endpoint, using the run's start latitude/longitude, date and start hour.

## Project structure

```
heat-analytics/
├── app.py                    # Streamlit dashboard
├── database.py               # PostgreSQL persistence (heat_runs table)
├── main.py                   # CLI entry point
├── analytics/
│   ├── gpx_parser.py         # GPX -> DataFrame (position, elevation, HR)
│   ├── cleaning.py           # Geodesic distance, speed, moving-time detection
│   ├── metrics.py            # Every formula above
│   └── weather.py            # WeatherAPI history client
└── docs/                     # Screenshots
```

The `heat_runs` table stores one row per run: run date (unique), average temperature/humidity/wind, sweat rate, sweat loss, body mass loss %, HR drift, average HR and average pace - a ready-made dataset for personal heat-stress analysis over time.

## Setup

Requires Python 3.12+ and PostgreSQL (local or remote).

```bash
pip install -r pyproject.toml   # or: uv sync
cp .env.example .env            # then fill in your keys
streamlit run app.py
```

Environment variables (see `.env.example`):

| Variable | Purpose |
|---|---|
| `WEATHER_API_KEY` | WeatherAPI key. Note: the *history* endpoint needs a paid plan; the app degrades gracefully and skips weather sections when unavailable |
| `DATABASE_URL` | `postgresql://user:password@host:5432/heat_analytics` |

The database schema is created automatically on app start.

## Example output

Analysing a 10.09 km sample run (73 min moving time):

| Metric | Value |
|---|---|
| Average pace | 7:14 /km |
| Average / max HR | 147 / 178 bpm |
| HR drift | 7.06 % |
| Aerobic decoupling | 6.45 % |
| Sweat loss | 1.40 L |
| Sweat rate | 1.15 L/hr |
| Body mass loss | 1.14 % |
| Fluid / carb / sodium intake rates | 0.66 L/hr, 24.65 g/hr, 328.62 mg/hr |

## Known limitations

- GPS spike filter and the 1 km/h moving threshold are running-specific (a future cycling or trail-running mode would need dynamic thresholds)
- Weather history requires a paid WeatherAPI plan; without it, the app runs but omits the weather sections
- `calculate_drift_onset` returns `"No Drift"` when HR never crosses the 5% threshold

## License

MIT
