# Cultural AI-Companion App Development: Architecture summary
## Core Concept:
The app features a dual-AI system:
* Main Chat AI (Main Chat LLM): Focused on engaging, high-quality conversation with the user, embodying a specific persona. It should not be burdened with auxiliary tasks.
* Asynchronous Task AI Crew (Async Task Modules): A team of smaller, specialized AI modules working in the background, in parallel, to enhance the main chat. These modules perform tasks like information extraction, conversation analysis, checklist updates, and generating system instructions.

## Key Components:
* User Interface (UI): Handles user input (text messages) and displays AI responses. Runs locally (desktop app, web app, or terminal).
* Main Chat Core: The central orchestrator:
    * Manages Chat History.
    * Handles System Instruction Injection (from Async Tasks).
    * Utilizes an Async Task Queue to trigger background tasks.
    * Includes a Timed Trigger (30-minute timer for proactive messages).
    * Manages Proactive Message Generation (when timed trigger results in an instruction).
* Main Chat LLM: The specialized LLM for the main conversation, optimized for persona and engagement. Runs locally.
* Async Task Manager: Manages the execution of asynchronous tasks:
    * Acts as a Task Queue Worker, processing jobs from the Async Task Queue.
    * Provides Error Handling for async task execution.
* Async Task Modules (LLM Pools): Specialized modules running in parallel (using smaller LLMs):
    * Information Extractor: Extracts relevant information from the Chat History.
    * Conversation Analyzer: Analyzes conversation quality and direction (using Chat History and extracted info).
    * Checklist Updater: Updates checklists based on extracted information (future feature focus).
    * Instruction Generator:
        * User Message Triggered Logic: Generates system instructions to steer the main chat based on conversation analysis.
        * Timed Trigger Logic: (Specific to 30-minute timer) Decides if and what system instruction to generate proactively when the user is inactive, aiming to re-engage or guide the conversation.

## Workflow Summary:

User Message Workflow:
1. User sends a message via UI.
2. Main Chat Core receives message, updates Chat History, and adds a "process chat history" job to the Async Task Queue.
3. Async Task Manager processes the job, running Async Task Modules sequentially (Info Extractor -> Conversation Analyzer -> Checklist Updater -> Instruction Generator).
4. Instruction Generator (User Message Logic) might generate a system instruction.
5. Main Chat Core injects the system instruction (if any) into the prompt by appending `[System instruction:...]` to the last user message in Chat History.
6. Main Chat Core sends the (potentially modified) Chat History to Main Chat LLM.
7. Main Chat LLM generates a response.
8. Main Chat Core sends response to UI and updates Chat History.

Timed Trigger (Proactive Message) Workflow (30-minute inactivity):
1. 30 minutes pass without user message. Timed Trigger in Main Chat Core fires.
2. Main Chat Core adds a "timed trigger job" to the Async Task Queue.
3. Async Task Manager processes the "timed trigger job," at least running the Instruction Generator (Timed Trigger Logic). (Optionally, other modules may run too).
4. Instruction Generator (Timed Trigger Logic) decides if a proactive system instruction is needed.
5. If an instruction is generated, it's passed to the Main Chat Core.
6. Main Chat Core (Proactive Msg Gen) constructs a prompt incorporating the system instruction and sends it to the Main Chat LLM.
7. Main Chat LLM generates a proactive response.
8. Main Chat Core immediately sends the proactive message to the UI and updates Chat History.

## Key Features and Clarifications:
* Local, Single-User, Single-Conversation App: Designed for local execution (PC, Mac, Raspberry Pi), single user, and single conversation. Scalability is not a concern.
* Different LLMs: Main Chat LLM is distinct from those used for Async Tasks (allowing for specialization).
* Async Task Queue: Decouples Main Chat Core from task execution, improving modularity.
* Error Handling: Basic error handling in Async Task Manager for robustness.
* Timed Trigger & Proactive Messages: AI can proactively initiate conversation during user inactivity based on timed intervals and Instruction Generator's logic.
* System Instruction Injection: Uses `[System instruction:...]` appended to the last user message for effective steering.
* Conversation Analyzer Dependency: Conversation Analyzer waits for Information Extractor to leverage extracted information.