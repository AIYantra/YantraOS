import logging
import asyncio
from typing import List, Dict, Any

from yantra.config import get_settings

logger = logging.getLogger(__name__)

class VectorMemory:
    """
    Manages vector representations of state and actions in ChromaDB.
    Runs persistently inside the local deployment.
    """
    def __init__(self):
        self.settings = get_settings()
        self.collection_name = "yantra_memory_v1"
        self._init_task = None
        self._collection = None
        self._init_failed = False
        
    async def initialize(self):
        """Asynchronously initialize the ChromaDB connection."""
        if self._collection is not None or self._init_failed:
            return
            
        try:
            # We defer import to gracefully handle missing dependencies in live environment
            import chromadb
            
            # Simple async wrapper for synchronous chromadb init
            loop = asyncio.get_running_loop()
            
            def _blocking_init():
                client = chromadb.PersistentClient(path="/var/lib/yantra/chroma")
                return client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
                
            self._collection = await loop.run_in_executor(None, _blocking_init)
            logger.info(f"MEMORY: Vector DB initialized -> [collection: {self.collection_name}]")
            
        except ImportError:
            logger.warning("MEMORY: VectorMemory is DEGRADED - 'chromadb' package not installed.")
            self._init_failed = True
        except Exception as e:
            logger.warning(f"MEMORY: VectorMemory is DEGRADED - ChromaDB init failed on startup ({str(e)})")
            self._init_failed = True

    async def _require_initialized(self):
        if not self._collection and not self._init_failed:
            await self.initialize()

    async def store_state(self, state: Dict[str, Any], importance: float = 1.0):
        """Store a complex state document with its metadata into the DB."""
        await self._require_initialized()
        if self._init_failed:
            return
            
        import uuid
        
        doc_id = str(uuid.uuid4())
        
        loop = asyncio.get_running_loop()
        def _blocking_add():
            self._collection.add(
                documents=[str(state)],
                metadatas=[{"importance": importance}],
                ids=[doc_id]
            )
            
        try:
            await loop.run_in_executor(None, _blocking_add)
            logger.debug(f"State stored in vector DB ({doc_id})")
        except Exception as e:
            logger.error(f"Failed to store state in vector db: {e}")

    async def recall_similar(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """Query memory for similar past states or contexts."""
        await self._require_initialized()
        if self._init_failed:
            return []
            
        loop = asyncio.get_running_loop()
        def _blocking_query():
            return self._collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
        try:    
            results = await loop.run_in_executor(None, _blocking_query)
            return results.get("documents", [])[0] if results.get("documents") else []
        except Exception as e:
            logger.error(f"Memory recall failed: {e}")
            return []
