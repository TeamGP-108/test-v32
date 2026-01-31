import streamlit as st
import requests
import json
from datetime import datetime
import time

# Configuration
WEATHER_API_KEY = "bd5e378503939ddaee76f12ad7a97608"

# Set page config
st.set_page_config(
    page_title="Weather Forecast",
    page_icon="🌤️",
    layout="wide"
)

# Title
st.title("🌤️ Weather Forecast Pro")
st.markdown("Real-time weather data from WeatherAPI.com")

# Initialize session state
if 'location' not in st.session_state:
    st.session_state.location = "London"
if 'favorites' not in st.session_state:
    st.session_state.favorites = ["London", "New York", "Tokyo", "Paris"]

# Sidebar for search and favorites
with st.sidebar:
    st.header("🔍 Search")
    
    # Search input
    new_location = st.text_input("Enter city name:", value=st.session_state.location)
    if st.button("Get Weather"):
        st.session_state.location = new_location
        st.rerun()
    
    st.header("⭐ Favorites")
    for fav in st.session_state.favorites:
        if st.button(f"📍 {fav}", key=f"fav_{fav}"):
            st.session_state.location = fav
            st.rerun()
    
    # Add current to favorites
    if st.button("➕ Add to Favorites"):
        if st.session_state.location not in st.session_state.favorites:
            st.session_state.favorites.append(st.session_state.location)
            st.success(f"Added {st.session_state.location} to favorites!")

# Main content
def get_weather_data(location):
    """Fetch weather data from WeatherAPI"""
    try:
        # Current weather
        current_url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}&aqi=no"
        current_response = requests.get(current_url, timeout=10)
        current_data = current_response.json()
        
        # Forecast
        forecast_url = f"http://api.weatherapi.com/v1/forecast.json?key={WEATHER_API_KEY}&q={location}&days=3&aqi=no&alerts=no"
        forecast_response = requests.get(forecast_url, timeout=10)
        forecast_data = forecast_response.json()
        
        return {
            "current": current_data,
            "forecast": forecast_data
        }
    except Exception as e:
        st.error(f"Error fetching data: {str(e)}")
        return None

# Get weather data
weather_data = get_weather_data(st.session_state.location)

if weather_data:
    # Current weather
    current = weather_data["current"]
    location = current["location"]
    current_weather = current["current"]
    
    # Display current weather
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Location", f"{location['name']}, {location['country']}")
        st.write(f"Local Time: {location['localtime']}")
    
    with col2:
        st.metric("Temperature", f"{current_weather['temp_c']}°C")
        st.write(f"Feels like: {current_weather['feelslike_c']}°C")
    
    with col3:
        st.metric("Condition", current_weather["condition"]["text"])
        st.write(f"Humidity: {current_weather['humidity']}%")
    
    # Weather details in columns
    st.subheader("📊 Weather Details")
    cols = st.columns(4)
    
    details = [
        ("Wind Speed", f"{current_weather['wind_kph']} km/h"),
        ("Wind Direction", current_weather['wind_dir']),
        ("Pressure", f"{current_weather['pressure_mb']} hPa"),
        ("Precipitation", f"{current_weather['precip_mm']} mm"),
        ("Visibility", f"{current_weather['vis_km']} km"),
        ("UV Index", current_weather['uv']),
        ("Cloud Cover", f"{current_weather['cloud']}%"),
        ("Gust", f"{current_weather['gust_kph']} km/h")
    ]
    
    for idx, (label, value) in enumerate(details):
        with cols[idx % 4]:
            st.metric(label, value)
    
    # 3-Day Forecast
    st.subheader("📅 3-Day Forecast")
    forecast_days = weather_data["forecast"]["forecast"]["forecastday"]
    
    forecast_cols = st.columns(3)
    for idx, day in enumerate(forecast_days):
        with forecast_cols[idx]:
            date = datetime.strptime(day['date'], "%Y-%m-%d").strftime("%A, %b %d")
            st.write(f"**{date}**")
            st.write(f"🌡️ Max: {day['day']['maxtemp_c']}°C")
            st.write(f"🌡️ Min: {day['day']['mintemp_c']}°C")
            st.write(f"🌧️ Rain: {day['day']['totalprecip_mm']}mm")
            st.write(f"💧 Humidity: {day['day']['avghumidity']}%")
            st.write(f"🌅 Sunrise: {day['astro']['sunrise']}")
            st.write(f"🌇 Sunset: {day['astro']['sunset']}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center;'>
        <p>Powered by <a href='https://www.weatherapi.com/' target='_blank'>WeatherAPI.com</a></p>
        <p style='font-size: 0.8rem; color: #666;'>Data updates in real-time</p>
    </div>
    """,
    unsafe_allow_html=True
)

# Auto-refresh
time.sleep(300)  # Refresh every 5 minutes
st.rerun()
