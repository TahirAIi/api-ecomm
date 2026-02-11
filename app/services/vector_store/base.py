from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from uuid import UUID


class VectorStore(ABC):
    """
    Abstract base class for vector stores.
    This allows easy swapping between different vector databases
    (Milvus, Pinecone, Weaviate, etc.)
    """

    @abstractmethod
    def initialize_collection(self, collection_name: str, dimension: int) -> None:
        """
        Initialize or create a collection in the vector store.

        Args:
            collection_name: Name of the collection
            dimension: Dimension of the vectors
        """
        pass

    @abstractmethod
    def insert_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        ids: List[UUID],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        """
        Insert vectors into the collection.

        Args:
            collection_name: Name of the collection
            vectors: List of embedding vectors
            ids: List of product UUIDs corresponding to vectors
            metadatas: Optional list of metadata dictionaries
        """
        pass

    @abstractmethod
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        expr: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search for similar vectors.

        Args:
            collection_name: Name of the collection
            query_vector: The query embedding vector
            limit: Maximum number of results to return
            score_threshold: Optional minimum similarity score threshold

        Returns:
            List of dictionaries containing:
            - id: Product UUID
            - score: Similarity score
            - metadata: Optional metadata
        """
        pass

    @abstractmethod
    def delete_vectors(self, collection_name: str, ids: List[UUID]) -> None:
        """
        Delete vectors by their IDs.

        Args:
            collection_name: Name of the collection
            ids: List of product UUIDs to delete
        """
        pass

    @abstractmethod
    def update_vector(
        self,
        collection_name: str,
        vector_id: UUID,
        vector: List[float],
        metadata: Optional[Dict] = None,
    ) -> None:
        """
        Update a single vector.

        Args:
            collection_name: Name of the collection
            vector_id: Product UUID
            vector: New embedding vector
            metadata: Optional updated metadata
        """
        pass

    @abstractmethod
    def collection_exists(self, collection_name: str) -> bool:
        """
        Check if a collection exists.

        Args:
            collection_name: Name of the collection

        Returns:
            True if collection exists, False otherwise
        """
        pass
