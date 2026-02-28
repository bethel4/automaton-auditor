#!/usr/bin/env python
# run_audit.py

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

# LOAD ENV ONCE - AT THE VERY TOP
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)
# 👇 ADD THE LANGSNITH TEST CODE RIGHT HERE 👇
from langsmith import Client
import langsmith.utils

# Clear any cached env vars (important after loading .env)
langsmith.utils.get_env_var.cache_clear()

# Test client connection
try:
    client = Client()
    print(f"✅ LangSmith client initialized: {client is not None}")
    print(f"   Project: {os.getenv('LANGCHAIN_PROJECT')}")
    print(f"   Endpoint: {os.getenv('LANGCHAIN_ENDPOINT')}")
except Exception as e:
    print(f"❌ LangSmith client failed: {e}")
    print("   Check your API key and environment variables")
# 👆 END OF TEST CODE 👆

# VERIFY environment variables are loaded (add this temporarily)
print("🔍 LangSmith Configuration:")
print(f"  LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2')}")
print(f"  LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT')}")
print(f"  LANGCHAIN_ENDPOINT: {os.getenv('LANGCHAIN_ENDPOINT')}")
print(f"  API Key set: {'Yes' if os.getenv('LANGCHAIN_API_KEY') else 'No'}")

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.graph import create_graph
from src.state import AgentState
from src.utils.rubric_loader import load_rubric, ContextBuilder


def main():
    # ❌ REMOVE THIS LINE: load_dotenv()
    
    parser = argparse.ArgumentParser(description="Automaton Auditor - Multi-agent code audit system")
    parser.add_argument("--repo-url", required=True, help="GitHub repository URL to audit")
    parser.add_argument("--pdf-path", default="./reports/final_report.pdf", 
                       help="Path to PDF report in the repository (default: ./reports/final_report.pdf)")
    parser.add_argument("--output", default="./audit/report_oneself_generated/report.md",
                       help="Output path for audit report")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set debug mode
    if args.debug:
        os.environ["DEBUG_MODE"] = "true"
    
    print("🤖 Automaton Auditor Starting...")
    print(f"📂 Repository: {args.repo_url}")
    print(f"📄 PDF Report: {args.pdf_path}")
    
    # Load rubric
    try:
        rubric = load_rubric("rubric.json")
        context_builder = ContextBuilder(rubric)
        print(f"📜 Loaded rubric with {len(rubric.get('dimensions', []))} dimensions")
    except Exception as e:
        print(f"❌ Failed to load rubric: {e}")
        sys.exit(1)
    
    # Create graph
    graph = create_graph()
    
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
        final_state = graph.invoke(initial_state)
        
        # Check for errors
        if final_state.get("errors"):
            print("\n⚠️ Warnings/Errors encountered:")
            for error in final_state["errors"]:
                print(f"  - {error}")
        
        # Save report
        if final_state.get("final_report"):
            # Create output directory
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Generate markdown
            if "markdown_report" in final_state:
                with open(output_path, "w") as f:
                    f.write(final_state["markdown_report"])
                
                print(f"\n✅ Audit complete! Report saved to: {output_path}")
                
                # Print summary
                report = final_state["final_report"]
                print(f"\n📊 Overall Score: {report.overall_score:.1f}/5.0")
                
                # Show top strengths/weaknesses
                high_scores = [c for c in report.criteria if c.final_score >= 4]
                low_scores = [c for c in report.criteria if c.final_score <= 2]
                
                if high_scores:
                    print(f"✅ Strengths: {', '.join([c.name for c in high_scores])}")
                if low_scores:
                    print(f"⚠️ Issues: {', '.join([c.name for c in low_scores])}")
            else:
                print("❌ No markdown report generated")
        else:
            print("❌ No final report generated")
            
    except Exception as e:
        print(f"❌ Audit failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()