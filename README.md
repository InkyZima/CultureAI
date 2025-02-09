# Cultural AI Companion

A sophisticated local AI chat application that acts as your personal cultural companion. Using a dual-AI system architecture, it provides engaging conversations about cultural topics while intelligently analyzing and adapting to your interests and needs.

## Key Features

- 🤖 Dual-AI System:
  - Main Chat AI for engaging, high-quality conversations
  - Background AI modules for intelligent analysis and personalization
- 📚 Intelligent Information Extraction:
  - Tracks cultural topics, interests, and learning progress
  - Maintains context across conversations
- 📊 Real-time Conversation Analysis:
  - Monitors engagement and conversation quality
  - Identifies areas for cultural guidance
- 🔄 Asynchronous Processing:
  - Parallel task execution for smooth user experience
  - Efficient background processing of chat analysis
- 💾 Local-first Architecture:
  - Runs entirely on your machine
  - SQLite database for secure data storage
  - No cloud dependencies (except API calls)

## Architecture

The application uses a sophisticated dual-AI architecture:

1. **Main Chat System**:
   - Focused on high-quality conversation
   - Maintains a specific persona
   - Handles direct user interaction

2. **Async Task Modules**:
   - Information Extractor: Processes chat history for relevant details
   - Conversation Analyzer: Evaluates conversation quality and progress
   - Task Manager: Orchestrates background processes
   - More modules coming soon (Instruction Generator, Checklist Manager)

## Project Status

Currently in active development (Phase 3 In Progress):

✅ Completed:
- Core chat functionality with Gradio UI
- Main Chat Core with SQLite persistence
- Async Task Manager implementation
- Information Extraction system
- Conversation Analysis system
- Basic Instruction Generator functionality

🔄 In Progress (Phase 3):
- Time-aware instruction generation
- Proactive messaging system

## Installation

1. Clone the repository:
```bash
git clone https://github.com/InkyZima/CultureAI.git
cd CultureAI
```

2. Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
   - Create a `.env` file in the project root
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

## Usage

1. Start the application:
```bash
python run.py
```

2. Open your web browser and navigate to the local Gradio interface (URL will be displayed in the console)

3. Begin chatting with your cultural AI companion!

## Project Structure

```
cultural-ai-companion/
├── src/
│   ├── main.py              # Application entry point
│   ├── main_chat_core.py    # Core chat functionality
│   └── async_modules/       # Background processing modules
│       ├── async_task_manager.py    # Task orchestration
│       ├── information_extractor.py # Cultural info extraction
│       └── conversation_analyzer.py # Conversation analysis
├── tests/                   # Test suites
├── docs/                    # Documentation
│   ├── project_plan.md      # Development roadmap
│   └── project_arch_summary.md # Architecture details
├── data/                    # Local database (created on first run)
├── requirements.txt         # Python dependencies
└── run.py                  # Application runner
```

## Requirements

- Python 3.8+
- Gradio 4.0.0+
- LangChain 0.1.0+
- Google Generative AI API key
- SQLite (included with Python)

## Development

The project follows a phased development approach:
1. ✅ Phase 1: Core Chat Functionality
2. ✅ Phase 2: Information Extraction & Analysis
3. 🔄 Phase 3: Instruction Generation & Timing
4. ⏳ Phase 4: Integration & Testing
5. ⏳ Phase 5: Optimization & Deployment

See [project_plan.md](docs/project_plan.md) for detailed development roadmap.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

[CC BY-NC 4.0]
