import json
from pathlib import Path
from datetime import datetime

class HistoryManager:
    def __init__(self, history_dir: str = "history"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def save_session(self, question: str, answer: str, sources: list, tag: str = "General"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_q = "".join([c if c.isalnum() else "_" for c in question[:30]])
        filename = f"{timestamp}_{safe_q}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "sources": sources,
            "tag": tag
        }

        with open(self.history_dir / filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_all_sessions(self):
        sessions = []
        for file in sorted(self.history_dir.glob("*.json"), reverse=True):
            with open(file, "r", encoding="utf-8") as f:
                sessions.append(json.load(f))
        return sessions
