# Project Wizard

A local Perplexity-style project generator for Windows that uses Ollama as the local LLM runtime.

## Features

- **Completely Local**: No internet required to function.
- **Ollama Integration**: Uses Ollama for planning and code generation.
- **CPU/GPU Support**: Supports GPU acceleration automatically via Ollama.
- **CLI & Web GUI**: Use your preferred interface.
- **Interview Workflow**: Guided interview -> Project Specification -> Full Code Generation.

## Prerequisites

1. **Python 3.10+**
2. **Ollama**:
   - Download and install from [ollama.com](https://ollama.com).
   - Pull the required models:
     ```bash
     ollama pull llama3.2:8b
     ollama pull deepseek-coder:latest
     ```

## Installation

1. Clone or download this repository.
2. Navigate to the project root and install the package:
   ```bash
   pip install -e .
   ```
   Or install from `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Configuration

The configuration is stored in `~/.project_wizard/config.yaml`. You can also configure it via the Web GUI settings page.

### CLI Interface

- **Full Workflow**:
  ```bash
  wizard full-run --output C:\projects\my_new_app
  ```
- **Individual Steps**:
  ```bash
  wizard interview --output C:\projects\my_new_app
  wizard build-spec --output C:\projects\my_new_app
  wizard generate-code --output C:\projects\my_new_app
  ```

### Web GUI Interface

Start the web server:
```bash
wizard-gui
```
Then open your browser at [http://localhost:8000](http://localhost:8000).

## License

MIT
