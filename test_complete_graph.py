#!/usr/bin/env python3
"""
Test script for the complete Automaton Auditor graph.
This demonstrates the full Digital Courtroom workflow.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.graph import build_graph
from src.state import AgentState
from src.context_manager import setup_audit_context

def main():
    """Test the complete auditor graph with proper sandboxing."""
    
    # Setup audit context with cleanup handlers
    setup_audit_context()
    
    # Example test case - using this repository
    test_state: AgentState = {
        "repo_url": "https://github.com/bethel4/automaton-auditor",
        "pdf_path": "reports/interim_report.md",  # You'll need to create this
        "rubric_dimensions": [],  # Will be populated by initialize_state
        "evidences": {},
        "opinions": [],
        "final_report": None,  # Will be populated by Chief Justice
    }
    
    print("🏛️  Starting Automaton Auditor - Digital Courtroom")
    print("=" * 60)
    print(f"📁 Target Repository: {test_state['repo_url']}")
    print(f"📄 Target PDF: {test_state['pdf_path']}")
    print("🧰 Sandbox: Temporary directories will be cleaned up automatically")
    print()
    
    try:
        # Build and run the graph
        graph = build_graph()
        
        print("🔍 Detective Layer: Collecting forensic evidence...")
        print("⚖️  Judicial Layer: Dialectical analysis in progress...")
        print("🧑‍⚖️  Chief Justice: Synthesizing final verdict...")
        print()
        
        # Execute the graph
        result = graph.invoke(test_state)
        
        # Display results
        print("✅ Audit Complete!")
        print("=" * 60)
        
        if "markdown_report" in result:
            report = result["markdown_report"]
            
            # Extract and display key metrics
            lines = report.split('\n')
            for line in lines:
                if "Overall Score:" in line:
                    print(f"📊 {line}")
                elif "Executive Summary" in line:
                    print(f"📋 {line}")
                    break
            
            print("\n📝 Full report generated in result['markdown_report']")
            
            # Optionally save to file
            with open("audit_report.md", "w") as f:
                f.write(report)
            print("💾 Report saved to audit_report.md")
            
        else:
            print("❌ No report generated")
            
    except KeyboardInterrupt:
        print("\n🛑 Audit interrupted by user")
        
    except Exception as e:
        print(f"❌ Error during audit: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n🧹 Cleanup completed")

if __name__ == "__main__":
    main()
