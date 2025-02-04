This is the frontend for chat between user and LLM. It is very simple to serve for prototyping.
The main div shall display the messages from AI (prefixed with "[short-formatted datetime:] AI: ") and from the user (prefixed with "[short-formatted datetime:] User: ").
Below the main div is a field where the user can sends his message and send it using the send button on the right, or with Ctrl+Enter.
Whenthe user sends a message, it gets displayed immediately in the main div, and a request to the LLM backend gets sent, which responds with the LLM's reply to the user message.
Here is the curl code for sending a request to the LLM backend:
curl -X POST http://localhost:8001/chat \
-H "Content-Type: application/json" \
-d '{
    "user_id": "user123",
    "content": "Hi AI, what is the capital of France?"
}'

At the start, the frontend requests the current chat history and loads that into the main div.