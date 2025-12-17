# Wyndhurst CCTV Network – Development / Workstation Tools

This repository contains the **development and workstation-side services** for the Wyndhurst CCTV Network.
It runs on a **separate server/workstation** (not the Farm PC) and provides:

* A **Streamlit dashboard** for monitoring CCTV storage, maps, timelapses, and sensors
* **Data synchronisation** from remote servers (Farm PC, Joc1 server)
* **Storage analytics and visualisations**
* **Bulk video management utilities** (transfer, cleanup, USB export)
* RTSP and recording support utilities for Hanwha cameras (**dev.biospi is not used to download any CCTV footage**)

This repo complements the on-farm CCTV ingestion and recording services.

---

## System Architecture (High Level)

```
Farm PC
 └─ Records CCTV footage (Hikvision)
 └─ Generates maps, thumbnails, metadata
 └─ Pushes frontend artefacts to Joc1 server

Joc1 Server
 └─ Central aggregation point
 └─ Records CCTV footage (Hanwha)
  └─ Pulls CCTV footage from farm PC (Hikvision)
 └─ Hosts frontend artefacts under /mnt/storage/frontend

Dev / Workstation (this repo)
 └─ Pulls frontend artefacts via SFTP
 └─ Hosts Streamlit dashboard
 └─ Performs analysis, exports, USB transfer
```

---

## Key Features

* Live **Streamlit dashboard** for CCTV network health
* Disk usage monitoring across multiple servers
* Storage growth visualisation and heatmaps
* Timelapse and latest CCTV map display
* Thumbnail browser for all cameras
* Sensor telemetry plotting (temperature, humidity, pressure, accelerometer)
* Automated frontend asset synchronisation
* Bulk MP4 filtering and export to USB storage

---

## Repository Structure

```
.
├── frontend.py                 # Streamlit dashboard
├── start_streamlit.sh          # Startup script for dashboard
├── update_front_end.py         # Pull frontend artefacts from Joc1 server
├── storage_info.py             # Storage analytics and heatmap generation
├── disk_space.py               # Disk usage data collection
├── move_to_usb.py              # Time-range based MP4 export to USB
├── transfer_to_workstation.py  # Video/data transfer utilities
├── clean.py                    # Cleanup utilities
├── delete.py                   # File deletion helpers
├── hanwha_rtsp.py              # Hanwha RTSP helpers
├── hanwha_rtsp_multi.py        # Multi-camera RTSP handling
├── start_hanwha_recording.py   # Hanwha recording trigger
├── rstp_playback.py            # RTSP playback utilities
├── report_email.py             # Email reporting
├── utils.py                    # Shared helpers and camera metadata
├── config.cfg                  # Credentials and configuration
├── requirements.txt            # Python dependencies
├── *.txt                       # Camera IPs and metadata
└── storage.png                 # Example output artefacts
```

---

## Streamlit Dashboard (`frontend.py`)

The dashboard provides a **single operational view** of the CCTV network.

### Displayed Sections

* File browser link (external service)
* Project repository links
* Disk usage overview (pie charts):

  * Joc1 server
  * Dev server
  * Farm PC
* Daily storage usage graphs
* Storage calendar image
* Latest storage snapshot
* Latest timelapse video
* Latest CCTV map image
* Thumbnail gallery for all cameras
* Camera location map
* Sensor measurements:

  * Temperature
  * Humidity
  * Pressure
  * Accelerometer (X, Y, Z)

### Data Sources

The dashboard reads pre-generated artefacts from:

```
/mnt/storage/frontend/
├── logs/disk_usage.json
├── all_videos.csv
├── daily_storage_calendar.png
├── storage.png
├── timelapse/
├── map/
├── hd/
└── sense/
```

These are produced upstream by other services and periodically synced.

---

## Running the Dashboard

### Start Script

```bash
./start_streamlit.sh
```

This:

1. Activates the virtual environment
2. Starts Streamlit on port `8501`
3. Runs `update_front_end.py` to keep assets up to date

### Manual Run

```bash
streamlit run frontend.py --server.port 8501
```

**to mount joc1 from dev.biospi (Dev workstation)**

### File browser

The dashboard provide a file browser that allows the user to navigate across all storage available

```bash
sudo sshfs fo18103@it106570.users.bris.ac.uk:/mnt /mnt/joc1 -o allow_other -o default_permissions -o umask=022
```

**to mount UoBcam from dev.biospi (Dev workstation)**
```bash
sudo sshfs uobcam@10.70.66.157:/mnt /mnt/pi -o allow_other -o default_permissions -o umask=022
```

---

## Frontend Synchronisation (`update_front_end.py`)

This script **continuously mirrors frontend artefacts** from the Joc1 server using SFTP.

* Connects via SSH using credentials in `config.cfg`
* Recursively downloads `/mnt/storage/frontend`
* Keeps the local dashboard data up to date
* Retries automatically on failure

Runs in an infinite loop with a 60-second interval.

---

## Storage Analytics (`storage_info.py`)

Generates detailed storage usage analytics from recorded MP4 files.

### Functionality

* Scans CCTV video directories
* Extracts timestamps from filenames
* Computes:

  * File size
  * Recording duration
  * Per-camera daily storage usage
* Groups by:

  * Camera
  * Location
  * Brand (Hikvision / Hanwha)
* Produces:

  * Heatmaps
  * CSV summaries
  * High-resolution PNG outputs

Used to generate artefacts consumed by the dashboard.

---

## USB Export Tool (`move_to_usb.py`)

Moves CCTV videos within a specified time window to external USB storage.

### Behaviour

* Filters MP4 files based on timestamps in filenames
* Preserves directory structure
* Uses multithreaded file moves
* Designed for large batch exports

### Example Usage

```python
main(
    input_dir=Path("/mnt/storage/cctvnet"),
    start_time_str="20250101T000000",
    end_time_str="20250430T000000",
    output_root=Path("/mnt/usb_storage/cctvnet")
)
```

---

## Configuration (`config.cfg`)

Contains credentials and connection details.

Example structure:

```ini
[SSH]
farm_server_user =
farm_server_password =
```

---

## Dependencies

* Python 3.9+
* Streamlit
* Pandas
* NumPy
* Matplotlib
* Plotly
* Paramiko
* OpenCV
* FFmpeg (system)
* ffprobe (system)

Install Python dependencies:

```bash
pip install -r requirements.txt
```

---

## Expected Environment

* Linux workstation or server
* Mounted storage under `/mnt/storage`
* Optional USB storage under `/mnt/usb_storage`
* SSH access to upstream servers

---

## Relationship to Other Repositories

* **WyndhurstFarmPC** – On-farm ingestion and recording
* **WyndhurstCCTVNet** – Core network logic
* **WyndhurstFarmFrontEnd** – GUI utility to visualise the CCTV network
* **CCTV Simulation** – Test and simulation environment

This repository focuses **only on workstation-side visualisation, analysis, and management**.

---
