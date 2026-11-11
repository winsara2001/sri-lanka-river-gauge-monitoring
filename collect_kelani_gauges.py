import pandas as pd
import requests
from pathlib import Path

# Set the ArcGIS query endpoint
url = (
    "https://services3.arcgis.com/J7ZFXmR8rSmQ3FGf/"
    "arcgis/rest/services/gauges_2_view/FeatureServer/0/query"
)

# Request recent readings from Kelani Ganga stations
params = {
    "where": "basin LIKE 'Kelani Ganga%'",
    "outFields": (
        "gauge,basin,water_level,rain_fall,CreationDate,"
        "alertpull,minorpull,majorpull"
    ),
    "returnGeometry": "false",
    "orderByFields": "CreationDate DESC",
    "resultRecordCount": 1000,
    "f": "json"
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()
result = response.json()

# Stop if the API returns an error
if "error" in result:
    raise RuntimeError(result["error"])

# Convert returned features into a DataFrame
records = [
    feature.get("attributes", {})
    for feature in result.get("features", [])
]
data = pd.DataFrame(records)

if data.empty:
    raise RuntimeError("No Kelani Ganga readings were returned.")

# Clean station and basin names
data["gauge"] = data["gauge"].astype("string").str.strip()
data["basin"] = data["basin"].astype("string").str.strip()

# Convert ArcGIS timestamps from milliseconds to Sri Lanka time
data["timestamp_local"] = (
    pd.to_datetime(data["CreationDate"], unit="ms", utc=True)
    .dt.tz_convert("Asia/Colombo")
)

# Add source information
data["source"] = "Irrigation Department ArcGIS gauge service"

# Keep only fields needed for the project
columns_to_keep = [
    "gauge",
    "basin",
    "timestamp_local",
    "water_level",
    "rain_fall",
    "alertpull",
    "minorpull",
    "majorpull",
    "CreationDate",
    "source"
]
data = data[columns_to_keep]

# Save the history file beside this Python script
output_file = Path(__file__).with_name("kelani_gauge_history.csv")

# Add new readings to the existing file without duplicating them
if output_file.exists():
    old_data = pd.read_csv(output_file)
    data = pd.concat([old_data, data], ignore_index=True)

data = data.drop_duplicates(
    subset=["gauge", "CreationDate"],
    keep="last"
)
data = data.sort_values(["gauge", "CreationDate"])

data.to_csv(output_file, index=False, encoding="utf-8-sig")

# Show the result
print("CSV saved to:", output_file)
print("Rows in history file:", len(data))
print("Latest readings:")
print(data.groupby("gauge").tail(1).to_string(index=False))