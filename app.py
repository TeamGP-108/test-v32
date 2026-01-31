# app.py - Complete Weather Website using FastAPI
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from datetime import datetime, timedelta
import sqlite3
import json
from contextlib import asynccontextmanager
import time

# API Configuration - Using your provided API key
WEATHER_API_KEY = "bd5e378503939ddaee76f12ad7a97608"  # Your WeatherAPI.com key
BASE_URL = "http://api.weatherapi.com/v1"

# Track app startup time for uptime
startup_time = time.time()

# Database setup for favorites
def init_db():
    """Initialize SQLite database for favorites and search history"""
    conn = sqlite3.connect(":memory:")  # Use in-memory DB for Streamlit
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS favorites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            country TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add some default favorite cities
    default_favorites = [
        ("New York", "USA"),
        ("London", "UK"),
        ("Tokyo", "Japan"),
        ("Sydney", "Australia"),
        ("Paris", "France"),
        ("Dubai", "UAE"),
        ("Mumbai", "India"),
        ("Singapore", "Singapore")
    ]
    
    for city, country in default_favorites:
        cursor.execute("SELECT 1 FROM favorites WHERE city = ? AND country = ?", (city, country))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO favorites (city, country) VALUES (?, ?)", (city, country))
    
    conn.commit()
    conn.close()

# Initialize database on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    print("✅ Database initialized")
    print("✅ Weather API Key:", WEATHER_API_KEY[:8] + "..." if WEATHER_API_KEY else "Not set")
    yield
    # Shutdown (cleanup if needed)

# Create FastAPI app with lifespan
app = FastAPI(
    title="Weather Forecast Pro",
    description="Real-time weather forecasts worldwide",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper functions
def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    return conn

def get_favorites():
    """Get list of favorite cities"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city, country FROM favorites ORDER BY timestamp DESC LIMIT 10")
    favorites = cursor.fetchall()
    conn.close()
    return favorites

def add_favorite(city: str, country: str):
    """Add a city to favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM favorites WHERE city = ? AND country = ?", (city, country))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO favorites (city, country) VALUES (?, ?)", (city, country))
    conn.commit()
    conn.close()

def remove_favorite(city: str, country: str):
    """Remove a city from favorites"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM favorites WHERE city = ? AND country = ?", (city, country))
    conn.commit()
    conn.close()

def add_search(query: str):
    """Add search to history"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO searches (query) VALUES (?)", (query,))
    conn.commit()
    conn.close()

def get_recent_searches():
    """Get recent searches"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT query FROM searches ORDER BY timestamp DESC LIMIT 10")
    searches = cursor.fetchall()
    conn.close()
    return searches

def get_weather_icon(condition: str):
    """Get Font Awesome icon based on weather condition"""
    condition = condition.lower()
    if any(word in condition for word in ['sunny', 'clear']):
        return "fas fa-sun"
    elif any(word in condition for word in ['cloud', 'overcast']):
        return "fas fa-cloud"
    elif any(word in condition for word in ['rain', 'drizzle']):
        return "fas fa-cloud-rain"
    elif any(word in condition for word in ['snow', 'sleet', 'ice', 'blizzard']):
        return "fas fa-snowflake"
    elif any(word in condition for word in ['storm', 'thunder', 'lightning']):
        return "fas fa-bolt"
    elif any(word in condition for word in ['fog', 'mist', 'haze']):
        return "fas fa-smog"
    elif any(word in condition for word in ['wind', 'breeze']):
        return "fas fa-wind"
    else:
        return "fas fa-cloud-sun"

def format_date(date_str: str):
    """Format date string"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%a, %b %d")
    except:
        return date_str

def get_uptime():
    """Calculate application uptime"""
    uptime_seconds = time.time() - startup_time
    days = int(uptime_seconds // 86400)
    hours = int((uptime_seconds % 86400) // 3600)
    minutes = int((uptime_seconds % 3600) // 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"

async def fetch_weather_data(location: str):
    """Fetch weather data from WeatherAPI.com"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Current weather
            current_url = f"{BASE_URL}/current.json?key={WEATHER_API_KEY}&q={location}&aqi=no"
            current_response = await client.get(current_url)
            current_response.raise_for_status()
            current_data = current_response.json()
            
            # Forecast for 3 days
            forecast_url = f"{BASE_URL}/forecast.json?key={WEATHER_API_KEY}&q={location}&days=3&aqi=no&alerts=no"
            forecast_response = await client.get(forecast_url)
            forecast_response.raise_for_status()
            forecast_data = forecast_response.json()
            
            # Merge data
            weather_data = {
                "location": current_data["location"],
                "current": current_data["current"],
                "forecast": forecast_data["forecast"]["forecastday"][:3]  # Get 3 days
            }
            
            # Add icon
            weather_data["current"]["icon"] = get_weather_icon(weather_data["current"]["condition"]["text"])
            
            # Add icons to forecast
            for day in weather_data["forecast"]:
                day["day"]["icon"] = get_weather_icon(day["day"]["condition"]["text"])
                day["date_formatted"] = format_date(day["date"])
            
            return weather_data
            
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            return {"error": "Location not found. Please try another city."}
        elif e.response.status_code == 401:
            return {"error": "Invalid API key. Please check your configuration."}
        else:
            return {"error": f"API Error: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to fetch weather data: {str(e)}"}

# HTML Template for the homepage
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Weather Forecast Pro</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #fff;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* Header */
        .header {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            text-align: center;
        }
        .header h1 {
            font-size: 3rem;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .header p {
            color: #a0a0c0;
            font-size: 1.1rem;
            margin-bottom: 25px;
        }
        
        /* Search Bar */
        .search-container {
            max-width: 600px;
            margin: 0 auto;
            display: flex;
            gap: 10px;
        }
        .search-input {
            flex: 1;
            padding: 15px 25px;
            border: 2px solid rgba(255, 255, 255, 0.1);
            border-radius: 50px;
            background: rgba(255, 255, 255, 0.05);
            color: white;
            font-size: 1rem;
            transition: all 0.3s ease;
        }
        .search-input:focus {
            outline: none;
            border-color: #00b4db;
            background: rgba(255, 255, 255, 0.1);
        }
        .search-btn {
            padding: 15px 35px;
            background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        .search-btn:hover {
            transform: translateY(-2px);
        }
        
        /* Main Layout */
        .main-content {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }
        @media (min-width: 1200px) {
            .main-content { grid-template-columns: 2fr 1fr; }
        }
        
        /* Weather Cards */
        .weather-card {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        /* Current Weather */
        .current-weather {
            text-align: center;
        }
        .location-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        .location-info h2 {
            font-size: 2rem;
            color: #fff;
        }
        .location-time {
            color: #a0a0c0;
            font-size: 0.9rem;
        }
        .favorite-btn {
            background: rgba(255, 193, 7, 0.1);
            color: #ffc107;
            border: 1px solid rgba(255, 193, 7, 0.3);
            padding: 10px 20px;
            border-radius: 50px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .favorite-btn:hover {
            background: rgba(255, 193, 7, 0.2);
        }
        .current-temp {
            font-size: 5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #00b4db 0%, #0083b0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 20px 0;
        }
        .current-condition {
            font-size: 1.5rem;
            color: #fff;
            margin-bottom: 30px;
        }
        
        /* Weather Stats */
        .weather-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 30px;
        }
        .stat-item {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 15px;
            text-align: center;
        }
        .stat-label {
            font-size: 0.9rem;
            color: #a0a0c0;
            margin-bottom: 5px;
        }
        .stat-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: #fff;
        }
        
        /* Forecast */
        .forecast-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        .forecast-day {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        .forecast-day:hover {
            transform: translateY(-5px);
            background: rgba(255, 255, 255, 0.1);
        }
        .forecast-date {
            color: #a0a0c0;
            font-size: 0.9rem;
            margin-bottom: 10px;
        }
        .forecast-icon {
            font-size: 2.5rem;
            color: #00b4db;
            margin: 10px 0;
        }
        .forecast-temp {
            font-size: 1.3rem;
            font-weight: 600;
            color: #fff;
        }
        .forecast-condition {
            font-size: 0.9rem;
            color: #a0a0c0;
            margin-top: 5px;
        }
        
        /* Sidebar */
        .sidebar-section {
            margin-bottom: 25px;
        }
        .section-title {
            font-size: 1.2rem;
            color: #fff;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        .favorites-list, .recent-list {
            list-style: none;
        }
        .list-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            margin-bottom: 8px;
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
            transition: background 0.3s ease;
        }
        .list-item:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        .city-link {
            color: #fff;
            text-decoration: none;
            cursor: pointer;
        }
        .city-link:hover {
            color: #00b4db;
        }
        .remove-btn {
            background: rgba(255, 0, 0, 0.1);
            color: #ff6b6b;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.9rem;
        }
        
        /* Error & Loading */
        .error-box {
            background: rgba(255, 0, 0, 0.1);
            border-left: 4px solid #ff6b6b;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        .loading {
            text-align: center;
            padding: 40px;
            color: #a0a0c0;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #a0a0c0;
            padding: 30px 0;
            margin-top: 50px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            font-size: 0.9rem;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 { font-size: 2rem; }
            .current-temp { font-size: 3.5rem; }
            .search-container { flex-direction: column; }
            .search-btn { width: 100%; }
            .forecast-grid { grid-template-columns: repeat(2, 1fr); }
            .weather-stats { grid-template-columns: repeat(2, 1fr); }
        }
        @media (max-width: 480px) {
            .forecast-grid { grid-template-columns: 1fr; }
            .weather-stats { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><i class="fas fa-cloud-sun"></i> Weather Forecast Pro</h1>
            <p>Real-time weather forecasts powered by WeatherAPI.com | API Status: Active ✓</p>
            
            <form method="post" action="/" class="search-container">
                <input type="text" name="location" class="search-input" 
                       placeholder="Search for a city (e.g., London, Tokyo, New York)..." 
                       value="{{ location or 'London' }}" required>
                <button type="submit" class="search-btn">
                    <i class="fas fa-search"></i> Search Weather
                </button>
            </form>
        </div>
        
        {% if error %}
        <div class="error-box">
            <i class="fas fa-exclamation-triangle"></i> {{ error }}
        </div>
        {% endif %}
        
        {% if weather_data %}
        <div class="main-content">
            <!-- Left Column: Weather Data -->
            <div class="left-column">
                <!-- Current Weather -->
                <div class="weather-card current-weather">
                    <div class="location-header">
                        <div class="location-info">
                            <h2><i class="fas fa-map-marker-alt"></i> {{ weather_data.location.name }}, {{ weather_data.location.country }}</h2>
                            <div class="location-time">{{ weather_data.location.localtime }}</div>
                        </div>
                        <form method="post" action="/favorite">
                            <input type="hidden" name="city" value="{{ weather_data.location.name }}">
                            <input type="hidden" name="country" value="{{ weather_data.location.country }}">
                            <button type="submit" class="favorite-btn">
                                <i class="fas fa-star"></i> Add to Favorites
                            </button>
                        </form>
                    </div>
                    
                    <div class="current-temp">{{ weather_data.current.temp_c }}°C</div>
                    <div class="current-condition">
                        <i class="{{ weather_data.current.icon }}"></i> {{ weather_data.current.condition.text }}
                    </div>
                    
                    <!-- Weather Stats -->
                    <div class="weather-stats">
                        <div class="stat-item">
                            <div class="stat-label"><i class="fas fa-temperature-high"></i> Feels Like</div>
                            <div class="stat-value">{{ weather_data.current.feelslike_c }}°C</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label"><i class="fas fa-wind"></i> Wind Speed</div>
                            <div class="stat-value">{{ weather_data.current.wind_kph }} km/h</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label"><i class="fas fa-tint"></i> Humidity</div>
                            <div class="stat-value">{{ weather_data.current.humidity }}%</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label"><i class="fas fa-compress-alt"></i> Pressure</div>
                            <div class="stat-value">{{ weather_data.current.pressure_mb }} hPa</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label"><i class="fas fa-eye"></i> Visibility</div>
                            <div class="stat-value">{{ weather_data.current.vis_km }} km</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-label"><i class="fas fa-umbrella"></i> Precipitation</div>
                            <div class="stat-value">{{ weather_data.current.precip_mm }} mm</div>
                        </div>
                    </div>
                </div>
                
                <!-- 3-Day Forecast -->
                <div class="weather-card">
                    <h3 class="section-title"><i class="fas fa-calendar-alt"></i> 3-Day Forecast</h3>
                    <div class="forecast-grid">
                        {% for day in weather_data.forecast %}
                        <div class="forecast-day">
                            <div class="forecast-date">{{ day.date_formatted }}</div>
                            <div class="forecast-icon">
                                <i class="{{ day.day.icon }}"></i>
                            </div>
                            <div class="forecast-temp">{{ day.day.maxtemp_c }}° / {{ day.day.mintemp_c }}°</div>
                            <div class="forecast-condition">{{ day.day.condition.text }}</div>
                            <div style="margin-top: 10px; font-size: 0.8rem; color: #a0a0c0;">
                                <div><i class="fas fa-sun"></i> {{ day.day.avghumidity }}% humidity</div>
                                <div><i class="fas fa-cloud-rain"></i> {{ day.day.totalprecip_mm }}mm rain</div>
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>
            
            <!-- Right Column: Sidebar -->
            <div class="right-column">
                <!-- Favorites -->
                <div class="weather-card sidebar-section">
                    <h3 class="section-title"><i class="fas fa-star"></i> Favorite Cities</h3>
                    <ul class="favorites-list">
                        {% for fav in favorites %}
                        <li class="list-item">
                            <a href="/?location={{ fav.city }}" class="city-link">
                                <i class="fas fa-map-marker-alt"></i> {{ fav.city }}, {{ fav.country }}
                            </a>
                            <form method="post" action="/favorite/remove" style="display: inline;">
                                <input type="hidden" name="city" value="{{ fav.city }}">
                                <input type="hidden" name="country" value="{{ fav.country }}">
                                <button type="submit" class="remove-btn" title="Remove">
                                    <i class="fas fa-times"></i>
                                </button>
                            </form>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                
                <!-- Recent Searches -->
                <div class="weather-card sidebar-section">
                    <h3 class="section-title"><i class="fas fa-history"></i> Recent Searches</h3>
                    <ul class="recent-list">
                        {% for search in recent_searches %}
                        <li class="list-item">
                            <a href="/?location={{ search.query }}" class="city-link">
                                <i class="fas fa-search"></i> {{ search.query }}
                            </a>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
                
                <!-- System Info -->
                <div class="weather-card sidebar-section">
                    <h3 class="section-title"><i class="fas fa-info-circle"></i> System Info</h3>
                    <div style="color: #a0a0c0; font-size: 0.9rem;">
                        <div style="margin-bottom: 8px;">API: WeatherAPI.com</div>
                        <div style="margin-bottom: 8px;">Uptime: {{ uptime }}</div>
                        <div style="margin-bottom: 8px;">Last Update: {{ current_time }}</div>
                        <div>Data refreshed every 30 minutes</div>
                    </div>
                </div>
            </div>
        </div>
        {% else %}
        <div class="loading">
            <i class="fas fa-cloud-sun fa-spin" style="font-size: 3rem; margin-bottom: 20px;"></i>
            <p>Loading weather data...</p>
            <p style="margin-top: 20px; font-size: 0.9rem;">Try searching for a city above!</p>
        </div>
        {% endif %}
        
        <div class="footer">
            <p>© 2024 Weather Forecast Pro | Powered by <a href="https://www.weatherapi.com/" style="color: #00b4db;" target="_blank">WeatherAPI.com</a></p>
            <p style="margin-top: 10px;">Data updates in real-time | API Key: {{ api_key_display }}</p>
            <p style="margin-top: 10px; font-size: 0.8rem;">
                <i class="fas fa-server"></i> FastAPI Backend | 
                <i class="fas fa-mobile-alt"></i> Responsive Design | 
                <i class="fas fa-bolt"></i> Real-time Updates
            </p>
        </div>
    </div>
    
    <script>
        // Auto-refresh weather data every 30 minutes
        setTimeout(() => location.reload(), 30 * 60 * 1000);
        
        // Add click handlers for city links
        document.querySelectorAll('.city-link').forEach(link => {
            link.addEventListener('click', function(e) {
                const location = this.getAttribute('href').split('=')[1];
                document.querySelector('input[name="location"]').value = decodeURIComponent(location);
                document.querySelector('form').submit();
            });
        });
        
        // Add animations
        document.addEventListener('DOMContentLoaded', () => {
            const cards = document.querySelectorAll('.weather-card');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
</body>
</html>
"""

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, location: str = "London"):
    """Main homepage with weather search"""
    favorites = get_favorites()
    recent_searches = get_recent_searches()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Fetch weather data for the location
    weather_data = await fetch_weather_data(location)
    
    # If no error, add to search history
    if "error" not in weather_data:
        add_search(location)
    
    # Prepare template variables
    template_vars = {
        "request": request,
        "location": location,
        "weather_data": weather_data if "error" not in weather_data else None,
        "error": weather_data.get("error") if "error" in weather_data else None,
        "favorites": favorites,
        "recent_searches": recent_searches,
        "current_time": current_time,
        "uptime": get_uptime(),
        "api_key_display": f"{WEATHER_API_KEY[:8]}..." if WEATHER_API_KEY else "Not configured"
    }
    
    # Return HTML response
    return HTMLResponse(content=HTML_TEMPLATE.format(**template_vars))

@app.post("/", response_class=HTMLResponse)
async def search_weather(request: Request, location: str = Form(...)):
    """Handle search form submission"""
    return await home(request, location)

@app.post("/favorite")
async def add_to_favorites(city: str = Form(...), country: str = Form(...)):
    """Add city to favorites"""
    add_favorite(city, country)
    return RedirectResponse(url=f"/?location={city}", status_code=303)

@app.post("/favorite/remove")
async def remove_from_favorites(city: str = Form(...), country: str = Form(...)):
    """Remove city from favorites"""
    remove_favorite(city, country)
    return RedirectResponse(url="/?location=London", status_code=303)

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "service": "weather-forecast-pro",
        "timestamp": datetime.now().isoformat(),
        "uptime": get_uptime(),
        "api_status": "active" if WEATHER_API_KEY else "inactive",
        "version": "2.0.0"
    }

@app.get("/api/weather/{location}")
async def api_weather(location: str):
    """API endpoint for weather data"""
    weather_data = await fetch_weather_data(location)
    if "error" in weather_data:
        raise HTTPException(status_code=400, detail=weather_data["error"])
    return weather_data

# For Streamlit deployment
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🌤️ Weather Forecast Pro starting on http://localhost:{port}")
    print(f"🔑 Using API Key: {WEATHER_API_KEY[:8]}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
