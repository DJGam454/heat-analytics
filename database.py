import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy import text

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/heat_analytics"
)

engine = create_engine(DATABASE_URL)

def create_table():

    query = """
    CREATE TABLE IF NOT EXISTS heat_runs (

        id SERIAL PRIMARY KEY,

        run_date TIMESTAMP UNIQUE,

        avg_temp FLOAT,
        avg_humidity FLOAT,
        avg_wind FLOAT,

        sweat_rate FLOAT,
        sweat_loss FLOAT,

        body_mass_loss_pct FLOAT,

        hr_drift FLOAT,

        avg_hr INTEGER,

        avg_pace TEXT
    );
    """

    with engine.connect() as conn:

        conn.execute(text(query))

        conn.commit()

def insert_run_data(

    run_date,

    avg_temp,
    avg_humidity,

    sweat_rate,
    sweat_loss,

    body_mass_loss_pct,

    hr_drift,
    avg_wind,

    avg_hr,

    avg_pace
):

    query = """
    INSERT INTO heat_runs (

        run_date,

        avg_temp,
        avg_humidity,
        avg_wind,

        sweat_rate,
        sweat_loss,

        body_mass_loss_pct,

        hr_drift,

        avg_hr,

        avg_pace

    )

    VALUES (

        :run_date,

        :avg_temp,
        :avg_humidity,
        :avg_wind,

        :sweat_rate,
        :sweat_loss,

        :body_mass_loss_pct,

        :hr_drift,

        :avg_hr,

        :avg_pace
    )

    ON CONFLICT (run_date)
    DO NOTHING;
    """

    with engine.connect() as conn:

        conn.execute(
            text(query),
            {

                "run_date": run_date,

                "avg_temp": avg_temp,
                "avg_humidity": avg_humidity,
                "avg_wind": avg_wind,

                "sweat_rate": sweat_rate,
                "sweat_loss": sweat_loss,


                "body_mass_loss_pct":
                    body_mass_loss_pct,

                "hr_drift": hr_drift,

                "avg_hr": avg_hr,

                "avg_pace": avg_pace
            }
        )

        conn.commit()