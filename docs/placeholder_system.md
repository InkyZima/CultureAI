# Placeholder System Documentation

## Overview

The placeholder system allows you to create dynamic prompt templates with variables that are automatically replaced at runtime. This enables more flexible agent prompts that can adapt to different contexts without modifying the core code.

## Available Placeholders

The following placeholders are currently supported in all prompt templates:

| Placeholder | Description |
|-------------|-------------|
| `{timestamp}` | Current time in ISO format |
| `{chat_history}` | Recent conversation history between user and assistant |
| `{unconsumed_injections}` | List of pending injections not yet consumed |

## Using Placeholders in Templates

1. Create a new template file in the `system_prompts` directory
2. Insert placeholders in the template text using the format `{placeholder_name}`
3. Run the agent with your template using the command-line options

Example template:
```
Current time: {timestamp}

Chat history:
{chat_history}

Pending instructions:
{unconsumed_injections}

Your custom instructions here...
```

## Running the Agent with a Custom Template

Use the `--template` option in the `run_agent_chain_manually.py` script:

```bash
python run_agent_chain_manually.py --template your_template.txt
```

## Adding New Placeholders

To add a new placeholder:

1. Open `agent/placeholder_handler.py`
2. Add a new handler function in the `PlaceholderHandler` class
3. Register the new placeholder in the constructor's `handlers` dictionary

Example:
```python
def _handle_your_placeholder(self) -> str:
    """Return the value for your placeholder."""
    # Your implementation here
    return "Your placeholder value"

# In the __init__ method, add:
self.handlers["your_placeholder"] = self._handle_your_placeholder
```

## Advanced Usage

### Programmatic Access

You can also use the placeholder system programmatically:

```python
from agent.placeholder_handler import process_template

# Process a template string
template = "Time: {timestamp}"
processed = process_template(template)
```

### Custom Placeholder Registration

Register custom placeholders at runtime:

```python
from agent.placeholder_handler import register_custom_placeholder

register_custom_placeholder("custom_value", lambda: "Your dynamic value")
```

## Best Practices

1. Keep templates modular and focused on specific use cases
2. Avoid hardcoding dynamic values that could be represented as placeholders
3. Use descriptive placeholder names
4. Document new placeholders as they are added
