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
    """Test the complete auditor graph with requests repository."""
    
    # Setup audit context with cleanup handlers
    setup_audit_context()
    
    # Test with requests repository directly in code
    test_state: AgentState = {
        "repo_url": "https://github.com/psf/requests.git",
        "pdf_path": "reports/interim_report.md",
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
        
        # Show evidence summary
        if "evidences" in result:
            print("🔍 Evidence Collected:")
            for category, evidence_list in result["evidences"].items():
                print(f"  📁 {category}: {len(evidence_list)} items")
                for i, evidence in enumerate(evidence_list[:2], 1):
                    print(f"    {i}. {evidence.get('goal', 'Unknown')} - Found: {evidence.get('found', False)}")
        
        # Show judicial opinions summary
        if "opinions" in result:
            print("\n⚖️ Judicial Opinions:")
            judges = {}
            for opinion in result["opinions"]:
                judge = opinion.get('judge', 'Unknown')
                if judge not in judges:
                    judges[judge] = []
                judges[judge].append(opinion.get('score', 0))
            
            for judge, scores in judges.items():
                avg_score = sum(scores) / len(scores) if scores else 0
                print(f"  �‍⚖️ {judge}: {len(scores)} opinions, avg score: {avg_score:.1f}/5")
        
        # Show final report
        if "final_report" in result and result["final_report"]:
            report = result["final_report"]
            if hasattr(report, 'overall_score'):
                print(f"\n📊 Overall Score: {report.overall_score:.1f}/5.0")
            
            if "markdown_report" in result:
                report_content = result["markdown_report"]
                lines = report_content.split('\n')
                for line in lines:
                    if "Overall Score:" in line:
                        print(f"📊 {line}")
                        break
                
                # Optionally save to file
                with open("audit_report.md", "w") as f:
                    f.write(report_content)
                print("💾 Report saved to audit_report.md")
            
        else:
            print("❌ No final report generated")
            
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
