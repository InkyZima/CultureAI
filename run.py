import asyncio
import signal
import sys
from src.main import create_app

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

async def main():
    # Create the app
    app = await create_app()
    
    try:
        # Launch the app (assuming it returns a tuple of tasks)
        tasks = app.launch()
        if isinstance(tasks, (tuple, list)):
            await asyncio.gather(*tasks)
        else:
            await tasks
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
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
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