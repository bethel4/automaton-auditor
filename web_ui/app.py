#!/usr/bin/env python3
"""
Web UI for Automaton Auditor - Digital Courtroom Interface
Provides interactive testing and visualization of the audit process.
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from src.graph import build_graph
from src.state import AgentState

# Page configuration
st.set_page_config(
    page_title="🏛️ Automaton Auditor - Digital Courtroom",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 2rem;
    }
    .status-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .evidence-card {
        background: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .judge-card {
        background: #f8f9fa;
        border-left: 4px solid #007bff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .prosecutor { border-left-color: #dc3545; }
    .defense { border-left-color: #28a745; }
    .techlead { border-left-color: #ffc107; }
    .score-high { color: #28a745; font-weight: bold; }
    .score-medium { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if 'audit_results' not in st.session_state:
        st.session_state.audit_results = None
    if 'audit_running' not in st.session_state:
        st.session_state.audit_running = False
    if 'current_step' not in st.session_state:
        st.session_state.current_step = ""
    if 'evidence_log' not in st.session_state:
        st.session_state.evidence_log = []
    if 'opinion_log' not in st.session_state:
        st.session_state.opinion_log = []

def load_rubric():
    """Load the evaluation rubric."""
    try:
        with open('rubric.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("❌ rubric.json not found. Please ensure it's in the root directory.")
        return None

def run_audit_async(repo_url: str, pdf_path: str) -> Dict[str, Any]:
    """Run the audit process with progress updates."""
    
    # Initialize audit state
    state: AgentState = {
        "repo_url": repo_url,
        "pdf_path": pdf_path,
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None,
    }
    
    try:
        # Build and run the graph
        graph = build_graph()
        
        # Update progress
        st.session_state.current_step = "🔍 Initializing Digital Courtroom..."
        
        # Execute the graph
        result = graph.invoke(state)
        
        return result
        
    except Exception as e:
        st.error(f"❌ Audit failed: {str(e)}")
        return {"error": str(e)}

def display_evidence(evidences: Dict[str, Any]):
    """Display collected evidence in an organized format."""
    st.subheader("🔍 Forensic Evidence Collection")
    
    if not evidences:
        st.warning("No evidence collected.")
        return
    
    for category, evidence_list in evidences.items():
        if evidence_list:
            st.markdown(f"### 📁 {category.replace('_', ' ').title()}")
            
            for i, evidence in enumerate(evidence_list, 1):
                with st.expander(f"Evidence {i}: {evidence.get('goal', 'Unknown')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**Goal:** {evidence.get('goal', 'Unknown')}")
                        st.markdown(f"**Location:** `{evidence.get('location', 'Unknown')}`")
                        st.markdown(f"**Rationale:** {evidence.get('rationale', 'No rationale provided')}")
                        
                        if evidence.get('content'):
                            with st.expander("View Content"):
                                st.code(evidence['content'][:500] + "..." if len(evidence['content']) > 500 else evidence['content'])
                    
                    with col2:
                        confidence = evidence.get('confidence', 0)
                        found = evidence.get('found', False)
                        
                        # Status indicator
                        if found:
                            st.success("✅ Found")
                        else:
                            st.error("❌ Not Found")
                        
                        # Confidence meter
                        st.metric("Confidence", f"{confidence:.1%}")
                        
                        # Color code confidence
                        if confidence >= 0.8:
                            st.markdown('<div class="score-high">High Confidence</div>', unsafe_allow_html=True)
                        elif confidence >= 0.5:
                            st.markdown('<div class="score-medium">Medium Confidence</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="score-low">Low Confidence</div>', unsafe_allow_html=True)

def display_judicial_opinions(opinions: list):
    """Display judicial opinions with persona separation."""
    st.subheader("⚖️ Judicial Deliberations")
    
    if not opinions:
        st.warning("No judicial opinions generated.")
        return
    
    # Group opinions by judge
    by_judge = {}
    for opinion in opinions:
        judge = opinion.get('judge', 'Unknown')
        if judge not in by_judge:
            by_judge[judge] = []
        by_judge[judge].append(opinion)
    
    # Display each judge's opinions
    judge_info = {
        "Prosecutor": {"emoji": "👨‍⚖️", "color": "prosecutor", "description": "Adversarial Analysis"},
        "Defense": {"emoji": "👩‍⚖️", "color": "defense", "description": "Optimistic Analysis"},
        "TechLead": {"emoji": "🧑‍💼", "color": "techlead", "description": "Pragmatic Analysis"}
    }
    
    for judge_name, judge_opinions in by_judge.items():
        info = judge_info.get(judge_name, {"emoji": "⚖️", "color": "", "description": ""})
        
        st.markdown(f"### {info['emoji']} {judge_name} - {info['description']}")
        
        for opinion in judge_opinions:
            score = opinion.get('score', 0)
            criterion = opinion.get('criterion_id', 'Unknown')
            argument = opinion.get('argument', 'No argument provided')
            cited_evidence = opinion.get('cited_evidence', [])
            
            # Score color coding
            if score >= 4:
                score_class = "score-high"
                score_text = "Excellent"
            elif score >= 3:
                score_class = "score-medium"
                score_text = "Good"
            else:
                score_class = "score-low"
                score_text = "Needs Improvement"
            
            st.markdown(f"""
            <div class="judge-card {info['color']}">
                <strong>Criterion:</strong> {criterion}<br>
                <strong>Score:</strong> <span class="{score_class}">{score}/5 - {score_text}</span><br>
                <strong>Argument:</strong> {argument}<br>
                <strong>Cited Evidence:</strong> {', '.join(cited_evidence) if cited_evidence else 'None'}
            </div>
            """, unsafe_allow_html=True)

def display_final_report(report: Dict[str, Any]):
    """Display the final audit report."""
    st.subheader("📋 Chief Justice Final Verdict")
    
    if not report:
        st.warning("No final report available.")
        return
    
    # Executive summary
    st.markdown("### 🎯 Executive Summary")
    overall_score = report.get('overall_score', 0)
    
    # Overall score visualization
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Score", f"{overall_score:.1f}/5.0")
    with col2:
        if overall_score >= 4.0:
            st.success("🏆 Excellent Implementation")
        elif overall_score >= 3.0:
            st.info("👍 Good Implementation")
        else:
            st.error("⚠️ Needs Improvement")
    with col3:
        st.metric("Criteria Evaluated", len(report.get('criteria', [])))
    
    # Detailed breakdown
    st.markdown("### 📊 Detailed Breakdown")
    
    criteria = report.get('criteria', [])
    if criteria:
        for criterion in criteria:
            name = criterion.get('dimension_name', 'Unknown')
            score = criterion.get('final_score', 0)
            dissent = criterion.get('dissent_summary')
            remediation = criterion.get('remediation', '')
            
            with st.expander(f"📋 {name} - Score: {score}/5"):
                st.markdown(f"**Final Score:** {score}/5")
                
                if dissent:
                    st.markdown(f"**⚖️ Dissent:** {dissent}")
                
                st.markdown(f"**🔧 Remediation:** {remediation}")
                
                # Show judge opinions for this criterion
                opinions = criterion.get('judge_opinions', [])
                if opinions:
                    st.markdown("**Judicial Analysis:**")
                    for opinion in opinions:
                        judge = opinion.get('judge', 'Unknown')
                        score = opinion.get('score', 0)
                        argument = opinion.get('argument', '')
                        st.markdown(f"- **{judge}** ({score}/5): {argument}")
    
    # Remediation plan
    remediation_plan = report.get('remediation_plan', '')
    if remediation_plan:
        st.markdown("### 🚀 Overall Remediation Plan")
        st.markdown(remediation_plan)

def main():
    """Main application interface."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🏛️ Automaton Auditor - Digital Courtroom</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #6c757d; margin-bottom: 2rem;">Autonomous Code Governance with Multi-Agent Synthesis</p>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Audit Configuration")
        
        # Repository input
        repo_url = st.text_input(
            "📁 Repository URL",
            value="https://github.com/bethel4/automaton-auditor",
            help="GitHub repository URL to audit"
        )
        
        # PDF input
        pdf_path = st.text_input(
            "📄 PDF Report Path",
            value="reports/interim_report.md",
            help="Path to the PDF or markdown report"
        )
        
        # Advanced options
        st.markdown("---")
        st.markdown("### 🔧 Advanced Options")
        
        enable_tracing = st.checkbox("🔍 Enable LangSmith Tracing", value=False)
        debug_mode = st.checkbox("🐛 Debug Mode", value=False)
        
        # Run audit button
        st.markdown("---")
        run_button = st.button(
            "🚀 Run Audit",
            type="primary",
            use_container_width=True,
            disabled=st.session_state.audit_running
        )
    
    # Main content area
    if run_button and not st.session_state.audit_running:
        st.session_state.audit_running = True
        st.session_state.current_step = "🔄 Starting audit process..."
        
        # Show progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Update status
        status_text.markdown("🔍 Initializing Digital Courtroom...")
        progress_bar.progress(10)
        
        # Run the audit
        try:
            results = run_audit_async(repo_url, pdf_path)
            
            if 'error' not in results:
                st.session_state.audit_results = results
                st.session_state.current_step = "✅ Audit completed successfully!"
                progress_bar.progress(100)
            else:
                st.session_state.current_step = f"❌ Audit failed: {results['error']}"
                
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
            st.session_state.current_step = f"❌ Audit failed: {str(e)}"
        
        finally:
            st.session_state.audit_running = False
    
    # Display current status
    if st.session_state.current_step:
        st.markdown(f"### 📊 Status: {st.session_state.current_step}")
    
    # Display results
    if st.session_state.audit_results:
        results = st.session_state.audit_results
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["🔍 Evidence", "⚖️ Judicial Opinions", "📋 Final Report", "📄 Raw Data"])
        
        with tab1:
            display_evidence(results.get('evidences', {}))
        
        with tab2:
            display_judicial_opinions(results.get('opinions', []))
        
        with tab3:
            final_report = results.get('final_report')
            if final_report:
                display_final_report(final_report.to_dict() if hasattr(final_report, 'to_dict') else final_report)
            else:
                st.warning("No final report available.")
        
        with tab4:
            st.markdown("### 📄 Raw Audit Data")
            st.json(results)
    
    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="text-align: center; color: #6c757d;">🏛️ Digital Courtroom • Automaton Auditor • Week 2 FDE Challenge</p>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
