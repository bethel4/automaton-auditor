#!/usr/bin/env python
# run_audit.py - CORRECT ORDER

# LOAD ENVIRONMENT VARIABLES FIRST - BEFORE ANY OTHER IMPORTS
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env immediately
env_path = Path(__file__).parent.absolute() / '.env'
print(f"📂 Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

# Verify they loaded (optional)
print(f"✅ DETECTIVE_MODEL = {os.getenv('DETECTIVE_MODEL')}")
print(f"✅ JUDGE_MODEL = {os.getenv('JUDGE_MODEL')}")

# NOW import your modules - AFTER environment is loaded
import sys
import argparse
sys.path.insert(0, str(Path(__file__).parent))

from src.graph import create_graph
from src.state import AgentState
from src.utils.rubric_loader import load_rubric, ContextBuilder

# ... rest of your code

def main():
    # Load environment variables
    load_dotenv()
    
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
    
    # Load rubric - using the load_rubric convenience function
    try:
        rubric = load_rubric("rubric.json")  # Returns rubric dictionary
        dimensions = rubric.get("dimensions", [])
        print(f"📜 Loaded rubric with {len(dimensions)} dimensions")
        
        # Create context builder from rubric
        context_builder = ContextBuilder(rubric)
        print(f"✅ ContextBuilder created successfully")
        
    except Exception as e:
        print(f"❌ Failed to load rubric: {e}")
        sys.exit(1)
    
    # Create graph
    graph = create_graph()
    
    # Initialize state with context builder
    initial_state: AgentState = {
        "repo_url": args.repo_url,
        "pdf_path": args.pdf_path,
        "config": {
            "rubric": context_builder  # 👈 This is what nodes will access
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
                    print(f"✅ Strengths: {', '.join([c.dimension_name for c in high_scores])}")
                if low_scores:
                    print(f"⚠️ Issues: {', '.join([c.dimension_name for c in low_scores])}")
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