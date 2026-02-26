# src/context_manager.py

import atexit
import signal
import sys
from tools.repo_tools import cleanup_temp_dirs

class AuditContextManager:
    """Manages audit lifecycle and cleanup."""
    
    def __init__(self):
        self.cleanup_registered = False
        
    def register_cleanup(self):
        """Register cleanup handlers for graceful shutdown."""
        if self.cleanup_registered:
            return
            
        # Register cleanup on normal exit
        atexit.register(self._cleanup)
        
        # Register cleanup on signals
        for sig in [signal.SIGTERM, signal.SIGINT]:
            signal.signal(sig, self._signal_handler)
            
        self.cleanup_registered = True
        
    def _cleanup(self):
        """Perform cleanup operations."""
        print("🧹 Cleaning up temporary directories...")
        try:
            cleanup_temp_dirs()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self._cleanup()
        sys.exit(0)

# Global context manager
_audit_context = AuditContextManager()

def setup_audit_context():
    """Setup audit context with cleanup handlers."""
    _audit_context.register_cleanup()
    return _audit_context
