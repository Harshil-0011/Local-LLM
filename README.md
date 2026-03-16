# Local Perplex — The Definitive Local AI Researcher

Local Perplex is a high-performance, privacy-first alternative to Perplexity AI. It combines a high-speed **C++ Core** for relevance ranking with **Ollama** for state-of-the-art LLM synthesis, providing a premium research experience entirely on your local machine.

## 🚀 Why Local Perplex?
- **Extreme Privacy**: Your queries and research data never leave your computer.
- **C++ Performance**: Heavy-duty text processing and source ranking are handled by a native C++ engine.
- **Premium UI**: Minimalist, stunning interface inspired by Apple, Nothing, and Google.
- **Deep Research**: Simultaneously analyzes 20+ sources to build exhaustive reports.
- **Local RAG**: Seamlessly integrates your private `.txt` and `.md` files into any research session.

## ✨ Key Features
- **Visual Research**: Upload images to research based on visual context.
- **AI Query Refinement**: Intelligently optimizes your research questions into professional search queries.
- **Knowledge Vault**: Manage and research your private documents (.txt, .md) with ease.
- **Conversational Research**: Ask follow-up questions to drill deeper into any topic.
- **Dual Research Modes**:
  - `Industry Standard`: Fast, focused, and concise synthesis.
  - `All References`: Deep-dive analysis with exhaustive citations.
- **History & Export**: Auto-save every research session and export to professional Markdown.
- **Related Suggestions**: Intelligently suggests the next steps for your research.

## 🛠 Installation (Windows)

### 1. Prerequisites
- **Python 3.10+**: [Download here](https://www.python.org/)
- **Ollama**: [Download here](https://ollama.com/)
- **C++ Build Tools**: Install [Visual Studio Community](https://visualstudio.microsoft.com/vs/community/) with "Desktop development with C++".

### 2. Setup Ollama
Pull the recommended research model:
```bash
ollama pull llama3.2:8b
```

### 3. Build & Install
```bash
# Build the C++ High-Performance Core
mkdir build
cd build
cmake ..
cmake --build . --config Release

# Install Python dependencies
cd ..
pip install -r requirements.txt
```

## 💻 Usage

### Launch the Premium Web Interface
```bash
perplex-gui
```
Visit `http://localhost:8000` to start your first research session.

### Terminal Interface (Power User)
```bash
perplex "What are the latest breakthroughs in solid-state battery technology?" --mode all_references
```

## 📂 Project Structure
- `src/`: Native C++ Core for ranking and processing.
- `local_perplex/`: Python orchestration and UI layer.
- `documents/`: Your private RAG folder. Drop files here to research them.
- `history/`: Persistent storage of your research sessions.

---
*Built for the privacy-conscious researcher. Better than Perplexity, in every way.*
