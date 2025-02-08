import asyncio
import signal
import sys
import logging
from src.main import create_app

# Configure logging to ignore the specific Windows error
logging.getLogger('asyncio').setLevel(logging.CRITICAL)

class WindowsSelectorEventLoopPolicy(asyncio.WindowsSelectorEventLoopPolicy):
    def get_event_loop(self):
        try:
            return super().get_event_loop()
        except RuntimeError as exc:
            if "There is no current event loop in thread" in str(exc):
                loop = self.new_event_loop()
                self.set_event_loop(loop)
                return loop
            raise

async def shutdown(app, loop):
    """Perform cleanup of all async resources"""
    print("\nShutting down gracefully...")
    
    # Cancel all running tasks
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    if tasks:
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
    
    # Close the loop
    loop.stop()

async def clear_database():
    """Clear all entries from messages and extracted_information tables"""
    import sqlite3
    import os
    
    db_path = 'data/chat.db'
    if os.path.exists(db_path):
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            # Clear messages table except system prompt
            cursor.execute('DELETE FROM messages WHERE role != "system"')
            # Clear extracted_information table
            cursor.execute('DELETE FROM extracted_information')
            # Clear conversation_analysis table
            cursor.execute('DELETE FROM conversation_analysis')
            # Clear generated_instructions table
            cursor.execute('DELETE FROM generated_instructions')
            
            conn.commit()
            print("Database tables cleared successfully")

async def main():
    # Create the app
    app = await create_app()
    
    # Clear database tables
    await clear_database()
    
    # Create a task to keep the event loop running
    async def keep_running():
        while True:
            await asyncio.sleep(1)

    try:
        # Start the background task
        background_task = asyncio.create_task(keep_running())
        
        # Launch the Gradio app in non-blocking mode
        app.queue()
        app.launch(prevent_thread_lock=True)
        
        # Keep the main task running
        await background_task
    except (asyncio.CancelledError, KeyboardInterrupt):
        pass
    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        # Get the current loop
        loop = asyncio.get_running_loop()
        await shutdown(app, loop)

if __name__ == "__main__":
    if sys.platform == "win32":
        # Set up a different event loop policy for Windows
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    finally:
        try:
            loop.close()
        except Exception as e:
            pass
        print("Shutdown complete") 