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
INJECTION_INTERVAL=12
NTFY_TOPIC=your_ntfy_topic_here
```

Replace `your_google_api_key_here` with your actual Google API key.

### 5. Run the application

```bash
python app.py
```

## How it works

This version of CultureAI has been modified to be compatible with Python 3.7 on Raspberry Pi:

1. **Custom Gemini API Wrapper**: Since the official `google-generativeai` package requires Python 3.9+, we've created a custom wrapper using HTTP requests to directly access the Gemini API.

2. **Fallback Mechanism**: The code will try to import the official SDK first, and if that fails, it will use our custom wrapper automatically.

3. **Compatible Dependencies**: The requirements.txt file has been updated to use versions that are compatible with Python 3.7.

## Troubleshooting

If you encounter any issues:

1. **Connection issues**: Make sure your API key is correct and that your Raspberry Pi has internet access.

2. **ImportError**: Ensure that all dependencies are installed correctly.

3. **Performance**: The application may run slower on a Raspberry Pi compared to more powerful hardware. This is normal.

4. **Log files**: Check the log files for detailed error messages if the application doesn't start properly.

## Limitations

- The custom wrapper implements only the basic functionality needed for CultureAI. Advanced features of the Gemini API may not be available.
- Response streaming is not implemented in the custom wrapper.

## Performance Considerations

Running large language models on a Raspberry Pi can be resource-intensive. Consider the following:

- Close other applications before running CultureAI
- Monitor CPU and memory usage
- If performance is consistently poor, consider running the application on a more powerful server and accessing it from your Raspberry Pi via the network.
