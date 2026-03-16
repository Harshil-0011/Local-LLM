# Local Perplex — Premium Private Search

A completely local alternative to Perplexity AI, better in every way. Private, stunningly minimal, and high-performance.

## Premium Features
- **Minimalist Design**: A premium UI inspired by Apple, Nothing, and Google.
- **C++ Core**: High-performance relevance ranking and text processing.
- **Research History**: Save and revisit your research sessions.
- **Dual Research Modes**:
  - *Industry Standard*: Concise, focused synthesis.
  - *All References*: Deep, exhaustive detail with every possible citation.
- **Ollama Integration**: Runs completely on your machine using local LLMs.
- **20+ Sources**: Deep research powered by high-relevance web scraping.

## Installation (Windows)
1. **Ollama**: Install and pull `llama3.2:8b`.
2. **Build C++ Core**:
   ```bash
   mkdir build
   cd build
   cmake ..
   make
   ```
3. **Install Python Deps**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
### CLI
```bash
python -m local_perplex.ui.cli "Where do you think LLM will move towards in future please??"
```

### Web
```bash
python -m local_perplex.ui.web.app
```
Visit http://localhost:8000
