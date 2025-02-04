import subprocess
import sys
import os

def run_servers():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Define paths to server files and their directories
    mainchat_dir = os.path.join(current_dir, "MainChat")
    overseer_dir = os.path.join(current_dir, "Overseer")
    notification_dir = os.path.join(current_dir, "NotificationServer")
    taskupdater_dir = os.path.join(current_dir, "TaskUpdater")
    frontend_dir = os.path.join(current_dir, "MainChatFrontend")
    
    mainchat_server = os.path.join(mainchat_dir, "server_mainchat.py")
    overseer_server = os.path.join(overseer_dir, "server_overseer.py")
    notification_server = os.path.join(notification_dir, "server_notifications.py")
    taskupdater_server = os.path.join(taskupdater_dir, "server_taskupdater.py")

    try:
        # Start all servers using Python subprocess with their respective working directories
        mainchat_process = subprocess.Popen([sys.executable, mainchat_server], cwd=mainchat_dir)
        overseer_process = subprocess.Popen([sys.executable, overseer_server], cwd=overseer_dir)
        notification_process = subprocess.Popen([sys.executable, notification_server], cwd=notification_dir)
        taskupdater_process = subprocess.Popen([sys.executable, taskupdater_server], cwd=taskupdater_dir)
        # Serve frontend using Python's HTTP server
        frontend_process = subprocess.Popen([sys.executable, "-m", "http.server", "8000"], cwd=frontend_dir)

        # Wait for all processes to complete (or until interrupted)
        mainchat_process.wait()
        overseer_process.wait()
        notification_process.wait()
        taskupdater_process.wait()
        frontend_process.wait()
    except KeyboardInterrupt:
        # Handle graceful shutdown on Ctrl+C
        print("\nShutting down servers...")
        mainchat_process.terminate()
        overseer_process.terminate()
        notification_process.terminate()
        taskupdater_process.terminate()
        frontend_process.terminate()
        print("Servers stopped")

if __name__ == "__main__":
    run_servers()
