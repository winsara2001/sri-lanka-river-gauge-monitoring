import requests
from datetime import datetime, timezone, timedelta

# Set the public ArcGIS query endpoint
url = (
    "https://services3.arcgis.com/J7ZFXmR8rSmQ3FGf/"
    "arcgis/rest/services/gauges_2_view/FeatureServer/0/query"
)

# Request recent records from the gauge service
params = {
    "where": "1=1",
    "outFields": "*",
    "returnGeometry": "false",
    "orderByFields": "CreationDate DESC",
    "resultRecordCount": 1000,
    "f": "json"
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
result = response.json()

if "error" in result:
    print("API error:", result["error"])
else:
    features = result.get("features", [])
    kelani_stations = set()
    latest_target_records = {}

    for feature in features:
        attributes = feature.get("attributes", {})
        gauge_name = str(attributes.get("gauge", "")).strip()
        basin_name = str(attributes.get("basin", "")).strip()

        if "kelani" in basin_name.casefold():
            kelani_stations.add(gauge_name)

        station_key = gauge_name.casefold()

        if (
            ("hanwella" in station_key or "pugoda" in station_key)
            and station_key not in latest_target_records
        ):
            latest_target_records[station_key] = attributes

    print("Records returned:", len(features))
    print("Kelani station names:", sorted(kelani_stations))

    if features:
        print(
            "Available field names:",
            sorted(features[0].get("attributes", {}).keys())
        )

    sri_lanka_timezone = timezone(timedelta(hours=5, minutes=30))

    for station_key, attributes in latest_target_records.items():
        timestamp = attributes.get("CreationDate")

        if timestamp is not None:
            local_time = datetime.fromtimestamp(
                timestamp / 1000,
                tz=timezone.utc
            ).astimezone(sri_lanka_timezone)
            timestamp_text = local_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            timestamp_text = None

        print({
            "station": attributes.get("gauge"),
            "basin": attributes.get("basin"),
            "water_level": attributes.get("water_level"),
            "rainfall": attributes.get("rain_fall"),
            "alert_threshold": attributes.get("alertpull"),
            "minor_flood_threshold": attributes.get("minorpull"),
            "major_flood_threshold": attributes.get("majorpull"),
            "timestamp_local": timestamp_text
        })