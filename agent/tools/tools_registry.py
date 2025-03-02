from .read_file import read_file, TOOL_SPEC as READ_FILE_SPEC
from .write_file import write_file

# Define the tool specification for write_file
WRITE_FILE_SPEC = {
    "name": "write_file",
    "description": "Write content to a file at a specified path",
    "parameters": {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "The absolute path to the file to write"
            },
            "content": {
                "type": "string",
                "description": "The content to write to the file"
            }
        },
        "required": ["file_path", "content"]
    }
}

class ToolRegistry:
    """Registry for all MCP tools available to the agent."""
    
    def __init__(self):
        """Initialize the tool registry with all available tools."""
        self.tools = {}
        self.tool_specs = []
        
        # Register the read_file tool
        self.register_tool(
            name="read_file",
            func=read_file,
            spec=READ_FILE_SPEC
        )
        
        # Register the write_file tool
        self.register_tool(
            name="write_file",
            func=write_file,
            spec=WRITE_FILE_SPEC
        )
    
    def register_tool(self, name, func, spec):
        """
        Register a tool in the registry.
        
        Args:
            name (str): The name of the tool
            func (callable): The function to execute when the tool is called
            spec (dict): The tool specification in Gemini format
        """
        self.tools[name] = func
        self.tool_specs.append(spec)
        
    def get_tool(self, name):
        """
        Get a tool function by name.
        
        Args:
            name (str): The name of the tool
            
        Returns:
            callable: The tool function if found, None otherwise
        """
        return self.tools.get(name)
    
    def get_all_tool_specs(self):
        """
        Get all tool specifications.
        
        Returns:
            list: List of all tool specifications for the Google Generative AI model
        """
        return self.tool_specs

# Create a global instance of the tool registry
tools_registry = ToolRegistry()