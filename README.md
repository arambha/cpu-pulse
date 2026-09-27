# CPU Pulse

A local Streamlit CPU performance dashboard with live utilization, per-core charts, frequency, RAM usage, uptime, pause/resume, and CSV export.

## Run on Windows

Double-click `run.bat`. The first launch creates a local virtual environment and installs dependencies; this needs internet access. Your browser opens automatically.

Or run manually from this directory:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m streamlit run app.py --server.address 127.0.0.1
```

Keep the terminal open. Press Ctrl+C to stop the server.

The app monitors the machine running Python, so hosting it remotely measures that server instead of your PC. Each refresh measures utilization over 100 milliseconds; bursts between samples may not appear. Frequency availability depends on the operating system. History is kept in memory for this browser session (up to 15 minutes at the fastest refresh). Pause freezes the displayed sample; resuming continues collection.

Live refresh uses Streamlit's fragment API: https://docs.streamlit.io/develop/api-reference/execution-flow/st.fragment
