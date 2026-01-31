# app.py - Complete Weather App for Streamlit Cloud
import streamlit as st
import httpx
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

# Set page config
st.set_page_config(
    page_title="Weather Forecast Pro 🌤️",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
WEATHER_API_KEY = "bd5e378503939ddaee76f12ad7a97608"  # Your WeatherAPI.com key
BASE_URL = "http://api.weatherapi.com/v1"

# Initialize session state
if 'startup_time' not in st.session_state:
    st.session_state.startup_time = time.time()
if 'favorites' not in st.session_state:
    st.session_state.favorites = []
if 'recent_searches' not in st.session_state:
    st.session_state.recent_searches = []
if 'current_location' not in st.session_state:
    st.session_state.current_location = "London"

# Initialize default favorites
if not st.session_state.favorites:
    st.session_state.favorites = [
        {"city": "New York", "country": "USA"},
        {"city": "London", "country": "UK"},
        {"city": "Tokyo", "country": "Japan"},
        {"city": "Sydney", "country": "Australia"},
        {"city": "Paris", "country": "France"},
        {"city": "Dubai", "country": "UAE"},
        {"city": "Mumbai", "country": "India"},
        {"city": "Singapore", "country": "Singapore"}
    ]

# Helper functions
def get_weather_icon(condition: str) -> str:
    """Get emoji icon based on weather condition"""
    condition = condition.lower()
    if any(word in condition for word in ['sunny', 'clear']):
        return "☀️"
    elif any(word in condition for word in ['cloud', 'overcast']):
        return "☁️"
    elif any(word in condition for word in ['rain', 'drizzle']):
        return "🌧️"
    elif any(word in condition for word in ['snow', 'sleet', 'ice', 'blizzard']):
        return "❄️"
    elif any(word in condition for word in ['storm', 'thunder', 'lightning']):
        return "⛈️"
    elif any(word in condition for word in ['fog', 'mist', 'haze']):
        return "🌫️"
    elif any(word in condition for word in ['wind', 'breeze']):
        return "💨"
    else:
        return "⛅"

def format_date(date_str: str) -> str:
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%a, %b %d")
    except:
        return date_str

def get_uptime() -> str:
    """Calculate application uptime"""
    uptime_seconds = time.time() - st.session_state.startup_time
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

async def fetch_weather_data(location: str) -> Dict:
    """Fetch weather data from WeatherAPI.com"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Current weather and forecast
            url = f"{BASE_URL}/forecast.json?key={WEATHER_API_KEY}&q={location}&days=3&aqi=no&alerts=no"
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Add icons
            data["current"]["icon"] = get_weather_icon(data["current"]["condition"]["text"])
            for day in data["forecast"]["forecastday"]:
                day["day"]["icon"] = get_weather_icon(day["day"]["condition"]["text"])
                day["date_formatted"] = format_date(day["date"])
            
            return data
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            return {"error": "Location not found. Please try another city."}
        elif e.response.status_code == 401:
            return {"error": "Invalid API key. Please check your configuration."}
        else:
            return {"error": f"API Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}

def add_to_favorites(city: str, country: str):
    """Add city to favorites"""
    if not any(f["city"] == city and f["country"] == country for f in st.session_state.favorites):
        st.session_state.favorites.append({"city": city, "country": country})

def remove_from_favorites(city: str, country: str):
    """Remove city from favorites"""
    st.session_state.favorites = [
        f for f in st.session_state.favorites 
        if not (f["city"] == city and f["country"] == country)
    ]

def add_to_search_history(query: str):
    """Add search to history"""
    if query not in st.session_state.recent_searches:
        st.session_state.recent_searches.insert(0, query)
        # Keep only last 10 searches
        st.session_state.recent_searches = st.session_state.recent_searches[:10]

# Custom CSS
st.markdown("""
<style>
    /* Main container */
    .stApp {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: rgba(255, 255, 255, 0.05) !important;
        backdrop-filter: blur(10px);
    }
    
    /* Cards */
    .weather-card {
        background: rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Metrics */
    .stMetric {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 10px;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0, 180, 219, 0.3);
    }
    
    /* Text */
    .big-text {
        font-size: 3.5rem !important;
        font-weight: 700;
        background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .medium-text {
        font-size: 1.5rem !important;
        color: #ffffff;
    }
    
    .small-text {
        font-size: 0.9rem !important;
        color: #a0a0c0;
    }
</style>
""", unsafe_allow_html=True)

# Main App
def main():
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("<h1 style='text-align: center; color: white;'>🌤️ Weather Forecast Pro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #a0a0c0;'>Real-time weather forecasts powered by WeatherAPI.com</p>", unsafe_allow_html=True)
    
    with col2:
        st.metric("API Status", "Active", "✓")
    
    # Search Bar
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            location = st.text_input(
                "Search Location",
                value=st.session_state.current_location,
                placeholder="Enter city name (e.g., London, Tokyo, New York)...",
                label_visibility="collapsed"
            )
        with col2:
            if st.button("🔍 Search", use_container_width=True):
                st.session_state.current_location = location
                st.rerun()
    
    # Main Content
    if location:
        try:
            # Fetch weather data
            import asyncio
            
            # Create async function and run it
            async def get_data():
                return await fetch_weather_data(location)
            
            # Run the async function
            weather_data = asyncio.run(get_data())
            
            # Check for errors
            if "error" in weather_data:
                st.error(f"⚠️ {weather_data['error']}")
                # Show default favorites
                st.info("Try one of these popular cities:")
                cols = st.columns(4)
                for idx, fav in enumerate(st.session_state.favorites[:8]):
                    with cols[idx % 4]:
                        if st.button(f"{fav['city']}", key=f"fav_{idx}"):
                            st.session_state.current_location = fav['city']
                            st.rerun()
            else:
                # Add to search history
                add_to_search_history(location)
                
                # Display Weather Data
                st.markdown("---")
                
                # Current Weather Header
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"### {weather_data['location']['name']}, {weather_data['location']['country']}")
                    st.markdown(f"*{weather_data['location']['localtime']}*")
                
                with col2:
                    if st.button("⭐ Add to Favorites", use_container_width=True):
                        add_to_favorites(weather_data['location']['name'], weather_data['location']['country'])
                        st.success(f"Added {weather_data['location']['name']} to favorites!")
                
                with col3:
                    st.metric("API Calls", "Successful", "✓")
                
                # Current Weather Card
                with st.container():
                    st.markdown('<div class="weather-card">', unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col1:
                        st.markdown(f"<div class='big-text'>{weather_data['current']['icon']}</div>", unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown(f"<div class='big-text'>{weather_data['current']['temp_c']}°C</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='medium-text'>{weather_data['current']['condition']['text']}</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='small-text'>Feels like {weather_data['current']['feelslike_c']}°C</div>", unsafe_allow_html=True)
                    
                    with col3:
                        st.metric("Humidity", f"{weather_data['current']['humidity']}%")
                        st.metric("Wind", f"{weather_data['current']['wind_kph']} km/h")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Weather Metrics
                st.markdown("### 📊 Weather Details")
                cols = st.columns(5)
                metrics = [
                    ("🌡️ Feels Like", f"{weather_data['current']['feelslike_c']}°C"),
                    ("💨 Wind", f"{weather_data['current']['wind_kph']} km/h"),
                    ("💧 Humidity", f"{weather_data['current']['humidity']}%"),
                    ("📊 Pressure", f"{weather_data['current']['pressure_mb']} hPa"),
                    ("👁️ Visibility", f"{weather_data['current']['vis_km']} km"),
                    ("🌧️ Precipitation", f"{weather_data['current']['precip_mm']} mm"),
                    ("🌅 UV Index", f"{weather_data['current']['uv']}"),
                    ("🌬️ Wind Direction", f"{weather_data['current']['wind_dir']}"),
                    ("🌀 Gust", f"{weather_data['current']['gust_kph']} km/h"),
                    ("🌡️ Dew Point", f"{weather_data['current']['dewpoint_c']}°C")
                ]
                
                for idx, (label, value) in enumerate(metrics):
                    with cols[idx % 5]:
                        st.metric(label, value)
                
                # 3-Day Forecast
                st.markdown("### 📅 3-Day Forecast")
                forecast_cols = st.columns(3)
                for idx, day in enumerate(weather_data['forecast']['forecastday']):
                    with forecast_cols[idx]:
                        with st.container():
                            st.markdown('<div class="weather-card">', unsafe_allow_html=True)
                            st.markdown(f"##### {day['date_formatted']}")
                            st.markdown(f"### {day['day']['icon']}")
                            st.markdown(f"**{day['day']['maxtemp_c']}° / {day['day']['mintemp_c']}°**")
                            st.markdown(f"{day['day']['condition']['text']}")
                            st.markdown(f"🌧️ {day['day']['totalprecip_mm']}mm rain")
                            st.markdown(f"💧 {day['day']['avghumidity']}% humidity")
                            st.markdown('</div>', unsafe_allow_html=True)
                
                # Hourly Forecast (next 12 hours)
                st.markdown("### ⏰ Next 12 Hours")
                hourly_data = weather_data['forecast']['forecastday'][0]['hour'][:12]
                hourly_cols = st.columns(12)
                for idx, hour in enumerate(hourly_data):
                    with hourly_cols[idx]:
                        time_str = datetime.strptime(hour['time'], "%Y-%m-%d %H:%M").strftime("%I%p")
                        st.markdown(f"**{time_str}**")
                        st.markdown(f"{get_weather_icon(hour['condition']['text'])}")
                        st.markdown(f"**{hour['temp_c']}°**")
        
        except Exception as e:
            st.error(f"Error fetching weather data: {str(e)}")
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⭐ Favorites")
        
        # Display favorites
        if st.session_state.favorites:
            for fav in st.session_state.favorites[:10]:
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(f"📍 {fav['city']}, {fav['country']}", key=f"fav_{fav['city']}", use_container_width=True):
                        st.session_state.current_location = fav['city']
                        st.rerun()
                with col2:
                    if st.button("🗑️", key=f"del_{fav['city']}"):
                        remove_from_favorites(fav['city'], fav['country'])
                        st.rerun()
        else:
            st.info("No favorites yet. Search for a city and click 'Add to Favorites'.")
        
        st.markdown("---")
        st.markdown("## 🔍 Recent Searches")
        
        # Display recent searches
        if st.session_state.recent_searches:
            for search in st.session_state.recent_searches[:5]:
                if st.button(f"🔍 {search}", key=f"search_{search}", use_container_width=True):
                    st.session_state.current_location = search
                    st.rerun()
        else:
            st.info("No recent searches.")
        
        st.markdown("---")
        st.markdown("## ℹ️ System Info")
        
        # System information
        st.markdown(f"**Uptime:** {get_uptime()}")
        st.markdown(f"**Current Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown(f"**API Status:** Active ✓")
        st.markdown(f"**Version:** 2.0.0")
        
        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
        
        # Clear history button
        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.recent_searches = []
            st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #a0a0c0; padding: 20px;'>
            <p>© 2024 Weather Forecast Pro | Powered by <a href='https://www.weatherapi.com/' style='color: #00b4db;' target='_blank'>WeatherAPI.com</a></p>
            <p style='font-size: 0.8rem;'>
                Data updates in real-time | Auto-refresh every 5 minutes
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Auto-refresh every 5 minutes
    time.sleep(300)
    st.rerun()

if __name__ == "__main__":
    main()
