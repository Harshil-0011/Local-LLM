import os
from pathlib import Path

class DocumentManager:
    def __init__(self, doc_dir: str = "documents"):
        self.doc_dir = Path(doc_dir)
        self.doc_dir.mkdir(parents=True, exist_ok=True)

    def get_local_context(self):
        context = []
        for file in self.doc_dir.glob("*"):
            ext = file.suffix.lower()
            if ext in [".txt", ".md"]:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        content = f.read()
                        context.append(f"Local File: {file.name}\nContent: {content[:2500]}")
                except Exception: continue
            elif ext == ".pdf":
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(file)
                    content = ""
                    for i in range(min(5, len(reader.pages))): # Read first 5 pages
                        content += reader.pages[i].extract_text() + " "
                    context.append(f"Local PDF: {file.name}\nContent: {content[:3000]}")
                except Exception: continue
        return "\n\n".join(context)

    def add_document(self, filename: str, content: str):
        with open(self.doc_dir / filename, "w", encoding="utf-8") as f:
            f.write(content)
