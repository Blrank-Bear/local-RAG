"""File reader tool — reads text content from a file path."""
from pathlib import Path
from typing import Any

from backend.tools.base import BaseTool


class FileReaderTool(BaseTool):
    name = "file_reader"
    description = "Read the text content of a local file (txt or pdf)."

    async def run(self, file_path: str, max_chars: int = 4000) -> dict:
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}"}

        suffix = path.suffix.lower()
        if suffix == ".txt":
            content = path.read_text(encoding="utf-8")[:max_chars]
            return {"content": content, "source": path.name}

        if suffix == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(str(path))
                text = "\n".join(
                    page.extract_text() or "" for page in reader.pages
                )
                return {"content": text[:max_chars], "source": path.name}
            except Exception as e:
                return {"error": str(e)}

        return {"error": f"Unsupported file type: {suffix}"}
