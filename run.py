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


def main():
    parser = argparse.ArgumentParser(description="Bolet Forecaster Catalunya Web App")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for development")

    args = parser.parse_args()

    print("=" * 65)
    print("🍄  BOLET FORECASTER CATALUNYA  🍄")
    print("    Previsió de bolets comestibles basada en dades meteorològiques")
    print(f"    Servidor local actiu a: http://{args.host}:{args.port}")
    print("=" * 65)

    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

