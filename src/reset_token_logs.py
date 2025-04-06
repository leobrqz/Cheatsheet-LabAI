import os
import sys

# Add the parent directory to sys.path to allow imports to work
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from src.database.chroma_db import ChromaDatabase
from src.core.generators import TokenUsageTracker
from src.utils.logger import get_logger

# Get logger instance
logger = get_logger(__name__)

def reset_token_logs():
    """Reset the token logs collection and clear all caches."""
    try:
        # Initialize database
        db = ChromaDatabase()
        logger.info("Chroma database initialized successfully")
        
        # Reset the collection
        db.reset_collection()
        logger.info("Token logs collection reset successfully")
        
        # Clear TokenUsageTracker cache
        token_tracker = TokenUsageTracker()
        token_tracker._clear_cache()
        logger.info("Token usage tracker cache cleared successfully")
        
        # Clear thread-local storage and collection cache
        if hasattr(db, '_local'):
            if hasattr(db._local, 'collection'):
                delattr(db._local, 'collection')
        with db._collection_cache_lock:
            db._collection_cache.clear()
        logger.info("Thread-local storage and collection cache cleared successfully")
        
        # Cleanup database resources
        db.cleanup()
        logger.info("Database resources cleaned up successfully")
        
        # Optimize the database
        db.optimize()
        logger.info("Database optimized successfully")
        
        # Force persist changes
        if hasattr(db.client, 'persist'):
            db.client.persist()
        logger.info("Changes persisted successfully")
        
        logger.info("Token logs reset completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error resetting token logs: {e}")
        return False

if __name__ == "__main__":
    # Run the reset
    success = reset_token_logs()
    if not success:
        sys.exit(1)