#!/usr/bin/env python3
"""
Test basic functionality without LLM to verify core components work.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.context_manager import setup_audit_context
from tools.repo_tools import clone_repository, extract_git_history

def main():
    """Test basic repo tools without LLM."""
    
    # Setup audit context with cleanup handlers
    setup_audit_context()
    
    print("🔍 Testing Basic Repo Tools")
    print("=" * 40)
    
    try:
        # Test with requests repository
        repo_url = "https://github.com/psf/requests.git"
        
        print(f"📁 Cloning: {repo_url}")
        repo_path = clone_repository(repo_url)
        print(f"✅ Successfully cloned to: {repo_path}")
        
        print("\n📊 Extracting git history...")
        commits = extract_git_history(repo_path)
        print(f"✅ Found {len(commits)} commits")
        
        print("\n📝 First 5 commits:")
        for i, commit in enumerate(commits[:5], 1):
            print(f"  {i}. {commit}")
        
        # Basic pattern analysis without LLM
        print("\n🧠 Basic Pattern Analysis:")
        feature_commits = [c for c in commits if 'feat:' in c.lower()]
        fix_commits = [c for c in commits if 'fix:' in c.lower() or 'bug' in c.lower()]
        release_commits = [c for c in commits if 'release' in c.lower() or 'bump' in c.lower()]
        
        print(f"  🚀 Feature commits: {len(feature_commits)}")
        print(f"  🐛 Bug fixes: {len(fix_commits)}")
        print(f"  📦 Releases: {len(release_commits)}")
        
        if len(feature_commits) > len(fix_commits):
            pattern = 'feature_development'
        elif len(release_commits) > 0:
            pattern = 'release_cycle'
        else:
            pattern = 'maintenance'
        
        print(f"  📋 Detected Pattern: {pattern}")
        
        print("\n✅ Basic functionality test completed successfully!")
        print("🎯 Core repo tools are working - ready for LLM integration!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
