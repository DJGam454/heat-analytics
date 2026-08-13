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

![Hydration, fueling and cardiovascular analytics](docs/screenshot-dashboard-hydration.png)

The dashboard below the core metrics: HR drift, aerobic decoupling, sweat loss, sweat rate, body mass loss, and fluid, carb and sodium intake rates.

## Metrics and formulas

All formulas below are implemented in `analytics/metrics.py` and validated against real GPX data.

### Notation

| Symbol | Definition |
|---|---|
| $p_i = (\varphi_i, \lambda_i)$ | GPS fix at sample $i$ (latitude, longitude) |
| $t_i$ | Timestamp of sample $i$ [s] |
| $\Delta t_i = t_i - t_{i-1}$ | Inter-sample time interval [s] |
| $v_i$ | Ground speed at sample $i$ [km/h] |
| $HR_i$ | Heart rate at sample $i$ [bpm] |
| $n$ | Number of GPS samples |
| $W_{\text{pre}}, W_{\text{post}}$ | Body mass before and after the run [kg] |
| $V_{\text{fluid}}, V_{\text{urine}}$ | Fluid consumed, urine output during the run [L] |
| $c_{\text{carb}}, m_{\text{Na}}$ | Carbohydrate [g] and sodium [mg] consumed |

### Core run metrics

**Elapsed time** - wall-clock duration from first to last fix:

$$T_{\text{elapsed}} = t_n - t_1$$

**Moving time** - time spent above the movement threshold $v_{\text{thr}} = 1$ km/h, using the indicator function $\mathbb{1}[\cdot]$:

$$T_{\text{moving}} = \sum_{i=2}^{n} \Delta t_i \cdot \mathbf{1}\big[v_i > v_{\text{thr}}\big]$$

**Distance** - cumulative geodesic distance over consecutive fixes, computed on the WGS84 reference ellipsoid (via `geopy` `geodesic`):

$$D = \sum_{i=2}^{n} d_g(p_{i-1},\, p_i)$$

**Pace** - moving time normalised by distance:

$$P = \frac{T_{\text{moving}}}{D} \quad \left[\frac{\text{min}}{\text{km}}\right]$$

### Cardiovascular metrics

Mean and peak heart rate over the $N$ samples with valid readings:

$$\overline{HR} = \frac{1}{N} \sum_{i=1}^{N} HR_i, \qquad HR_{\max} = \max_{i} HR_i$$

All drift metrics split the run into two halves at the sample midpoint $m = \lfloor n/2 \rfloor$, with $\mathcal{H}_1 = \{1,\dots,m\}$ and $\mathcal{H}_2 = \{m+1,\dots,n\}$.

**Heart-rate drift** - relative change in mean heart rate between the two halves. Values above ~10% are classically associated with heat strain, dehydration, and cardiac drift:

$$\mathrm{HRD} = \frac{\overline{HR}_{\mathcal{H}_2} - \overline{HR}_{\mathcal{H}_1}}{\overline{HR}_{\mathcal{H}_1}} \times 100\%$$

**Aerobic decoupling** - drift in pace efficiency $E$ (time per unit distance per unit heart rate), i.e. whether the run becomes metabolically less efficient over time:

$$E = \frac{T_{\text{moving}} / D}{\overline{HR}}, \qquad
\mathrm{AD} = \left| \frac{E_{\mathcal{H}_2} - E_{\mathcal{H}_1}}{E_{\mathcal{H}_1}} \right| \times 100\%$$

**HR stability** - sample standard deviation of heart rate; low values indicate a steady, well-managed effort:

$$\sigma_{HR} = \sqrt{\frac{1}{N-1} \sum_{i=1}^{N} \left( HR_i - \overline{HR} \right)^2}$$

**Drift onset** - first time at which the 30-sample rolling mean of heart rate exceeds the baseline by 5%, reported in minutes from the start:

$$\mu_{30}(k) = \frac{1}{30} \sum_{j = k-29}^{k} HR_j, \qquad t_{\text{onset}} = \min\left\lbrace k : \mu_{30}(k) > 1.05 \cdot \mu_{30}(1) \right\rbrace$$

### Hydration metrics (the core of the app)

**Sweat loss** - whole-body mass balance: pre-run body mass plus what was taken in, minus what was excreted:

$$V_{\text{sweat}} = \left( W_{\text{pre}} - W_{\text{post}} \right) + V_{\text{fluid}} - V_{\text{urine}}$$

**Sweat rate** - sweat loss normalised by moving time (the figure hydration plans are built around):

$$\dot{V}_{\text{sweat}} = \frac{V_{\text{sweat}}}{T_{\text{moving}}} \quad \left[\frac{\text{L}}{\text{hr}}\right]$$

**Body mass loss percentage** - relative dehydration. Losing more than ~2% measurably impairs endurance performance (ACSM guidance):

$$\%\mathrm{BML} = \frac{W_{\text{pre}} - W_{\text{post}}}{W_{\text{pre}}} \times 100\%$$

**Fueling rates** - intake normalised by moving time, compared against the ~30-60 g/hr carbohydrate reference range for endurance events:

$$\dot{V}_{\text{fluid}} = \frac{V_{\text{fluid}}}{T_{\text{moving}}}, \qquad
\dot{c}_{\text{carb}} = \frac{c_{\text{carb}}}{T_{\text{moving}}}, \qquad
\dot{m}_{\text{Na}} = \frac{m_{\text{Na}}}{T_{\text{moving}}}$$

### Environmental metrics

Weather is fetched for the start and end hours of the run; each environmental variable $x$ is reported as the mean of the two observations, $x \in \{T, T_{\text{feels-like}}, \mathrm{RH}, v_{\text{wind}}\}$:

$$\bar{x} = \frac{x_{\text{start}} + x_{\text{end}}}{2}$$

Weather comes from the [WeatherAPI](https://www.weatherapi.com) history endpoint, using the run's start latitude/longitude, date and start hour.

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
