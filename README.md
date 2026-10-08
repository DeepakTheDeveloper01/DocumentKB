# DocumentKB

DocumentKB is a document-aware support assistant built in Python. It searches a local Markdown knowledge base, cites the sections it uses, and keeps conversation context across questions so it can handle follow-ups and topic changes.

## Features

- Loads and chunks Markdown documents by heading.
- Ranks relevant sections with BM25-style retrieval and keyword boosts.
- Answers with citations to source documents and sections.
- Tracks conversation topics, previously covered points, and repeated information.
- Runs with built-in synthesis by default; optionally uses Groq or Anthropic for generated answers.

## Requirements

- Python 3.10 or later
- No third-party packages are required for the built-in demo mode.

## Run

From the repository root, start an interactive conversation:

```bash
python -X utf8 -m run_demo
```

Ask questions at the prompt. Enter `summary` to inspect conversation state, or `quit` to exit.

Run the scripted multi-turn demonstration instead:

```bash
python -X utf8 -m run_demo --demo
```

## Optional LLM providers

The assistant uses built-in synthesis when no provider key is configured. To enable an API-backed provider, set one of these environment variables:

- `GROQ_API_KEY` for Groq
- `ANTHROPIC_API_KEY` for Anthropic

Install the package for the provider you plan to use:

```bash
python -m pip install groq openai
```

For Anthropic, install:

```bash
python -m pip install anthropic
```

The project can load variables from a `.env` file if `python-dotenv` is installed. Otherwise, set them in your shell before starting the demo. If both provider keys are present, Anthropic is tried first.

## Knowledge base

The Markdown files in `knowledge_base/` contain the source material loaded by default. The included AcmeCloud support topics cover getting started, billing and pricing, API authentication, teams and permissions, and troubleshooting.

To use another folder of Markdown documents, pass its path when creating the assistant:

```python
from document_kb import KnowledgeAssistant

assistant = KnowledgeAssistant(kb_dir="path/to/markdown_docs")
response = assistant.ask("How do I get started?")
print(response.text)
```

`response.citations` contains the document chunks used to answer the question. The conversation state is held in memory and resets when the process exits.