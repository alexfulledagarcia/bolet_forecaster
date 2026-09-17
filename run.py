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
    default_host = os.environ.get("HOST", "127.0.0.1")
    default_port = int(os.environ.get("PORT", 8000))
    parser.add_argument("--host", default=default_host, help=f"Host to bind (default: {default_host})")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to bind (default: {default_port})")
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

