#!/usr/bin/env python3
"""
Bolet Forecaster Catalunya Launcher
Run this script to start the local web application.
"""
import sys
import os
import argparse
import uvicorn

# Ensure the root folder is on PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    pass


def main():
    default_host = os.environ.get("HOST", "127.0.0.1")
    default_port = int(os.environ.get("PORT", 8000))

    parser = argparse.ArgumentParser(description="Bolet Forecaster Catalunya Web App")
    parser.add_argument("--host", default=default_host, help=f"Host to bind (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to bind (default: {default_port})")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    parser.add_argument("--force-update", action="store_true", help="Skip cache and force update weather data from Meteocat / Open-Meteo on startup")

    args = parser.parse_args()

    if args.force_update:
        print("⚡ Skipping cache and forcing weather data update (Meteocat / Open-Meteo)...")
        from app.services.geography_service import GeographyService
        from app.services.weather_service import WeatherService
        geo = GeographyService()
        ws = WeatherService()
        ws.get_weather_for_zones(geo.get_all_zones(), force_update=True)
        print("✅ Weather data cache successfully refreshed!")

    print("=" * 65)
    print("🍄  BOLET FORECASTER CATALUNYA  🍄")
    print("    Previsió de bolets comestibles basada en dades meteorològiques")
    print(f"    Servidor local actiu a: http://{args.host}:{args.port}")
    print("=" * 65)

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

