# Local Perplex

Local Perplex is a Python web and CLI research assistant that combines web search,
local documents, Ollama synthesis, and a growing local GraphMap memory.

## What It Does

- Searches the web and ranks sources with a pure-Python ranking core.
- Uses Ollama for local answer synthesis when Ollama is running.
- Reads local documents from `documents/` for private RAG context.
- Stores completed research, sources, documents, terms, and relationships in a
  SQLite GraphMap at `graph/knowledge_graph.sqlite3`.
- Reuses GraphMap memory in future prompts so repeated use can improve answers
  over time.
- Keeps incognito searches out of history and GraphMap storage.

## Requirements

- Python 3.10+
- Ollama for answer generation
- A pulled Ollama model, for example:

```powershell
ollama pull llama3.2-vision
```

## Install

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
```

## Run

Start Ollama first:

```powershell
ollama serve
```

Then run the web app:

```powershell
perplex-gui
```

Open:

```text
http://localhost:8000
```

You can also run the compatibility wrapper directly:

```powershell
python ui\web\app.py
```

CLI usage:

```powershell
perplex "What is retrieval augmented generation?"
```

## GraphMap

The GraphMap is a local SQLite knowledge graph. Each completed non-incognito
research session adds nodes for questions, sources, terms, tags, and research
answers. Uploaded documents add document and term nodes. Future research queries
retrieve related graph context and include it before synthesis.

View it in the web app:

```text
http://localhost:8000/graph
```

Or inspect JSON:

```text
http://localhost:8000/api/graph
```

## Testing

```powershell
python -B -m pytest -q -p no:cacheprovider
```

`-B` and `-p no:cacheprovider` keep the test run from writing bytecode and
pytest cache files.

## Troubleshooting

If the web app loads but answers do not stream, check Ollama:

```powershell
curl http://localhost:11434/api/tags
```

If no models are returned, pull one:

```powershell
ollama pull llama3.2-vision
```

If you are running from source, prefer:

```powershell
perplex-gui
```

or:

```powershell
python ui\web\app.py
```
