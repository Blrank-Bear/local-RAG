"""Tool registry — central store for all available tools."""
from typing import Dict, Optional

from backend.tools.base import BaseTool
from backend.tools.rag_search import RAGSearchTool
from backend.tools.file_reader import FileReaderTool
from backend.tools.calculator import CalculatorTool
from backend.tools.api_caller import APICallerTool


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._register_defaults()

    def _register_defaults(self):
        for tool in [RAGSearchTool(), FileReaderTool(), CalculatorTool(), APICallerTool()]:
            self.register(tool)

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [t.schema() for t in self._tools.values()]

    async def run(self, tool_name: str, **kwargs):
        tool = self.get(tool_name)
        if not tool:
            return {"error": f"Tool '{tool_name}' not found"}
        return await tool.run(**kwargs)


# Singleton
tool_registry = ToolRegistry()
