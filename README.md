# Automaton Auditor – Interim Submission

**Multi-Agent Judicial Code Audit System (Week 2 – TRP1 Challenge)**

This repository contains the interim implementation of the **Automaton Auditor**, a multi-agent system that evaluates a GitHub repository and PDF report using a forensic, dialectical process. It implements **Detective agents** for evidence collection, prepares structured evidence, and sets the stage for Judge nodes and the Chief Justice synthesis engine.

---

## 📁 Repository Structure
automaton-auditor/
│
├── src/
│ ├── state.py # Pydantic/TypedDict state definitions with reducers
│ ├── graph.py # Partial StateGraph wiring: Detectives fan-out & EvidenceAggregator fan-in
│ ├── tools/
│ │ ├── repo_tools.py # Sandboxed git clone, git log extraction, AST-based graph analysis
│ │ └── doc_tools.py # PDF ingestion and chunked querying (RAG-lite)
│ ├── nodes/
│ │ └── detectives.py # RepoInvestigator and DocAnalyst LangGraph nodes
│
├── reports/
│ └── interim_report.pdf # PDF report committed for peer review
│
├── pyproject.toml # Dependencies managed via uv
├── .env.example # Example environment variables and API keys
└── README.md # This document

---

# Automaton Auditor

Automaton Auditor is an interim multi-agent system for repository and document auditing. It includes detective nodes that gather evidence from code repositories and reports to support downstream judgement and synthesis components.

## Repository layout

- `src/` — core modules: `graph.py`, `llm.py`, `state.py`
- `nodes/` — agent implementations (e.g., `detectives.py`)
- `tools/` — helper utilities (`repo_tools.py`, `doc_tools.py`)
- `reports/` — sample and interim PDF reports
- `pyproject.toml` — project metadata and dependencies
- `.env.example` — example environment variables and API keys

## Prerequisites

- Python 3.11 or newer
- Git
- An LLM API key (if you plan to use `src/llm.py` with a provider such as Grok)

## Quick setup

Clone and install:

```bash
git clone https://github.com/<your-username>/automaton-auditor.git
cd automaton-auditor
python -m pip install -e .
```

Create your environment variables:

```bash
cp .env.example .env
# Edit .env and add your API keys and settings
```


## License

See the repository settings or add a LICENSE file.