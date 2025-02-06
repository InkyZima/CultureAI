# Cultural AI-Companion App Development: Project Plan

**1. Project Goal and Scope:**

*   **Goal:** To develop a local, single-user AI chat application that acts as a cultural AI-companion. This companion will engage in daily conversations with the user, provide cultural guidance, and proactively offer reminders and suggestions related to cultural practices.
*   **Scope:**
    *   Single-user application.
    *   Single-conversation focus (one ongoing chat history).
    *   Runs locally (PC, Mac, Raspberry Pi - no cloud hosting).
    *   Implements the defined architecture with a Main Chat Core, Main Chat LLM, Async Task Manager, and Async Task Modules (Information Extractor, Conversation Analyzer, Checklist Updater - future, Instruction Generator).
    *   Focus on core functionality: Main chat, information extraction, conversation analysis, proactive instruction generation (timed and user-triggered), basic error handling.
    *   Initial checklist management is out of scope for the first version but considered for future expansion.
    *   Maintain a modular architecture with clear interfaces.
    *   Utilize containerization (if needed for deployment consistency) and virtual environments.

**2. Development Phases:**

The project will be divided into the following phases:

*   **Phase 1: Project Setup and Core Chat Functionality**
*   **Phase 2: Async Task Modules - Information Extraction & Conversation Analysis**
*   **Phase 3: Async Task Modules - Instruction Generation & Timed Trigger Logic**
*   **Phase 4: Integration, Proactive Messages & End-to-End Testing**
*   **Phase 5: Refinement, Optimization & Raspberry Pi Deployment (Optional)**

**3. Phase Breakdown and To-Do Lists:**

**Phase 1: Project Setup and Core Chat Functionality**

*   **Objective:**  Establish the basic application structure, UI, and core chat communication between the user and the Main Chat LLM.
*   **Aspects to Consider:**
    *   **Development Environment Setup:** Python virtual environment setup. Install necessary libraries including Gradio, LangChain, and LLM libraries.
    *   **UI Framework Implementation (Gradio):** Set up Gradio for the user interface, leveraging its chat-specific components for input and message display. Design the basic chat interface.
    *   **Main Chat Core Structure:** Implement the basic class/module for `MainChatCore`, handling chat history using SQLite for persistence.
    *   **Main Chat LLM Integration (LangChain):** Choose a suitable Main Chat LLM and integrate it into the `MainChatCore` using LangChain for managing LLM interactions. Focus on basic text in/text out.
    *   **Basic Chat Flow Implementation:** Implement the flow: User input -> `MainChatCore` -> `MainChatLLM` (via LangChain) -> `MainChatCore` -> UI display (Gradio).
*   **To-Do List (Phase 1):**
    1.  **Set up Python virtual environment.**
    2.  **Install Gradio UI framework and LangChain library.**
    3.  **Design and implement basic chat UI using Gradio (input, display).**
    4.  **Create `MainChatCore` class/module (initial structure).**
    5.  **Select and download a suitable Main Chat LLM model.**
    6.  **Integrate Main Chat LLM with `MainChatCore` using LangChain for interaction.**
    7.  **Implement SQLite database for chat history persistence.**
    8.  **Implement basic chat message flow (user -> AI -> display) using Gradio and LangChain.**
    9.  **Basic testing of core chat functionality.**
*   **Deliverables (Phase 1):**
    *   Functional basic chat application with Gradio UI and Main Chat LLM integration via LangChain.
    *   Basic `MainChatCore` class/module structure.
    *   SQLite database implementation for persistent chat history.
    *   Codebase with basic chat functionality.
    *   Phase 1 completed and tested.
    *   **Technology/Tools (Phase 1):** Python, Virtual Environment, Gradio, LangChain, SQLite, chosen Main Chat LLM model.

**Phase 2: Async Task Modules - Information Extraction & Conversation Analysis**

*   **Objective:** Implement the first two Async Task Modules: Information Extractor and Conversation Analyzer, and the Async Task Manager to orchestrate them using `asyncio`.
*   **Aspects to Consider:**
    *   **Database Integration:** Leverage existing SQLite database for efficient querying of chat history by Information Extractor and Conversation Analyzer modules.
    *   **Async Task Manager Implementation:**  Create `AsyncTaskManager` class/module, implement task queue using `asyncio.Queue` and worker logic using `asyncio`.
    *   **Information Extractor Module (LangChain):** Design and implement `InformationExtractor` module. Choose a suitable smaller LLM and integrate it using LangChain. Implement logic to extract relevant information from chat history using SQLite queries.
    *   **Conversation Analyzer Module (LangChain):** Design and implement `ConversationAnalyzer` module. Choose a suitable smaller LLM and integrate it using LangChain. Implement logic to analyze conversation (using SQLite queries and output from `InformationExtractor`).
    *   **Data Passing between Modules:** Ensure proper data flow from `InformationExtractor` to `ConversationAnalyzer` within the `AsyncTaskManager`.
    *   **Triggering Async Tasks (User Message):** Implement the mechanism in `MainChatCore` to add "process chat history" jobs to the Async Task Queue after each user message.
*   **To-Do List (Phase 2):**
    1.  **Create `AsyncTaskManager` class/module (task queue using `asyncio.Queue`, worker using `asyncio`).**
    2.  **Implement `InformationExtractor` module (choose LLM, extraction logic) using LangChain.**
    3.  **Implement `ConversationAnalyzer` module (choose LLM, analysis logic, dependency on `InformationExtractor`) using LangChain.**
    4.  **Implement data passing between `InformationExtractor` and `ConversationAnalyzer` in `AsyncTaskManager`.**
    5.  **Modify `MainChatCore` to trigger async tasks via Async Task Queue after user messages.**
    6.  **Integrate `AsyncTaskManager` with `MainChatCore`.**
    7.  **Testing of Information Extraction and Conversation Analysis workflows.**
*   **Deliverables (Phase 2):**
    *   Implemented `AsyncTaskManager` (using `asyncio`), `InformationExtractor` (using LangChain), and `ConversationAnalyzer` (using LangChain) modules.
    *   Asynchronous task processing triggered by user messages.
    *   Basic information extraction and conversation analysis functionality.
    *   Phase 2 components integrated and tested.
*   **Technology/Tools (Phase 2):** Python, `asyncio`, LangChain, chosen LLMs for Information Extraction and Conversation Analysis.

**Phase 3: Async Task Modules - Instruction Generation & Timed Trigger Logic**

*   **Objective:** Implement the Instruction Generator module, including both user-triggered and timed trigger logic. Implement basic error handling using Loguru and retry mechanism using tenacity in `AsyncTaskManager`. Integrate AsyncIO for timed tasks.
*   **Aspects to Consider:**
    *   **Instruction Generator Module (User-Triggered Logic - LangChain):** Design and implement `InstructionGenerator` module for user message triggered instructions using LangChain. Choose a suitable smaller LLM. Implement logic to generate system instructions based on `ConversationAnalyzer` output.
    *   **Instruction Generator Module (Timed Trigger Logic - LangChain & AsyncIO):** Implement the "Timed Trigger Logic" within `InstructionGenerator` using LangChain for LLM interaction and AsyncIO for scheduling the timed trigger. Design logic for proactive instruction generation in periods of user inactivity.
    *   **Timed Trigger Implementation (AsyncIO & MainChatCore):** Implement the 30-minute timer in `MainChatCore` using AsyncIO to trigger "timed trigger jobs" in the `Async Task Queue`. Add the `ProactiveTrigger` class to handle timer resets on user activity.
    *   **Proactive Message Generation Logic (MainChatCore):** Implement the `ProactiveMsgGen` component in `MainChatCore` to handle system instructions from timed triggers and generate proactive AI messages.
    *   **Error Handling in Async Task Manager (Loguru & tenacity):** Implement robust error handling in `AsyncTaskManager` using Loguru for logging and tenacity for retry mechanisms for transient errors during LLM calls or task execution. Apply retry policies per-module (e.g., 3 retries for `InformationExtractor`, 5 retries for `ConversationAnalyzer`).
*   **To-Do List (Phase 3):**
    1.  **Implement `InstructionGenerator` module (user-triggered logic, choose LLM, instruction logic based on `ConversationAnalyzer`) using LangChain.**
    2.  **Implement "Timed Trigger Logic" within `InstructionGenerator` (proactive instruction generation logic) using LangChain and AsyncIO.**
    3.  **Implement 30-minute timer in `MainChatCore` using AsyncIO and trigger "timed trigger jobs".**
    4.  **Implement `ProactiveTrigger` class in `MainChatCore` to handle timer resets on user activity.**
    5.  **Implement `ProactiveMsgGen` component in `MainChatCore` to handle timed trigger instructions and generate proactive messages.**
    6.  **Implement error handling in `AsyncTaskManager` using Loguru for logging and tenacity for retry.**
    7.  **Integrate `InstructionGenerator` with `AsyncTaskManager` and `MainChatCore`.**
    8.  **Testing of Instruction Generation (user-triggered and timed), and error handling.**
*   **Deliverables (Phase 3):**
    *   Implemented `InstructionGenerator` module with both user-triggered and timed logic using LangChain and AsyncIO.
    *   Timed trigger mechanism and proactive message generation using AsyncIO.
    *   Robust error handling and logging in `AsyncTaskManager` using Loguru and tenacity.
    *   Phase 3 components integrated and tested.
*   **Technology/Tools (Phase 3):** Python, `asyncio`, LangChain, Loguru, tenacity, chosen LLM for Instruction Generation.

**Phase 4: Integration, Proactive Messages & End-to-End Testing**

*   **Objective:** Integrate all components, implement system instruction injection, refine proactive message flow, and conduct thorough end-to-end testing.
*   **Aspects to Consider:**
    *   **System Instruction Injection Implementation:** Implement the logic in `MainChatCore` to inject system instructions by appending `[System instruction:...]` to the last user message in the Chat History before sending to `MainChatLLM` via LangChain.
    *   **Refine Proactive Message Flow (Gradio UI Integration):** Ensure smooth flow of proactive messages initiated by the timed trigger, properly displayed in the Gradio UI and recorded in Chat History.
    *   **End-to-End Testing (All Workflows):** Test all workflows: User message -> async tasks -> instruction injection -> AI response, and Timed Trigger -> proactive message generation. Test error handling scenarios, including those handled by tenacity.
    *   **Usability Testing (Basic - Gradio UI):**  Initial user testing to evaluate basic usability and conversation flow within the Gradio UI.
    *   **Configuration and Basic Setup:**  Implement basic configuration options (e.g., choosing LLM models via LangChain, setting timer intervals via AsyncIO - if configurable).
*   **To-Do List (Phase 4):**
    1.  **Implement system instruction injection in `MainChatCore` for LangChain interactions.**
    2.  **Refine the proactive message generation flow and UI display within Gradio.**
    3.  **Conduct comprehensive end-to-end testing of all workflows (user-message triggered, timed-triggered, error cases, tenacity retries).**
    4.  **Perform basic usability testing with Gradio UI and gather initial feedback.**
    5.  **Implement basic configuration options (e.g., LLM selection via LangChain, timer interval via AsyncIO).**
    6.  **Address and fix bugs identified during testing.**
*   **Deliverables (Phase 4):**
    *   Fully integrated AI Chat application with all core functionalities implemented using specified technologies.
    *   Functional system instruction injection and proactive message generation.
    *   Application thoroughly tested (end-to-end and basic usability).
    *   Basic configuration options.
    *   Phase 4 completed and tested; application ready for initial deployment/refinement.

**Phase 5: Refinement, Optimization & Raspberry Pi Deployment (Optional)**

*   **Objective:** Refine the application based on testing feedback, optimize for performance (especially for Raspberry Pi if targeted), and prepare for deployment. Consider containerization for consistent local deployment if needed.
*   **Aspects to Consider:**
    *   **Performance Optimization:** Profile the application for performance bottlenecks, optimize code, consider model quantization or smaller models for Raspberry Pi compatibility. Leverage LangChain's model management if helpful.
    *   **Refinement based on Testing Feedback:** Address any usability issues within Gradio UI, refine conversation flow, improve error handling, and enhance overall user experience based on testing in Phase 4.
    *   **Raspberry Pi Deployment Preparation (if desired):**  Test application on Raspberry Pi, optimize for resource constraints, create deployment instructions, consider containerization (Docker) for easier deployment if needed.
    *   **Documentation (Basic):** Create basic user and developer documentation.
*   **To-Do List (Phase 5):**
    1.  **Performance profiling and optimization (focus on Raspberry Pi if targeting it).**
    2.  **Address usability issues and refine conversation flow based on testing feedback within Gradio.**
    3.  **Enhance error handling and logging based on testing, refine tenacity retry strategies if necessary.**
    4.  **Test and optimize application specifically on Raspberry Pi (if applicable), consider containerization for deployment.**
    5.  **Create basic user and developer documentation.**
    6.  **Final testing and bug fixing.**
*   **Deliverables (Phase 5):**
    *   Optimized and refined AI Chat application using specified technologies.
    *   Application tested and functional on Raspberry Pi (if targeted), potentially containerized for deployment.
    *   Basic user and developer documentation.
    *   Final deliverable: Ready-to-deploy Cultural AI-Companion App.
*   **Technology/Tools (Phase 5):** Python profiling tools, optimization libraries, Raspberry Pi (for testing), Docker (optional containerization), documentation tools (Markdown, etc.).

**4. Overall Project Aspects (Across all Phases):**

*   **LLM Selection and Fine-tuning (LangChain):** Continuously evaluate and refine the Main Chat LLM and smaller LLMs used for Async Tasks, managed with LangChain.  Consider fine-tuning for persona, cultural knowledge, and specific task performance. Data collection for fine-tuning might be needed.
*   **Testing and Evaluation Strategy:** Implement unit tests for modules, integration tests for workflows, and end-to-end testing for overall application functionality. Define metrics for evaluating conversation quality and cultural guidance effectiveness (qualitative assessment initially).
*   **Modular Architecture and Clear Interfaces:** Emphasize modular design throughout development, ensuring clear interfaces between components for maintainability and scalability.
*   **Environment Setup and Version Control:**  Establish consistent development environment setup instructions using virtual environments. Utilize Git for version control throughout the project.
*   **Cultural Knowledge Integration:**  Consider how cultural knowledge will be integrated – into the Main Chat LLM fine-tuning, into the prompts for Async Tasks (managed with LangChain), or as a separate knowledge base accessed by the modules.

**5. Timeline (Rough Estimates - Highly Variable):**

*   **Phase 1: Project Setup and Core Chat Functionality:** 2-4 weeks
*   **Phase 2: Async Task Modules - Information Extraction & Conversation Analysis:** 3-5 weeks
*   **Phase 3: Async Task Modules - Instruction Generation & Timed Trigger Logic:** 4-6 weeks
*   **Phase 4: Integration, Proactive Messages & End-to-End Testing:** 2-4 weeks
*   **Phase 5: Refinement, Optimization & Raspberry Pi Deployment (Optional):** 1-3 weeks (optional, depending on goals)

**Total Estimated Time: 12-22 weeks (or longer, depending on complexity, resources, and learning curve).**

**Important Notes:**

*   This timeline and phase breakdown are estimates. Actual time may vary based on your familiarity with the technologies, complexity of the LLM tasks, and debugging efforts.
*   Start with Phase 1 and iterate. Focus on getting each phase working well before moving to the next.
*   Prioritize core functionality first. Checklist management and advanced UI features can be considered for future iterations.
*   Regularly test and evaluate the application throughout development to identify issues early.