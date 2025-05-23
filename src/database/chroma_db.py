import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from datetime import datetime
from ..utils.logger import get_logger
import backoff
from functools import wraps
import threading
from .query_builder import LogQueryBuilder
from ..utils.utils import validate_numeric_range, validate_positive_integer

# Get logger instance
logger = get_logger(__name__)

def handle_chroma_errors(func):
    """Decorator to handle ChromaDB errors with retries."""
    @wraps(func)
    @backoff.on_exception(
        backoff.expo,
        (chromadb.errors.ChromaError, Exception),
        max_tries=3,
        max_time=30
    )
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except chromadb.errors.ChromaError as e:
            logger.error(f"ChromaDB error in {func.__name__}: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise
    return wrapper

class ChromaDatabase:
    _instance = None
    _lock = threading.Lock()
    _collection_lock = threading.Lock()  # Add separate lock for collection operations
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ChromaDatabase, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the ChromaDatabase instance with proper error handling."""
        if getattr(self, '_initialized', False):
            return
            
        with self._lock:
            if getattr(self, '_initialized', False):
                return
                
            try:
                # Create the database directory if it doesn't exist
                self.db_path = os.path.join('..', 'data', 'chroma')
                os.makedirs(self.db_path, exist_ok=True)
                
                # Initialize Chroma client with persistent storage
                self.client = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=Settings(
                        allow_reset=True,
                        is_persistent=True,
                        persist_directory=self.db_path
                    )
                )
                
                # Initialize thread-local storage
                self._local = threading.local()
                self._collection_cache = {}
                self._collection_cache_lock = threading.Lock()
                
                # Verify client initialization
                if not self.client:
                    raise RuntimeError("Failed to initialize ChromaDB client")
                
                # Ensure the token_logs collection exists
                self._ensure_token_logs_collection()
                
                self._initialized = True
                logger.info(f"Successfully initialized Chroma database at {self.db_path}")
            except Exception as e:
                self._initialized = False
                logger.critical(f"Critical error initializing ChromaDatabase: {e}")
                raise RuntimeError(f"Failed to initialize ChromaDatabase: {e}")
    
    def __del__(self):
        """Cleanup when the database instance is destroyed."""
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def cleanup(self):
        """
        Clean up resources without deleting the database.
        This includes:
        - Closing thread-local collections
        - Resetting thread-local storage
        - Persisting any pending changes
        """
        try:
            with self._collection_cache_lock:
                # Clear collection cache
                self._collection_cache.clear()
            
            # Clear thread-local storage
            if hasattr(self._local, 'collection'):
                delattr(self._local, 'collection')
            
            # Persist any pending changes
            if hasattr(self.client, 'persist'):
                self.client.persist()
            
            logger.info("ChromaDB cleanup completed successfully")
        except Exception as e:
            logger.error(f"Error during ChromaDB cleanup: {e}")
            raise
    
    def reset_collection(self):
        """
        Reset the collection without deleting the database.
        This is useful for clearing all data while maintaining the database structure.
        """
        try:
            with self._lock:
                # Delete the existing collection
                self.client.delete_collection("token_logs")
                
                # Recreate the collection
                self.collection = self.client.create_collection(
                    name="token_logs",
                    metadata={
                        "description": "Token usage logs for OpenAI API calls",
                        "schema_timestamp": "float",
                        "schema_function_name": "str",
                        "schema_prompt_tokens": "int",
                        "schema_completion_tokens": "int",
                        "schema_total_tokens": "int",
                        "schema_cost": "float"
                    }
                )
                
                # Reset thread-local collection
                if hasattr(self._local, 'collection'):
                    self._local.collection = self.collection
                
                # Clear collection cache
                with self._collection_cache_lock:
                    self._collection_cache.clear()
                
                # Clear thread-local storage
                if hasattr(self._local, 'collection'):
                    delattr(self._local, 'collection')
                
                # Persist changes
                if hasattr(self.client, 'persist'):
                    self.client.persist()
                
                logger.info("Collection reset completed successfully")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise
    
    def optimize(self):
        """
        Optimize the database without deleting data.
        This includes:
        - Compacting the database
        - Optimizing indexes
        - Cleaning up temporary files
        """
        try:
            with self._lock:
                # Persist any pending changes
                if hasattr(self.client, 'persist'):
                    self.client.persist()
                
                # Compact the database if supported
                if hasattr(self.client, 'compact'):
                    self.client.compact()
                
                logger.info("Database optimization completed successfully")
        except Exception as e:
            logger.error(f"Error optimizing database: {e}")
            raise
    
    def _get_thread_safe_collection(self):
        """Get a thread-safe collection instance with proper locking."""
        thread_id = threading.get_ident()
        
        # Check cache first
        with self._collection_cache_lock:
            if thread_id in self._collection_cache:
                return self._collection_cache[thread_id]
        
        # If not in cache, create new collection with proper locking
        with self._collection_lock:
            collection = self.client.get_or_create_collection(
                name="token_logs",
                metadata={
                    "description": "Token usage logs for OpenAI API calls",
                    "schema_timestamp": "float",
                    "schema_function_name": "str",
                    "schema_prompt_tokens": "int",
                    "schema_completion_tokens": "int",
                    "schema_total_tokens": "int",
                    "schema_cost": "float"
                }
            )
            
            # Update cache
            with self._collection_cache_lock:
                self._collection_cache[thread_id] = collection
            
            return collection
    
    def _validate_and_format_date(self, date_str: str) -> float:
        """
        Validate and format date string to timestamp.
        
        Args:
            date_str: Date string to validate and format
            
        Returns:
            Timestamp as a float (seconds since epoch)
            
        Raises:
            ValueError: If date format is invalid
        """
        try:
            # Parse the date string as YYYY-MM-DD
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            # Convert to timestamp (seconds since epoch)
            return dt.timestamp()
        except ValueError:
            # If the date is not in YYYY-MM-DD format, try to parse it as ISO format
            try:
                dt = datetime.fromisoformat(date_str)
                # Convert to timestamp
                return dt.timestamp()
            except ValueError:
                raise ValueError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD or ISO format")
    
    def _validate_numeric_range(self, min_val: float, max_val: float) -> bool:
        """
        Validate numeric range.
        
        Args:
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            True if valid, False otherwise
        """
        return min_val <= max_val
    
    @handle_chroma_errors
    def add_log(self, function_name: str, prompt_tokens: int, 
                completion_tokens: int, total_tokens: int, 
                cost: float, output: Optional[str] = None) -> None:
        """
        Add a new log entry to the database.
        
        Args:
            function_name: Name of the function that generated the log
            prompt_tokens: Number of tokens in the prompt
            completion_tokens: Number of tokens in the completion
            total_tokens: Total number of tokens
            cost: Cost of the API call
            output: Optional output text
        """
        try:
            # Validate input parameters
            if not isinstance(function_name, str) or not function_name.strip():
                raise ValueError("Invalid function name")
            if not isinstance(prompt_tokens, int) or prompt_tokens < 0:
                raise ValueError("prompt_tokens must be a non-negative integer")
            if not isinstance(completion_tokens, int) or completion_tokens < 0:
                raise ValueError("completion_tokens must be a non-negative integer")
            if not isinstance(total_tokens, int) or total_tokens < 0:
                raise ValueError("total_tokens must be a non-negative integer")
            if not isinstance(cost, (int, float)) or cost < 0:
                raise ValueError("cost must be a non-negative number")
            if output is not None and not isinstance(output, str):
                raise ValueError("output must be a string or None")
            
            # Create a unique ID for the log entry
            timestamp = datetime.now().timestamp()
            log_id = f"{function_name}_{timestamp}"
            
            # Prepare metadata
            metadata = {
                "timestamp": timestamp,  # Store as timestamp (float)
                "function_name": function_name,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost": cost
            }
            
            # Add the log entry to the collection
            collection = self._get_thread_safe_collection()
            collection.add(
                ids=[log_id],
                metadatas=[metadata],
                documents=[output] if output else [""]
            )
            
            logger.debug(f"Added log entry: {log_id}")
        except Exception as e:
            logger.error(f"Error adding log entry: {e}")
            raise
    
    @handle_chroma_errors
    def get_logs_by_date_range(self, start_date: str, end_date: str, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs within a date range."""
        try:
            # Validate and format dates to timestamps
            start_timestamp = self._validate_and_format_date(start_date)
            end_timestamp = self._validate_and_format_date(end_date)
            
            # Validate limit
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive integer")
            
            # Query the collection
            collection = self._get_thread_safe_collection()
            
            # Use timestamps for date range queries
            results = collection.get(
                where={
                    "$and": [
                        {"timestamp": {"$gte": start_timestamp}},
                        {"timestamp": {"$lte": end_timestamp}}
                    ]
                },
                limit=limit
            )
            
            return self._format_results(results)
        except Exception as e:
            logger.error(f"Error getting logs by date range: {e}")
            raise
    
    @handle_chroma_errors
    def get_logs_by_function(self, function_name: str, 
                            limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs for a specific function."""
        try:
            # Validate function name
            if not isinstance(function_name, str) or not function_name.strip():
                raise ValueError("Invalid function name")
            
            # Validate limit
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive integer")
            
            # Query the collection
            collection = self._get_thread_safe_collection()
            results = collection.get(
                where={
                    "function_name": {
                        "$eq": function_name
                    }
                },
                limit=limit
            )
            
            return self._format_results(results)
        except Exception as e:
            logger.error(f"Error getting logs by function: {e}")
            raise
    
    @handle_chroma_errors
    def get_logs_by_token_range(self, min_tokens: int, max_tokens: int, 
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs within a token range."""
        try:
            # Validate token range
            if not validate_positive_integer(min_tokens) or not validate_positive_integer(max_tokens):
                raise ValueError("min_tokens and max_tokens must be positive integers")
            if not validate_numeric_range(min_tokens, max_tokens):
                raise ValueError("min_tokens must be less than or equal to max_tokens")
            
            # Validate limit
            if not validate_positive_integer(limit):
                raise ValueError("limit must be a positive integer")
            
            # Query the collection
            collection = self._get_thread_safe_collection()
            results = collection.get(
                where={
                    "$and": [
                        {"total_tokens": {"$gte": min_tokens}},
                        {"total_tokens": {"$lte": max_tokens}}
                    ]
                },
                limit=limit
            )
            
            return self._format_results(results)
        except Exception as e:
            logger.error(f"Error getting logs by token range: {e}")
            raise

    @handle_chroma_errors
    def get_unique_functions(self) -> List[str]:
        """
        Get a list of unique function names from the logs.
        
        Returns:
            List of unique function names
        """
        try:
            # Query the collection for all entries
            collection = self._get_thread_safe_collection()
            results = collection.get()
            
            # Extract unique function names
            unique_functions = set()
            for metadata in results['metadatas']:
                if 'function_name' in metadata:
                    unique_functions.add(metadata['function_name'])
            
            # Sort the list for consistent ordering
            return sorted(list(unique_functions))
        except Exception as e:
            logger.error(f"Error getting unique functions: {e}")
            raise

    @handle_chroma_errors
    def get_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all logs from the database."""
        try:
            # Validate limit
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit must be a positive integer")
            
            # Query the collection
            collection = self._get_thread_safe_collection()
            results = collection.get(limit=limit)
            
            # Format results
            logs = []
            for i in range(len(results['ids'])):
                log = {
                    'id': results['ids'][i],
                    'timestamp': results['metadatas'][i]['timestamp'],
                    'function_name': results['metadatas'][i]['function_name'],
                    'prompt_tokens': results['metadatas'][i]['prompt_tokens'],
                    'completion_tokens': results['metadatas'][i]['completion_tokens'],
                    'total_tokens': results['metadatas'][i]['total_tokens'],
                    'cost': results['metadatas'][i]['cost'],
                    'output': results['documents'][i] if results['documents'][i] else None
                }
                logs.append(log)
            
            return logs
        except Exception as e:
            logger.error(f"Error getting logs: {e}")
            raise

    @handle_chroma_errors
    def get_logs_by_cost_range(self, min_cost: float, max_cost: float, 
                              limit: int = 100) -> List[Dict[str, Any]]:
        """Get logs within a specific cost range."""
        try:
            if not validate_numeric_range(min_cost, max_cost):
                raise ValueError("Invalid cost range")
            if not validate_positive_integer(limit):
                raise ValueError("limit must be a positive integer")
                
            collection = self._get_thread_safe_collection()
            results = collection.get(
                where={
                    "$and": [
                        {"cost": {"$gte": min_cost}},
                        {"cost": {"$lte": max_cost}}
                    ]
                },
                limit=limit
            )
            
            return self._format_results(results)
        except Exception as e:
            logger.error(f"Error getting logs by cost range: {e}")
            raise

    @handle_chroma_errors
    def query_logs(self, query_builder_or_dict, limit: int = 100) -> List[Dict[str, Any]]:
        """Execute a combined query using the query builder.
        
        Args:
            query_builder_or_dict: An instance of LogQueryBuilder or a dictionary containing the query conditions
            limit: Maximum number of results to return
            
        Returns:
            List of log entries matching the query conditions
        """
        collection = self._get_thread_safe_collection()
        
        # Handle both LogQueryBuilder object and dictionary
        if hasattr(query_builder_or_dict, 'has_filters') and callable(getattr(query_builder_or_dict, 'has_filters')):
            # If no filters are set, return all logs up to the limit
            if not query_builder_or_dict.has_filters():
                logger.debug("No filters set, returning all logs")
                return self.get_logs(limit)
            
            # Get the query dictionary
            query = query_builder_or_dict.build()
            where_clause = query.get("where", {})
            limit = query.get("limit", limit)
        else:
            # If it's already a dictionary, use it directly
            where_clause = query_builder_or_dict.get("where", {})
            limit = query_builder_or_dict.get("limit", limit)
        
        logger.debug(f"Executing query with where clause: {where_clause}")
        
        # Execute the query
        results = collection.get(
            where=where_clause,
            limit=limit
        )
        
        return self._format_results(results)

    def _format_results(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format the results from ChromaDB into a list of dictionaries."""
        if not results or not results.get('ids'):
            logger.debug("No results found in ChromaDB response")
            return []
            
        formatted_results = []
        for i in range(len(results['ids'])):
            metadata = results['metadatas'][i]
            # Convert timestamp to datetime for proper formatting
            timestamp = datetime.fromtimestamp(metadata.get('timestamp', 0))
            formatted_results.append({
                'id': results['ids'][i],
                'function_name': metadata.get('function_name', ''),
                'prompt_tokens': metadata.get('prompt_tokens', 0),
                'completion_tokens': metadata.get('completion_tokens', 0),
                'total_tokens': metadata.get('total_tokens', 0),
                'cost': metadata.get('cost', 0.0),
                'timestamp': timestamp,
                'output': results['documents'][i] if results.get('documents') else ''
            })
            
        logger.debug(f"Formatted {len(formatted_results)} results")
        return formatted_results

    @handle_chroma_errors
    def _get_templates_collection(self):
        """Get or create the templates collection with thread-safe access."""
        thread_id = threading.get_ident()
        
        # Check cache first
        with self._collection_cache_lock:
            if f"templates_{thread_id}" in self._collection_cache:
                return self._collection_cache[f"templates_{thread_id}"]
        
        # If not in cache, create new collection with proper locking
        with self._collection_lock:
            collection = self.client.get_or_create_collection(
                name="templates",
                metadata={"description": "Template storage for cheatsheets"}
            )
            
            # Update cache
            with self._collection_cache_lock:
                self._collection_cache[f"templates_{thread_id}"] = collection
            
            return collection

    @handle_chroma_errors
    def add_template(self, name: str, type: str, structure: str) -> str:
        """Add a new template to the database."""
        # Generate unique ID
        template_id = f"template_{datetime.now().timestamp()}"
        
        # Prepare metadata with ISO format timestamps
        now = datetime.now()
        template_metadata = {
            "name": name,
            "type": type,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat()
        }
        
        # Add to collection
        collection = self._get_templates_collection()
        collection.add(
            ids=[template_id],
            metadatas=[template_metadata],
            documents=[structure]
        )
        
        return template_id

    @handle_chroma_errors
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a template by ID."""
        collection = self._get_templates_collection()
        result = collection.get(ids=[template_id])
        
        if not result or not result['ids']:
            raise ValueError(f"Template not found: {template_id}")
            
        return {
            "id": result['ids'][0],
            "name": result['metadatas'][0]['name'],
            "type": result['metadatas'][0]['type'],
            "structure": result['documents'][0],
            "created_at": result['metadatas'][0]['created_at'],
            "updated_at": result['metadatas'][0]['updated_at']
        }

    @handle_chroma_errors
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """Get all templates with improved error handling."""
        try:
            if not hasattr(self, '_initialized') or not self._initialized:
                raise RuntimeError("ChromaDatabase not properly initialized")
                
            if not hasattr(self, 'client'):
                raise RuntimeError("ChromaDB client not initialized")
            
            collection = self._get_templates_collection()
            if not collection:
                logger.warning("Templates collection not found or could not be created")
                return []
                
            results = collection.get()
            if not results or not results.get('ids'):
                logger.debug("No templates found in collection")
                return []
            
            templates = []
            for i in range(len(results['ids'])):
                try:
                    templates.append({
                        "id": results['ids'][i],
                        "name": results['metadatas'][i]['name'],
                        "type": results['metadatas'][i]['type'],
                        "structure": results['documents'][i],
                        "created_at": results['metadatas'][i]['created_at'],
                        "updated_at": results['metadatas'][i]['updated_at']
                    })
                except (KeyError, IndexError) as e:
                    logger.error(f"Error processing template at index {i}: {e}")
                    continue
            
            return templates
        except Exception as e:
            logger.error(f"Error in get_all_templates: {e}")
            return []

    @handle_chroma_errors
    def delete_template(self, template_id: str) -> bool:
        """Delete a template."""
        try:
            # Get the templates collection
            collection = self._get_templates_collection()
            
            # Check if template exists before deleting
            result = collection.get(ids=[template_id])
            if not result or not result['ids']:
                logger.warning(f"Template not found for deletion: {template_id}")
                return False
            
            # Delete the template
            collection.delete(ids=[template_id])
            
            # Verify deletion
            verify_result = collection.get(ids=[template_id])
            if verify_result and verify_result['ids']:
                logger.error(f"Template deletion failed: {template_id} still exists")
                return False
            
            logger.info(f"Template deleted successfully: {template_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting template {template_id}: {e}")
            return False

    @handle_chroma_errors
    def update_template(self, template_id: str, name: str, type: str, structure: str) -> bool:
        """Update an existing template."""
        # Get the template collection
        collection = self._get_templates_collection()
        
        # Check if template exists
        result = collection.get(ids=[template_id])
        if not result or not result['ids']:
            raise ValueError(f"Template not found: {template_id}")
        
        # Get existing metadata to preserve created_at
        existing_metadata = result['metadatas'][0]
        
        # Prepare metadata with ISO format timestamps
        template_metadata = {
            "name": name,
            "type": type,
            "created_at": existing_metadata.get('created_at', datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
        
        # Update the template
        collection.update(
            ids=[template_id],
            metadatas=[template_metadata],
            documents=[structure]
        )
        
        return True

    def _ensure_token_logs_collection(self):
        """Ensure the token_logs collection exists with proper schema."""
        try:
            collection = self.client.get_or_create_collection(
                name="token_logs",
                metadata={
                    "description": "Token usage logs for OpenAI API calls",
                    "schema_timestamp": "float",
                    "schema_function_name": "str",
                    "schema_prompt_tokens": "int",
                    "schema_completion_tokens": "int",
                    "schema_total_tokens": "int",
                    "schema_cost": "float"
                }
            )
            return collection
        except Exception as e:
            logger.critical(f"Failed to ensure token_logs collection: {e}")
            raise

    @handle_chroma_errors
    def reset_templates_collection(self):
        """
        Reset the templates collection without deleting the database.
        This is useful for clearing all templates while maintaining the database structure.
        """
        try:
            with self._lock:
                # Delete the existing collection
                self.client.delete_collection("templates")
                
                # Recreate the collection
                self.client.create_collection(
                    name="templates",
                    metadata={"description": "Template storage for cheatsheets"}
                )
                
                # Clear collection cache for templates
                with self._collection_cache_lock:
                    # Remove all template-related entries from cache
                    keys_to_remove = [k for k in self._collection_cache.keys() if k.startswith("templates_")]
                    for key in keys_to_remove:
                        del self._collection_cache[key]
                
                # Persist changes
                if hasattr(self.client, 'persist'):
                    self.client.persist()
                
                logger.info("Templates collection reset completed successfully")
                return True
        except Exception as e:
            logger.error(f"Error resetting templates collection: {e}")
            return False 