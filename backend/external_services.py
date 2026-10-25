import os
import re
import json
import html
import urllib.request
import urllib.parse
from datetime import datetime, timezone
import zoneinfo
from typing import Dict, Any, List, Optional

# Weather code mapping according to WMO Weather interpretation codes
WMO_WEATHER_CODES = {
    0: "Clear sky ☀️",
    1: "Mainly clear 🌤️",
    2: "Partly cloudy ⛅",
    3: "Overcast ☁️",
    45: "Fog 🌫️",
    48: "Depositing rime fog 🌫️",
    51: "Light drizzle 🌦️",
    53: "Moderate drizzle 🌦️",
    55: "Dense drizzle 🌧️",
    61: "Slight rain 🌧️",
    63: "Moderate rain 🌧️",
    65: "Heavy rain ⛈️",
    71: "Slight snow 🌨️",
    73: "Moderate snow 🌨️",
    75: "Heavy snow ❄️",
    80: "Slight rain showers 🌦️",
    81: "Moderate rain showers 🌧️",
    82: "Violent rain showers ⛈️",
    95: "Thunderstorm ⚡",
    96: "Thunderstorm with slight hail ⛈️",
    99: "Thunderstorm with heavy hail ⛈️"
}

def get_live_weather(location_query: str) -> Dict[str, Any]:
    """
    Retrieves real-time current weather and 24h forecast using Open-Meteo
    Free, zero API key required, reliable worldwide.
    """
    cleaned_query = location_query.strip().title()
    if not cleaned_query:
        cleaned_query = "Vijayawada"

    # Step 1: Geocoding
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(cleaned_query)}&count=1&language=en&format=json"
    req = urllib.request.Request(geo_url, headers={"User-Agent": "AILifePilot/2.0"})
    
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            geo_data = json.loads(resp.read().decode("utf-8"))
            results = geo_data.get("results")
            if not results:
                return {
                    "success": False,
                    "error": f"Location '{cleaned_query}' not found. Please specify a recognized city or region.",
                    "location": cleaned_query
                }
            best_match = results[0]
            lat = best_match["latitude"]
            lon = best_match["longitude"]
            city_name = best_match.get("name", cleaned_query)
            country = best_match.get("country", "")
            region = best_match.get("admin1", "")
            tz_str = best_match.get("timezone", "UTC")
    except Exception as e:
        return {
            "success": False,
            "error": f"Weather geocoding connection failed: {str(e)}",
            "location": cleaned_query
        }

    # Step 2: Fetch current weather & forecast
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
        f"&timezone={urllib.parse.quote(tz_str)}"
    )
    req2 = urllib.request.Request(weather_url, headers={"User-Agent": "AILifePilot/2.0"})
    
    try:
        with urllib.request.urlopen(req2, timeout=8) as resp2:
            w_data = json.loads(resp2.read().decode("utf-8"))
            curr = w_data.get("current", {})
            w_code = curr.get("weather_code", 0)
            condition = WMO_WEATHER_CODES.get(w_code, "Partly Cloudy")

            return {
                "success": True,
                "city": city_name,
                "region": region,
                "country": country,
                "coordinates": f"{lat:.2f}, {lon:.2f}",
                "timezone": tz_str,
                "observation_time": curr.get("time", datetime.now().isoformat()),
                "temperature_c": round(curr.get("temperature_2m", 0.0), 1),
                "temperature_f": round(curr.get("temperature_2m", 0.0) * 9/5 + 32, 1),
                "feels_like_c": round(curr.get("apparent_temperature", 0.0), 1),
                "humidity_percent": curr.get("relative_humidity_2m", 0),
                "precipitation_mm": curr.get("precipitation", 0.0),
                "wind_speed_kmh": round(curr.get("wind_speed_10m", 0.0), 1),
                "condition": condition,
                "source": "Open-Meteo Live API",
                "timestamp": datetime.now().isoformat()
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Weather data retrieval failed: {str(e)}",
            "location": f"{city_name}, {country}"
        }


def search_web(query: str, max_results: int = 5) -> Dict[str, Any]:
    """
    Performs a live web search using DuckDuckGo HTML parser.
    Extracts genuine external source URLs, titles, and snippets.
    """
    cleaned_query = query.strip()
    if not cleaned_query:
        return {"success": False, "error": "Search query cannot be empty", "results": []}

    search_url = "https://html.duckduckgo.com/html/?q=" + urllib.parse.quote(cleaned_query)
    req = urllib.request.Request(
        search_url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            page = response.read().decode("utf-8", errors="ignore")

        clean = lambda t: html.unescape(re.sub(r"<[^<]+?>", "", t)).strip()

        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', page, re.DOTALL)
        titles = re.findall(r'<a class="result__title[^>]*>(.*?)</a>', page, re.DOTALL)
        raw_urls = re.findall(r'<a class="result__url"[^>]*href="([^"]+)"', page)

        results = []
        for i in range(min(max_results, len(snippets))):
            t = clean(titles[i]) if i < len(titles) else f"Resource {i+1}"
            s = clean(snippets[i])
            raw_u = raw_urls[i].strip() if i < len(raw_urls) else ""

            # Unquote DuckDuckGo redirect url parameter 'uddg' to get the actual direct URL
            real_url = raw_u
            if "uddg=" in raw_u:
                try:
                    parsed_qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_u).query)
                    if "uddg" in parsed_qs:
                        real_url = parsed_qs["uddg"][0]
                except Exception:
                    pass
            elif raw_u.startswith("//"):
                real_url = "https:" + raw_u

            if not real_url or not real_url.startswith("http"):
                real_url = f"https://duckduckgo.com/?q={urllib.parse.quote(cleaned_query)}"

            results.append({
                "title": t,
                "snippet": s,
                "url": real_url
            })

        return {
            "success": True,
            "query": cleaned_query,
            "result_count": len(results),
            "results": results,
            "searched_at": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "query": cleaned_query,
            "error": f"Live web search failed: {str(e)}",
            "results": []
        }


def get_current_time(timezone_name: str = "auto") -> Dict[str, Any]:
    """
    Returns the real-time date, time, and timezone information.
    """
    now_utc = datetime.now(timezone.utc)
    target_tz = None

    if timezone_name and timezone_name != "auto":
        try:
            target_tz = zoneinfo.ZoneInfo(timezone_name)
        except Exception:
            target_tz = None

    if target_tz is None:
        # Default to local system timezone
        now_local = datetime.now()
        tz_name = datetime.now().astimezone().tzname() or "Local Time"
    else:
        now_local = now_utc.astimezone(target_tz)
        tz_name = timezone_name

    return {
        "iso_timestamp": now_local.isoformat(),
        "date": now_local.strftime("%Y-%m-%d"),
        "time_24h": now_local.strftime("%H:%M:%S"),
        "time_12h": now_local.strftime("%I:%M:%S %p"),
        "day_of_week": now_local.strftime("%A"),
        "timezone": tz_name,
        "formatted_display": now_local.strftime("%A, %B %d, %Y - %I:%M %p")
    }


def parse_uploaded_document(filename: str, content_bytes: bytes) -> Dict[str, Any]:
    """
    Extracts text from uploaded documents (.txt, .md, .json, .csv, or plain text from .pdf).
    """
    ext = os.path.splitext(filename)[1].lower()
    text = ""

    if ext in [".txt", ".md", ".json", ".csv", ".py", ".js", ".ts", ".html"]:
        try:
            text = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = content_bytes.decode("latin-1", errors="ignore")
    elif ext == ".pdf":
        # Basic text stream extraction for PDF without heavy dependencies
        raw_str = content_bytes.decode("latin-1", errors="ignore")
        # Extract text blocks between BT and ET
        matches = re.findall(r"\((.*?)\)\s*Tj", raw_str)
        if matches:
            text = " ".join(matches)
        else:
            # Fallback: clean ASCII sequences
            clean_ascii = re.findall(r"[A-Za-z0-9 ,.:;!?'\"\-_\n]{4,}", raw_str)
            text = "\n".join(clean_ascii[:500])
    else:
        text = content_bytes.decode("utf-8", errors="ignore")

    char_count = len(text)
    word_count = len(text.split())

    return {
        "filename": filename,
        "extension": ext,
        "text": text[:20000], # limit to 20,000 characters for token safety
        "char_count": char_count,
        "word_count": word_count,
        "is_truncated": char_count > 20000
    }


def generate_icalendar(tasks: List[Dict[str, Any]]) -> str:
    """
    Generates a standard RFC 5545 iCalendar (.ics) format string.
    Can be imported into Google Calendar, Apple Calendar, Microsoft Outlook.
    """
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//AI LifePilot//Intelligent Daily Assistant//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]

    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    for t in tasks:
        task_id = t.get("id", "task-0")
        title = t.get("title", "Task").replace("\n", " ").replace(";", "\\;").replace(",", "\\,")
        desc = (t.get("description") or f"Category: {t.get('category', 'General')}").replace("\n", "\\n")
        deadline_str = t.get("deadline", "")
        start_time = t.get("scheduled_start")
        end_time = t.get("scheduled_end")

        dt_start_str = ""
        dt_end_str = ""

        if deadline_str:
            try:
                clean_dl = deadline_str[:16].replace("-", "").replace(":", "")
                if "T" in clean_dl:
                    dt_end_str = clean_dl + "00Z"
                else:
                    dt_end_str = clean_dl + "T180000Z"
                dt_start_str = dt_end_str
            except Exception:
                pass

        if not dt_start_str:
            dt_start_str = now_stamp
            dt_end_str = now_stamp

        lines.extend([
            "BEGIN:VEVENT",
            f"UID:{task_id}@lifepilot.local",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART:{dt_start_str}",
            f"DTEND:{dt_end_str}",
            f"SUMMARY:{title}",
            f"DESCRIPTION:{desc}",
            f"STATUS:{'COMPLETED' if t.get('status') == 'completed' else 'CONFIRMED'}",
            f"PRIORITY:{'1' if 'urgent' in t.get('priority', '') else '5'}",
            "END:VEVENT"
        ])

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)
