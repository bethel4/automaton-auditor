# Automaton Auditor

Automaton Auditor is a multi-agent system for auditing code repositories and documents. Detectives collect and structure evidence; downstream judge and synthesis components will evaluate and summarize findings.

## Table of Contents

- [Features](#features)
- [Repository Layout](#repository-layout)
- [Quickstart](#quickstart)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
    - [CLI example](#cli-example)
    - [Python example](#python-example)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- Multi-agent detective nodes for repository and document analysis
- Utilities for cloning, extracting git history, and parsing PDFs
- Modular design to plug different LLM backends (see `src/llm.py`)

## Repository Layout

- `src/` — core modules (`graph.py`, `llm.py`, `state.py`)
- `nodes/` — agent implementations (e.g., `detectives.py`)
- `tools/` — helper utilities (`repo_tools.py`, `doc_tools.py`)
- `reports/` — sample and interim PDF reports
- `pyproject.toml` — project metadata and dependencies
- `.env.example` — example environment variables and API keys

## Quickstart

Clone the repository and install editable dependencies:

```bash
git clone https://github.com/<your-username>/automaton-auditor.git
cd automaton-auditor
python -m pip install -e .
```

Create and edit environment variables:

```bash
cp .env.example .env
# open .env and add your API keys/settings
```

## Configuration

- Put LLM API keys and other secrets into `.env` (example in `.env.example`).
- `src/llm.py` contains the adapter/entry points for calling an LLM provider.

## Usage Examples

### CLI example

Run a simple detective node (example script):

```bash
python -m nodes.detectives
```

### Python example

Use modules from the codebase inside a script or REPL:

```python
from src import llm
from nodes import detectives

# Example: call an llm helper (implementations depend on your provider)
# response = llm.call_model('Explain recursion in simple terms')

# Example: run detectives programmatically
# detectives.run_all()
```

Replace the commented example calls above with the appropriate function names in your local `src/llm.py` and `nodes/detectives.py` implementations.

## Development

- Tests: run `pytest` if there are tests present.
- Formatting: use `ruff`/`black` or your preferred tools.
- Add type hints and small, focused tests for new behaviors.

## Contributing

Open issues or PRs. Provide runnable repro steps and tests for non-trivial changes.

## License

Add a `LICENSE` file or consult repository settings for license details.
```
## Run the Detective Graph

```python
from src.graph import build_graph

state = {
    "repo_url": "https://github.com/example/repo",
    "pdf_path": "reports/interim_report.pdf",
    "evidences": {},
    "opinions": [],
}

graph = build_graph()
result = graph.invoke(state)

print(result["evidences"])


---

# 6️ Key Takeaways

- The core problem: **DocAnalyst was not actually running in parallel with RepoInvestigator.**
- Fix: Wire both nodes into fan-out → aggregator (fan-in).
- Optional: add `VisionInspector` in same pattern.
- Make sure conditional edges for errors exist.
- Update README to show how to invoke parallel execution.

---

