from abc import ABC, abstractmethod
from typing import List


class EmbeddingService(ABC):
    """
    Abstract base class for embedding services.
    This allows easy swapping between different embedding providers
    (Gemini, OpenAI, Cohere, etc.)
    """

    @abstractmethod
    def generate_embedding(
        self, text: str, task_type: str = "retrieval_document"
    ) -> List[float]:
        """
        Generate an embedding vector for a single text.

        Args:
            text: The text to embed
            task_type: Optional task type (e.g., "retrieval_document" for products, "retrieval_query" for queries)

        Returns:
            A list of floats representing the embedding vector
        """
        pass

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """
        Get the dimension of embeddings produced by this service.

        Returns:
            The dimension of the embedding vectors
        """
        pass
