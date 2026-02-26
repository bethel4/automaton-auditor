# Automaton Auditor

Automaton Auditor is a production-grade multi-agent system for autonomous code governance. It implements the **Digital Courtroom** paradigm using LangGraph, where specialized detective agents collect forensic evidence, dialectical judges debate findings, and a Chief Justice synthesizes final verdicts.

## 🏛️ Architecture: The Digital Courtroom

### Layer 1: Detective Agents (Forensic Sub-Agents)
- **RepoInvestigator**: Git forensic analysis, AST parsing, security assessment
- **DocAnalyst**: PDF parsing, theoretical depth analysis, cross-referencing  
- **VisionInspector**: Multimodal diagram analysis (framework ready)

### Layer 2: Judicial Bench (Dialectical Synthesis)
- **Prosecutor**: Adversarial analysis - "Trust No One, Assume Vibe Coding"
- **Defense**: Optimistic analysis - "Reward Effort and Intent"
- **Tech Lead**: Pragmatic analysis - "Does it actually work?"

### Layer 3: Chief Justice (Deterministic Synthesis)
- Security Override: Confirmed flaws cap scores at 3
- Fact Supremacy: Forensic evidence overrules judicial opinion
- Functionality Weight: Tech Lead assessment carries highest weight
- Dissent Requirement: High variance triggers explicit dissent documentation

## 🚀 Quick Start

### Prerequisites
- Python 3.10-3.12
- uv package manager
- OpenAI/X.AI API key

### Installation

```bash
# Clone the repository
git clone https://github.com/bethel4/automaton-auditor.git
cd automaton-auditor

# Install dependencies with uv
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Configuration

```bash
# .env file
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.x.ai/v1  # For Grok models
LANGCHAIN_TRACING_V2=true  # Optional: LangSmith tracing
LANGSMITH_API_KEY=your_langsmith_key_here  # For LangSmith tracing
```

## 📖 Usage

### Command Line Interface

```bash
# Run a complete audit
python test_complete_graph.py

# The script will:
# 1. Clone and analyze the target repository
# 2. Parse and evaluate the PDF report
# 3. Run parallel detective and judge agents
# 4. Generate a comprehensive audit report
```

### Basic Audit (Python API)

```python
from src.graph import build_graph

# Initialize audit state
state = {
    "repo_url": "https://github.com/username/repository",
    "pdf_path": "path/to/report.pdf",
    "rubric_dimensions": [],  # Auto-populated
    "evidences": {},
    "opinions": [],
    "final_report": None,
}

# Run the Digital Courtroom
graph = build_graph()
result = graph.invoke(state)

# Access the audit report
print(result["markdown_report"])
```

## 📁 Repository Structure

```
automaton-auditor/
├── src/
│   ├── state.py              # Pydantic models and TypedDict state
│   ├── graph.py              # Complete StateGraph with parallel orchestration
│   ├── llm.py                # LLM adapter for OpenAI/Grok
│   ├── context_manager.py    # Sandbox cleanup and signal handling
│   └── nodes/
│       ├── detectives.py     # Forensic evidence collection
│       ├── judges.py         # Dialectical judicial personas
│       └── justice.py        # Chief Justice synthesis engine
├── tools/
│   ├── repo_tools.py         # Sandboxed git operations and AST parsing
│   └── doc_tools.py          # PDF ingestion and analysis
├── rubric.json               # Machine-readable evaluation rubric
├── reports/
│   └── interim_report.md     # Architecture documentation
├── test_complete_graph.py    # End-to-end test script
├── pyproject.toml            # Dependencies and project config
└── .env.example              # Environment variables template
```

## 🔧 Key Features

### ✅ Production-Grade Infrastructure
- **Typed State Management**: Pydantic models with reducers prevent data races
- **Parallel Orchestration**: True fan-out/fan-in patterns for scalability
- **Safe Tool Engineering**: Sandboxed git operations with proper error handling
- **Structured Output**: LLM responses validated against Pydantic schemas

### ✅ Dialectical Synthesis
- **Distinct Personas**: Three conflicting judicial philosophies
- **Parallel Processing**: Judges analyze evidence independently
- **Deterministic Resolution**: Hardcoded rules, not LLM averaging
- **Dissent Documentation**: High variance triggers explicit explanations

### ✅ Forensic Protocols
- **Git Analysis**: Commit history, progression patterns, atomic development
- **AST Parsing**: Structural verification of LangGraph implementations
- **Security Assessment**: Tool safety, sandboxing, input validation
- **Cross-Reference**: PDF claims vs. repository reality verification

## 📊 Evaluation Rubric

The system evaluates submissions across 10 dimensions:

1. **Git Forensic Analysis** - Commit quality and progression
2. **State Management Rigor** - Pydantic models and reducers
3. **Graph Orchestration** - Parallel architecture patterns
4. **Safe Tool Engineering** - Security and sandboxing
5. **Structured Output Enforcement** - LLM validation
6. **Judicial Nuance** - Persona separation and dialectics
7. **Chief Justice Synthesis** - Deterministic conflict resolution
8. **Theoretical Depth** - Documentation quality
9. **Report Accuracy** - Cross-referencing claims vs. reality
10. **Swarm Visual** - Architectural diagram correctness

## 🧪 Testing

```bash
# Run the complete test suite
python test_complete_graph.py

# The test demonstrates:
# - Parallel detective evidence collection
# - Dialectical judicial analysis
# - Chief Justice synthesis
# - Markdown report generation
```

## 🔍 Debugging & Observability

### LangSmith Tracing
Enable LangSmith for detailed execution tracing:
```bash
# .env file
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT="automaton-auditor"
```

LangSmith provides:
- 🏛️ **Digital Courtroom Visualization**: See the complete workflow
- 🔍 **Agent Tracking**: Each detective, judge, and Chief Justice step
- 📊 **Performance Metrics**: Token usage, latency, error rates
- 🐛 **Debug Insights**: Exact prompts and responses
- 📈 **Execution Flow**: Parallel processing and fan-out/fan-in patterns

### Error Handling
The system includes comprehensive error handling:
- Conditional edges for missing evidence/opinions
- Graceful degradation when components fail
- Detailed error messages in audit reports

## 🤝 Contributing

This is a Week 2 FDE Challenge submission. The system is designed for:
- Peer-to-peer auditing
- MinMax optimization loops
- Autonomous governance at scale

## 📜 License

MIT License - see LICENSE file for details.

## 🏆 Challenge Compliance

✅ **All Mandatory Requirements Met:**
- Hierarchical StateGraph with parallel execution
- Dialectical synthesis with distinct personas
- Deterministic Chief Justice with conflict resolution
- Forensic evidence collection protocols
- Safe tool engineering with sandboxing
- Structured output enforcement
- Machine-readable rubric integration
- Production-grade error handling

The Digital Courtroom is ready for peer auditing and the MinMax feedback loop.

