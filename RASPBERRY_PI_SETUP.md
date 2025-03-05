# Running CultureAI on Raspberry Pi (Python 3.7)

This guide provides instructions for running the CultureAI application on a Raspberry Pi with Python 3.7.

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/CultureAI.git
cd CultureAI
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

Create a `.env` file with the following content:

```
GOOGLE_API_KEY=your_google_api_key_here
CHAT_MODEL=gemini-2.0-flash
DEFAULT_MODEL=gemini-2.0-flash
THINKING_MODEL=gemini-2.0-flash  # Important for the thinking agent
INJECTION_INTERVAL=12
NTFY_TOPIC=your_ntfy_topic_here
```

Replace `your_google_api_key_here` with your actual Google API key.

### 5. Run the application

```bash
python app.py
```

The application will be available at `http://<raspberry-pi-ip>:5000` where `<raspberry-pi-ip>` is the IP address of your Raspberry Pi.

## Running the Agent

To run the agent functionality:

```bash
python run_agent.py --prompt "send the user a test notification"
```

## Recent Updates (March 2025)

This version of CultureAI has been significantly improved for Raspberry Pi compatibility:

1. **Enhanced Gemini API Wrapper**: The custom wrapper has been completely rewritten using direct HTTP requests to the Gemini v1beta API.

2. **Improved Message Format Handling**: Fixed issues with message format and parts structure for the v1beta API.

3. **Comprehensive Testing**: Added multiple test scripts in the `tests` directory to verify API compatibility:
   - `test_formatted_message.py`: Tests the message formatting pattern
   - `test_chat_session.py`: Tests the full chat session initialization
   - `test_chat_flow.py`: Tests the entire chat processing flow

4. **Robust Timestamp Handling**: Added improved fallback mechanisms for timestamp parsing and formatting.

5. **Network Accessibility**: Ensured Flask app is accessible on the network by default.

6. **Updated Dependencies**: Added `tzlocal` and `pytz` for consistent timezone handling.

7. **Removed SDK Dependency**: The application no longer attempts to use the official Google SDK, simplifying the codebase.

## How it works

This version of CultureAI has been modified to be compatible with Python 3.7 on Raspberry Pi:

1. **Custom Gemini API Wrapper**: Since the official `google-generativeai` package requires Python 3.9+, we've created a custom wrapper using HTTP requests to directly access the Gemini API.

2. **Fallback Mechanism**: The code will try to import the official SDK first, and if that fails, it will use our custom wrapper automatically.

3. **Compatible Dependencies**: The requirements.txt file has been updated to use versions that are compatible with Python 3.7.

4. **Support for All Use Cases**: The wrapper implements both chat functionality (`start_chat` and `send_message`) and the single-prompt functionality (`generate_content`) used by the thinking agent.

5. **Robust Error Handling**: The code includes improved error handling and timestamp processing to handle different timestamp formats correctly.

6. **Network Accessibility**: The Flask app is configured to listen on all network interfaces (`host='0.0.0.0'`), making it accessible from other devices on your network.

## Testing the Wrapper

You can test that the custom wrapper is working correctly by running:

```bash
python tests/test_gemini_wrapper.py
```

This will verify that both chat functionality and the `generate_content` method work as expected.

## Troubleshooting

If you encounter any issues:

1. **Connection issues**: Make sure your API key is correct and that your Raspberry Pi has internet access. You may have to add host='0.0.0.0' to socketio.run

2. **ImportError**: Ensure that all dependencies are installed correctly.

3. **Performance**: The application may run slower on a Raspberry Pi compared to more powerful hardware. This is normal.

4. **Log files**: Check the log files for detailed error messages if the application doesn't start properly.

5. **'No module named google.generativeai'**: This is expected when running on Python 3.7. The application now directly uses the custom wrapper.

6. **THINKING_MODEL environment variable**: If you see errors about the thinking agent, make sure you've set the `THINKING_MODEL` environment variable in your `.env` file.

7. **Message format errors**: If you see message format errors, ensure you're using the latest version of the code. The v1beta API requires parts to have a "text" key instead of direct strings.

8. **WebSocket issues**: If you encounter WebSocket connection problems, make sure the `simple-websocket` package is installed.

9. **Timezone errors**: If you see errors related to timezone handling, ensure the `tzlocal` and `pytz` packages are installed.

10. **API request errors**: The application now includes detailed debugging output for API requests. Check the console for request data and error messages.

## Limitations

- The custom wrapper implements only the basic functionality needed for CultureAI. Advanced features of the Gemini API may not be available.
- Response streaming is not implemented in the custom wrapper.
- API requests may be slightly slower than with the official SDK.

## Performance Considerations

Running large language models on a Raspberry Pi can be resource-intensive. Consider the following:

- Close other applications before running CultureAI
- Monitor CPU and memory usage
- If performance is consistently poor, consider running the application on a more powerful server and accessing it from your Raspberry Pi via the network
