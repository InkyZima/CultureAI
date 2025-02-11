import subprocess
import sys
import webbrowser
from time import sleep
import argparse
from backend.utils.db_utils import clear_history

def run_app():
    # Start the Flask backend
    print("Starting backend server...")
    backend_process = subprocess.Popen([sys.executable, "backend/app_backend.py"])
    
    # Give the backend a moment to start up
    sleep(2)
    
    # Start the Streamlit frontend
    print("Starting frontend...")
    frontend_process = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "frontend/app_frontend.py"])
    
    # Open the frontend in the default browser
    webbrowser.open("http://localhost:8501")
    
    try:
        # Keep the script running until interrupted
        frontend_process.wait()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        frontend_process.terminate()
        backend_process.terminate()
        frontend_process.wait()
        backend_process.wait()
        print("Servers shut down successfully")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the application with options.")
    parser.add_argument(
        "--clear-history",
        action="store_true",
        help="Delete all records from the SQL history table before running the app.",
    )
    args = parser.parse_args()

    if args.clear_history:
        clear_history()

    run_app()