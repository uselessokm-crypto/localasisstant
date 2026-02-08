#!/usr/bin/env python3
"""
Entry point for the local voice assistant
This script allows you to run the assistant either in voice mode or API mode
"""

import argparse
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from src.main_assistant import main as run_voice_assistant
from src.api.rest_api import app
import uvicorn


def main():
    parser = argparse.ArgumentParser(description="Local Voice Assistant")
    parser.add_argument(
        "--mode", 
        choices=["voice", "api"], 
        default="voice",
        help="Run mode: 'voice' for voice-controlled assistant, 'api' for REST API"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for API mode (default: 8000)"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for API mode (default: 0.0.0.0)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "voice":
        print("Starting voice assistant...")
        print("Say 'capri' to activate the assistant")
        run_voice_assistant()
    elif args.mode == "api":
        print(f"Starting API server on {args.host}:{args.port}")
        print("API documentation available at /docs")
        uvicorn.run(
            app, 
            host=args.host, 
            port=args.port,
            log_level="info"
        )


if __name__ == "__main__":
    main()