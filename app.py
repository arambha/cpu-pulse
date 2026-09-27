from collections import deque
from datetime import datetime, timedelta
import platform
import time

import altair as alt
import pandas as pd
import psutil
import streamlit as st

st.set_page_config(page_title="CPU Pulse", page_icon="⚡", layout="wide")
st.markdown("""<style>
.stApp {background: #0b1120;}
[data-testid="stMetric"] {background:#151f32; padding:20px; border:1px solid #26344d; border-radius:14px;}
.block-container {padding-top:2rem;}
</style>""", unsafe_allow_html=True)
st.title("⚡ CPU Pulse")
st.caption("Live performance • " + platform.node())

with st.sidebar:
    st.header("Monitor controls")
    live = st.toggle("Live updates", value=True)
    refresh = st.select_slider("Refresh interval (seconds)", options=[0.5, 1, 2, 3, 5], value=1)
    window = st.selectbox("History window", [1, 5, 15], index=1, format_func=lambda x: f"{x} minutes")
    if st.button("Clear history", width="stretch"):
        st.session_state.pop("samples", None)
    st.divider()
    st.caption("This dashboard measures the computer running Streamlit. Keep it running locally to monitor your PC.")
    st.text(f"{platform.system()} {platform.release()}")
    st.caption(platform.processor() or "CPU model unavailable")

if "samples" not in st.session_state:
    st.session_state.samples = deque(maxlen=1801)


def read_sample():
    # A short explicit interval gives a valid first reading and avoids relying
    # on psutil's thread-local baseline across Streamlit reruns.
    cores = psutil.cpu_percent(interval=0.1, percpu=True)
    memory = psutil.virtual_memory()
    try:
        frequency = psutil.cpu_freq()
    except (OSError, NotImplementedError):
        frequency = None
    return {
        "Time": datetime.now(),
        "CPU usage": sum(cores) / len(cores) if cores else 0.0,
        "cores": cores,
        "RAM usage": memory.percent,
        "ram_used": memory.used / 1024**3,
        "ram_total": memory.total / 1024**3,
        "frequency": frequency.current if frequency else None,
    }


@st.fragment(run_every=refresh if live else None)
def dashboard():
    samples = st.session_state.samples
    if live or not samples:
        samples.append(read_sample())
    latest = samples[-1]
    cutoff = latest["Time"] - timedelta(minutes=window)
    visible = [sample for sample in samples if sample["Time"] >= cutoff]

    st.caption(f"{'🟢 LIVE' if live else '⏸ PAUSED'}  ·  Last sample {latest['Time']:%H:%M:%S}  ·  100 ms sampling window")
    cols = st.columns(4)
    cols[0].metric("CPU utilization", f"{latest['CPU usage']:.1f}%")
    cols[1].metric("Window peak", f"{max(s['CPU usage'] for s in visible):.1f}%")
    cols[2].metric("CPU frequency", f"{latest['frequency'] / 1000:.2f} GHz" if latest['frequency'] else "Unavailable")
    cols[3].metric("Memory", f"{latest['RAM usage']:.1f}%", help=f"{latest['ram_used']:.1f} / {latest['ram_total']:.1f} GB")

    st.subheader("CPU usage over time")
    history = pd.DataFrame([{ "Time": s["Time"], "CPU usage": s["CPU usage"]} for s in visible])
    st.altair_chart(alt.Chart(history).mark_line(color="#38bdf8", point=True).encode(
        x=alt.X("Time:T", title="Time"),
        y=alt.Y("CPU usage:Q", title="CPU usage (%)", scale=alt.Scale(domain=[0, 100])),
        tooltip=["Time:T", "CPU usage:Q"],
    ).properties(height=280), width="stretch")

    st.subheader("Logical processor activity")
    cores = latest["cores"]
    core_frame = pd.DataFrame({"Processor": [f"CPU {i:02d}" for i in range(len(cores))], "Usage (%)": cores})
    st.altair_chart(alt.Chart(core_frame).mark_bar(color="#2dd4bf").encode(
        x=alt.X("Processor:N", sort=None),
        y=alt.Y("Usage (%):Q", scale=alt.Scale(domain=[0, 100])),
        tooltip=["Processor:N", "Usage (%):Q"],
    ).properties(height=250), width="stretch")
    with st.expander("Per-core history and readings"):
        core_history = pd.DataFrame([
            {"Time": s["Time"], **{f"CPU {i:02d}": value for i, value in enumerate(s["cores"])}}
            for s in visible
        ])
        core_history = core_history.melt("Time", var_name="Processor", value_name="Usage (%)")
        st.altair_chart(alt.Chart(core_history).mark_line(point=True).encode(
            x="Time:T",
            y=alt.Y("Usage (%):Q", scale=alt.Scale(domain=[0, 100])),
            color="Processor:N",
            tooltip=["Time:T", "Processor:N", "Usage (%):Q"],
        ).properties(height=250), width="stretch")
        st.dataframe(core_frame, hide_index=True, width="stretch")

    a, b, c = st.columns(3)
    a.metric("Physical cores", psutil.cpu_count(logical=False) or "Unavailable")
    b.metric("Logical processors", psutil.cpu_count() or len(cores))
    uptime = int(time.time() - psutil.boot_time())
    c.metric("System uptime", f"{uptime // 86400}d {(uptime % 86400) // 3600}h {(uptime % 3600) // 60}m")
    export = pd.DataFrame([
        {"Time": s["Time"], "CPU (%)": s["CPU usage"], "RAM (%)": s["RAM usage"],
         **{f"CPU {i:02d} (%)": value for i, value in enumerate(s["cores"])}}
        for s in visible
    ])
    st.download_button("Download visible history (CSV)", export.to_csv(index=False), "cpu-history.csv", "text/csv")


dashboard()

