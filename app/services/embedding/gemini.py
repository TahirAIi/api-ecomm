from typing import List
from google import genai
from app.services.embedding.base import EmbeddingService
from app.core.config import settings


class GeminiEmbeddingService(EmbeddingService):
    def __init__(self):
        api_key = settings.GEMINI_API_KEY

        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-embedding-001"
        self._dimension = 768

    def generate_embedding(
        self,
        text: dict,
        task_type: str = "retrieval_document",
        config: genai.types.EmbedContentConfig = None,
    ) -> List[float]:
        try:
            if config is None:
                config = genai.types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=self._dimension,
                    title=text["title"],
                )
            result = self.client.models.embed_content(
                model=self.model, contents=text["text"], config=config
            )
            if result.embeddings and len(result.embeddings) > 0:
                return result.embeddings[0].values
            else:
                raise RuntimeError("No embeddings returned from API")
        except Exception as e:
            raise RuntimeError(f"Failed to generate embedding: {str(e)}")

    def generate_query_embedding(self, text: str) -> List[float]:
        config = genai.types.EmbedContentConfig(
            task_type="retrieval_query", output_dimensionality=self._dimension
        )
        return self.generate_embedding({"text": text}, "retrieval_query", config)

    def get_embedding_dimension(self) -> int:
        return self._dimension
