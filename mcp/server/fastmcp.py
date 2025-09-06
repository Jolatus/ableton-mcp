from typing import Callable, Any

class Context:
    """A mock context class."""
    def get(self, key: str) -> Any:
        return None

class FastMCP:
    """A mock FastMCP server class."""
    def __init__(self, name: str, lifespan: Any = None):
        self.name = name
        self.lifespan = lifespan

    def tool(self):
        def decorator(f: Callable) -> Callable:
            return f
        return decorator

    def run(self, transport: str, port: int):
        print(f"Mock run of {self.name} on {port} with {transport}")
