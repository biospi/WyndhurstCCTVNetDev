import json
import os
import re

import numpy as np
import plotly.graph_objects as go
from stl import mesh   # pip install numpy-stl

import streamlit as st
import pandas as pd
import matplotlib
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.graph_objs as go

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from pathlib import Path
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

VIDEO_BASE = Path("/mnt/storage/cctvnet")
DISK_USAGE_FILE = "/mnt/storage/frontend/logs/disk_usage.json"
ALL_VIDEO_FILE = "/mnt/storage/frontend/all_videos.csv"
CALENDAR_FILE = "/mnt/storage/frontend/daily_storage_calendar.png"
STORAGE_FILE = "/mnt/storage/frontend/storage.png"
TIMELAPSE_DIR = Path("/mnt/storage/frontend/timelapse")
MAP_DIR = Path("/mnt/storage/frontend/map")
THUMBNAIL_DIR = Path("/mnt/storage/frontend/hd")

st.set_page_config(page_title="Wyndhurst CCTV Network Dashboard", layout="wide")

count = st_autorefresh(interval=60 * 10 * 1000, limit=100, key="refresh")

# Title with subtitle
st.title("Wyndhurst CCTV Network Dashboard")
st.caption("Monitor storage usage, timelapses, and CCTV health at a glance.")
if st.button("Refresh"):
    st.rerun()

st.markdown("### File Browser")
#filebrowser -r /mnt/storage/cctvnet --address 127.0.0.1 --port 8502
# Styled link that looks like a button and opens in a new tab
st.markdown(
    """
    <a href="http://localhost:8502" target="_blank" style="text-decoration:none">
        <button style="
            background-color: #0099ff;
            color: white;
            border: none;
            padding: 0.5em 1em;
            font-size: 1em;
            border-radius: 4px;
            cursor: pointer;
        ">
            Open File Browser
        </button>
    </a>
    """,
    unsafe_allow_html=True
)

# --- GitHub Project Links ---
st.markdown("### Project Repositories")
st.markdown(
    """
    [Documentation](https://uob.sharepoint.com/:f:/r/teams/grp-bvs-johnoldacrecentre/Shared%20Documents/AI%20Group/documentation?csf=1&web=1&e=xyZzt2)  

    Here are the related GitHub repositories for this project:

    - [Wyndhurst CCTV Network](https://github.com/biospi/WyndhurstCCTVNet)  
    - [Wyndhurst Farm PC](https://github.com/biospi/WyndhurstFarmPC)  
    - [CCTV Simulation](https://github.com/biospi/WhyndhurstCCTVSimulation)  
    - [Video Downloader](https://github.com/biospi/WyndhurstVideoDownload)  
    - [BBSRC Annotation Tool](https://github.com/biospi/BBSRC_Annotation_tool)  
    """,
    unsafe_allow_html=True,
)

# --- Disk Usage Graphs ---
st.markdown("## Disk Usage Overview")

with open(DISK_USAGE_FILE) as f:
    disk_data = json.load(f)


def to_gb(size_str):
    if size_str.endswith("T"):
        return float(size_str[:-1]) * 1024
    elif size_str.endswith("G"):
        return float(size_str[:-1])
    elif size_str.endswith("M"):
        return float(size_str[:-1]) / 1024
    else:
        return float(size_str)


def parse_df_output(df_text, target_mounts=None):
    results = {}
    lines = df_text.strip().splitlines()
    for line in lines[1:]:
        parts = line.split()
        if len(parts) >= 6:
            fs, size, used, avail, percent, mount = parts[:6]
            if (target_mounts and mount in target_mounts) or (not target_mounts and mount == "/"):
                size_gb, used_gb, avail_gb = to_gb(size), to_gb(used), to_gb(avail)
                try:
                    pct = float(percent.strip("%"))
                except:
                    pct = (used_gb / size_gb * 100) if size_gb > 0 else 0
                results[mount] = {
                    "size": size_gb, "used": used_gb, "avail": avail_gb, "percent": pct
                }
    return results


# Extract disk usage
local_usage = parse_df_output(disk_data["joc1_server"], ["/mnt/storage", "/mnt/usb_storage"])
dev_usage = parse_df_output(disk_data["dev_server"], ["/mnt/storage", "/mnt/usb_storage"])
farm_usage = parse_df_output(disk_data["farm_server"])  # just "/"

def natural_key(path: Path):
    """Sort by numbers inside filename naturally (e.g. 1, 2, 10 instead of 1, 10, 2)."""
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split(r'(\d+)', path.stem)]


def gb_to_tb_str(val_gb, decimals=2):
    return f"{val_gb / 1024:.{decimals}f} TB"


def plot_pie(stats, title):
    try:
        fig, ax = plt.subplots(figsize=(2.5, 2.5))
        ax.pie(
            [stats["used"], stats["avail"]],
            labels=[f"Used {stats['percent']:.0f}%", "Free"],
            autopct="%1.0f%%",
            startangle=90,
            colors=["#ff6666", "#66b3ff"],
            textprops={'fontsize': 8}
        )
        ax.set_title(title, fontsize=10)
        st.pyplot(fig)
    except Exception as e:
        print(e)


# --- Single row with all pies ---
cols = st.columns(5)

try:
    with cols[0]:
        plot_pie(local_usage["/mnt/storage"], f"Joc1 Main Storage ({gb_to_tb_str(local_usage['/mnt/storage']['size'])})")
    with cols[1]:
        plot_pie(local_usage["/mnt/usb_storage"],
                 f"Joc1 USB Storage ({gb_to_tb_str(local_usage['/mnt/usb_storage']['size'])})")
    with cols[2]:
        plot_pie(dev_usage["/mnt/storage"], f"Dev Main Storage ({gb_to_tb_str(dev_usage['/mnt/storage']['size'])})")
    with cols[3]:
        plot_pie(dev_usage["/mnt/usb_storage"], f"Dev USB Storage ({gb_to_tb_str(dev_usage['/mnt/usb_storage']['size'])})")
    with cols[4]:
        mount, stats = next(iter(farm_usage.items()))
        plot_pie(stats, f"Farm PC ({gb_to_tb_str(farm_usage['/']['size'])})")
except Exception as e:
    print(e)

# --- Daily storage chart ---
df = pd.read_csv(ALL_VIDEO_FILE)  # or query live data
df["date"] = pd.to_datetime(df["s_dates"], format="%Y%m%dT%H%M%S")
daily = df.groupby(df["date"].dt.date)["FileSizeGB"].sum()

fig, ax = plt.subplots()
daily.plot(ax=ax, title="Daily Storage Usage (GB)")
# st.pyplot(fig)

# --- Images and videos ---
st.markdown("### Storage Calendar")
st.image(CALENDAR_FILE, caption="Calendar view of daily storage")

st.markdown("### Storage Snapshot")
st.image(STORAGE_FILE,
         caption="Latest storage snapshot")

st.markdown("### Timelapse")
timelapse_file = list(TIMELAPSE_DIR.rglob("*.mp4"))
st.video(timelapse_file[0])

st.markdown("### Last CCTV Map")
map_file = list(MAP_DIR.rglob("*.jpg"))
st.image(map_file[0], caption="Most recent frame captured")

# --- Thumbnails ---
st.markdown("### All Thumbnails")
thumbnails = sorted(THUMBNAIL_DIR.rglob("*.jpg"), key=natural_key)
full_paths = [thumb.resolve() for thumb in thumbnails]

num_cols = 10
cols = st.columns(num_cols)

for i, thumb in enumerate(thumbnails):
    col = cols[i % num_cols]
    with col:
        st.caption(f"{thumb.stem}")
        try:
            st.image(thumb, width='stretch')
        except Exception as e:
            print(e)

# --- Map view ---
st.markdown("### CCTV Location")
st.map(pd.DataFrame({"lat": [51.341726], "lon": [-2.777592]}))


# --- Sensor Dashboard ---
st.markdown("## Sensor Measurements Overview")



SENSE_DIR = Path("/mnt/storage/frontend/sense")

# Load all JSON files
json_files = sorted(SENSE_DIR.glob("measurements_*.json"))

records = []

for jf in json_files:
    with open(jf) as f:
        data = json.load(f)

    for ts, vals in data.items():
        try:
            dt = pd.to_datetime(ts, format="%d-%m-%Y %H:%M:%S")
        except:
            continue

        row = {"timestamp": dt}
        # Keep only required fields
        for k in ["temperature", "humidity", "pressure",
                  "accel_x", "accel_y", "accel_z"]:
            if k in vals:
                row[k] = vals[k]

        records.append(row)

df = pd.DataFrame(records).sort_values("timestamp")

if df.empty:
    st.warning("No sensor data found.")
    st.stop()

# -------------------------
# Colours (professional palette)
# -------------------------
temp_color = "#1f77b4"     # blue
hum_color = "#2ca02c"      # green
press_color = "#9467bd"    # purple

accel_colors = {
    "accel_x": "#ff7f0e",  # orange
    "accel_y": "#d62728",  # red
    "accel_z": "#17becf",  # cyan
}

# -------------------------
# Create a 2×2 subplot grid
# -------------------------
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Temperature (°C)",
        "Humidity (%)",
        "Pressure (hPa)",
        "Acceleration (X, Y, Z) m/s²"
    ),
    vertical_spacing=0.12,
    horizontal_spacing=0.08,
)

# -------------------------
# Temperature
# -------------------------
fig.add_trace(
    go.Scatter(
        x=df["timestamp"],
        y=df["temperature"],
        mode="lines",
        name="Temperature (°C)",
        line=dict(color=temp_color, width=2),
    ),
    row=1, col=1
)

# -------------------------
# Humidity
# -------------------------
fig.add_trace(
    go.Scatter(
        x=df["timestamp"],
        y=df["humidity"],
        mode="lines",
        name="Humidity (%)",
        line=dict(color=hum_color, width=2),
    ),
    row=1, col=2
)

# -------------------------
# Pressure
# -------------------------
fig.add_trace(
    go.Scatter(
        x=df["timestamp"],
        y=df["pressure"],
        mode="lines",
        name="Pressure (hPa)",
        line=dict(color=press_color, width=2),
    ),
    row=2, col=1
)

# -------------------------
# Accelerometer X/Y/Z (same subplot)
# -------------------------
for axis, color in accel_colors.items():
    fig.add_trace(
        go.Scatter(
            x=df["timestamp"],
            y=df[axis],
            mode="lines",
            name=f"{axis.upper()} (m/s²)",
            line=dict(color=color, width=2),
        ),
        row=2, col=2
    )

# -------------------------
# Layout
# -------------------------
fig.update_layout(
    height=900,
    showlegend=True,
    template="plotly_white",
    margin=dict(l=40, r=40, t=60, b=40),
)

# Improve axes labels
fig.update_xaxes(title_text="Time", row=1, col=1)
fig.update_xaxes(title_text="Time", row=1, col=2)
fig.update_xaxes(title_text="Time", row=2, col=1)
fig.update_xaxes(title_text="Time", row=2, col=2)

fig.update_yaxes(title_text="°C", row=1, col=1)
fig.update_yaxes(title_text="%", row=1, col=2)
fig.update_yaxes(title_text="hPa", row=2, col=1)
fig.update_yaxes(title_text="m/s²", row=2, col=2)

# -------------------------
# Streamlit Display
# -------------------------
st.plotly_chart(fig, use_container_width=True)


