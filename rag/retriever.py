import os
import sys
import logging
import numpy as np
import json
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.embedding import EmbeddingModel
from rag.utils import get_vector_store_dir

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Retriever:
    def __init__(self, pdf_name, top_k=5):
        """
        Initialize the retriever.
        
        Args:
            pdf_name (str): Name of the PDF file (without extension)
            top_k (int): Number of top results to retrieve
        """
        self.pdf_name = pdf_name
        self.top_k = top_k
        self.embedding_model = EmbeddingModel()
        self.vector_store_dir = get_vector_store_dir()
        
        self.vector_file = os.path.join(self.vector_store_dir, f"{self.pdf_name}_vectors.npz")
        self.metadata_file = os.path.join(self.vector_store_dir, f"{self.pdf_name}_metadata.json")
        
        self.embeddings = None
        self.metadata = None
    
    def load_vectors(self):
        """
        Load embeddings and metadata from disk.
        
        Returns:
            bool: Success status
        """
        try:
            if not os.path.exists(self.vector_file) or not os.path.exists(self.metadata_file):
                logger.error(f"Vector files not found for {self.pdf_name}")
                return False
            
            logger.info(f"Loading vectors from {self.vector_file}")
            self.embeddings = np.load(self.vector_file)["embeddings"]
            
            logger.info(f"Loading metadata from {self.metadata_file}")
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
            
            logger.info(f"Loaded {len(self.metadata)} chunks with embeddings shape {self.embeddings.shape}")
            return True
        except Exception as e:
            logger.error(f"Error loading vectors: {str(e)}")
            return False
    
    def search(self, query, top_k=None):
        """
        Search for relevant chunks based on the query.
        
        Args:
            query (str): Query text
            top_k (int): Number of top results to retrieve (overrides instance value)
            
        Returns:
            list: List of relevant chunks with metadata and scores
        """
        try:
            if self.embeddings is None or self.metadata is None:
                if not self.load_vectors():
                    return []
            
            # Use instance top_k if not specified
            if top_k is None:
                top_k = self.top_k
            
            # Generate query embedding
            query_embedding = self.embedding_model.get_query_embedding(query)
            if query_embedding is None:
                logger.error("Failed to generate query embedding")
                return []
            
            # Calculate similarity scores
            similarity_scores = np.dot(self.embeddings, query_embedding)
            
            # Get top k indices
            top_indices = np.argsort(similarity_scores)[-top_k:][::-1]
            
            # Get top k chunks with scores
            results = []
            for idx in top_indices:
                chunk = self.metadata[idx]
                score = float(similarity_scores[idx])
                results.append({
                    "chunk": chunk,
                    "score": score
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching: {str(e)}")
            return []

def main():
    if len(sys.argv) < 3:
        print("Usage: python retriever.py <pdf_name> <query>")
        sys.exit(1)
    
    pdf_name = sys.argv[1]
    query = sys.argv[2]
    
    retriever = Retriever(pdf_name)
    results = retriever.search(query)
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()