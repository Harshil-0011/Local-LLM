# Local Perplex

A completely local alternative to Perplexity AI, better in every way (privacy, performance, customization).

## Features
- **C++ Core**: High-performance relevance ranking and text processing.
- **Python Orchestration**: Flexible engine using Ollama.
- **20 Sources**: Comprehensive searching using DuckDuckGo.
- **Industry Standard vs All References**: Choose your level of detail.
- **Web & CLI Interfaces**: Flexible usage.

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
