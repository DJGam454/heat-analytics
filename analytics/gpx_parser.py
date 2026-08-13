import gpxpy
import pandas as pd


def parse_gpx(uploaded_file):

    gpx = gpxpy.parse(uploaded_file)

    data = []

    for track in gpx.tracks:

        for segment in track.segments:

            for point in segment.points:

                heart_rate = None

                if point.extensions:

                    for ext in point.extensions:

                        for child in ext:

                            if "hr" in child.tag.lower():

                                try:
                                    heart_rate = int(child.text)
                                except:
                                    heart_rate = None

                data.append({
                    "time": point.time,
                    "latitude": point.latitude,
                    "longitude": point.longitude,
                    "elevation": point.elevation,
                    "heart_rate": heart_rate
                })

    df = pd.DataFrame(data)

    # Remove invalid timestamps
    df = df.dropna(subset=["time"])

    # Sort chronologically
    df = df.sort_values("time")

    # Reset index
    df = df.reset_index(drop=True)

    return df