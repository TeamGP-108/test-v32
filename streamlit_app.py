import streamlit as st
import subprocess
import threading
import time
import os

st.set_page_config(
    page_title="Weather Forecast Pro",
    page_icon="🌤️",
    layout="wide"
)

st.title("🌤️ Weather Forecast Pro")
st.write("FastAPI Weather Application")

# Start FastAPI server in background
def start_fastapi():
    subprocess.Popen(["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"])

# Start the server
if 'server_started' not in st.session_state:
    thread = threading.Thread(target=start_fastapi, daemon=True)
    thread.start()
    st.session_state.server_started = True
    time.sleep(3)  # Wait for server to start

# Embed the FastAPI app
st.components.v1.iframe("http://localhost:8000", height=800, scrolling=True)
