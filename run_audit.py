#!/usr/bin/env python
# run_audit.py

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# LOAD ENV ONCE - AT THE VERY TOP
_root = Path(sys.argv[0]).resolve().parent if sys.argv else Path.cwd()
env_path = _root / '.env'
print(f"📂 .env path: {env_path} (exists: {env_path.exists()})")
load_dotenv(dotenv_path=env_path, override=True)
# Fallback: if dotenv didn't load LANGCHAIN_* / LANGSMITH_*, parse .env manually (handles encoding/line endings)
if not os.environ.get("LANGCHAIN_API_KEY") and env_path.exists():
    try:
        with open(env_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip().rstrip("\r")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key, value = key.strip().rstrip("\r"), value.strip().rstrip("\r").strip('"\'')
                if key.startswith(("LANGCHAIN_", "LANGSMITH_")):
                    os.environ.setdefault(key, value)
    except Exception as e:
        print(f"⚠️ Could not parse .env: {e}")
file_values = {k: v for k, v in os.environ.items() if k.startswith(("LANGCHAIN_", "LANGSMITH_"))}
print("📄 .env keys detected:", ", ".join(sorted(file_values.keys())))

from langsmith import Client
import langsmith.utils

# Clear any cached env vars (important after loading .env)
langsmith.utils.get_env_var.cache_clear()


# Add src to path
sys.path.insert(0, str(_root))

from src.graph import create_graph
from src.state import AgentState
from src.utils.rubric_loader import load_rubric, ContextBuilder
from src.nodes.justice import generate_markdown_report
def main():
    # ❌ REMOVE THIS LINE: load_dotenv()
    
    print("🚀 main() function started...")
    
    parser = argparse.ArgumentParser(description="Automaton Auditor - Multi-agent code audit system")
    parser.add_argument("--repo-url", required=True, help="GitHub repository URL to audit")
    parser.add_argument("--pdf-path", default="./reports/final_report.pdf", 
                       help="Path to PDF report in the repository (default: ./reports/final_report.pdf)")
    parser.add_argument("--output", default="./audit/report_oneself_generated/report.md",
                       help="Output path for audit report")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    print("📝 Arguments parsed successfully...")
    
    # Set debug mode
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
    
    print("🤖 Automaton Auditor Starting...")
    print(f"📂 Repository: {args.repo_url}")
    print(f"📄 PDF Report: {args.pdf_path}")
    
    # Load rubric
    try:
        print("🔄 Loading rubric...")
        rubric = load_rubric("rubric.json")
        context_builder = ContextBuilder(rubric)
        print(f"📜 Loaded rubric with {len(rubric.get('dimensions', []))} dimensions")
    except Exception as e:
        print(f"❌ Failed to load rubric: {e}")
        sys.exit(1)
    
    # Create graph
    try:
        print("🔄 Creating graph...")
        graph = create_graph()
        print("✅ Graph created successfully...")
    except Exception as e:
        print(f"❌ Failed to create graph: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Initialize state
    initial_state: AgentState = {
        "repo_url": args.repo_url,
        "pdf_path": args.pdf_path,
        "config": {
            "rubric": context_builder
        },
        "evidences": {},
        "opinions": [],
        "final_report": None,
        "errors": []
    }
    
    print("🚀 Running audit graph...")
    
    try:
        # Run the graph
        print("🔄 Invoking graph with initial state...")
        final_state = graph.invoke(initial_state)
        print("✅ Graph execution completed...")
        
        # Check for errors
        if final_state.get("errors"):
            print("\n⚠️ Warnings/Errors encountered:")
            for error in final_state["errors"]:
                print(f"  - {error}")
        if final_state.get("final_report"):
            # Create output directory
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report = final_state["final_report"]
            markdown = final_state.get("markdown_report")
            if not markdown:
                markdown = generate_markdown_report(report)
            with open(output_path, "w") as f:
                f.write(markdown)
            
            print(f"\n✅ Audit complete! Report saved to: {output_path}")
            print(f"\n📊 Overall Score: {report.overall_score:.1f}/5.0")
            
            high_scores = [c for c in report.criteria if c.final_score >= 4]
            low_scores = [c for c in report.criteria if c.final_score <= 2]
            if high_scores:
                print(f"✅ Strengths: {', '.join([c.name for c in high_scores])}")
            if low_scores:
                print(f"⚠️ Issues: {', '.join([c.name for c in low_scores])}")
        else:
            print("❌ No final report generated")
            
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Entry point when run as script (use escaped names so __ is not stripped by sync/tools)
if getattr(sys.modules.get("\x5f\x5fmain\x5f\x5f", object()), "\x5f\x5fname\x5f\x5f", None) == "\x5f\x5fmain\x5f\x5f":
    main()