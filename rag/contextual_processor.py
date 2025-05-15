import os
import sys
import logging
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.llm import LLMModel

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("contextual_processor")

class ContextualProcessor:
    def __init__(self):
        """Initialize the contextual processor."""
        self.llm = LLMModel()
    
    def add_context_to_chunk(self, chunk, document_text):
        """
        Add contextual information to a chunk using the LLM.
        
        Args:
            chunk (dict): The chunk to contextualize
            document_text (str): The full document text
            
        Returns:
            dict: The contextualized chunk
        """
        try:
            # Create a prompt for the LLM to generate context
            prompt = f"""
            <document>
            {document_text[:10000]}  # Limit document size to avoid token limits
            </document>

            Here is the chunk we want to situate within the whole document:
            <chunk>
            {chunk['text']}
            </chunk>

            Please give a short succinct context (2-3 sentences) to situate this chunk within the overall document 
            for the purposes of improving search retrieval of the chunk. 
            Answer only with the succinct context and nothing else.
            """
            
            # Generate contextual information
            context = self.llm.generate(prompt, max_tokens=100).strip()
            logger.info(f"Generated context: {context[:50]}...")
            
            # Create a new chunk with context prepended
            contextualized_text = f"{context}\n\n{chunk['text']}"
            
            # Return updated chunk
            contextualized_chunk = chunk.copy()
            contextualized_chunk['text'] = contextualized_text
            contextualized_chunk['original_text'] = chunk['text']
            contextualized_chunk['context'] = context
            
            return contextualized_chunk
        except Exception as e:
            logger.error(f"Error adding context to chunk: {str(e)}")
            return chunk  # Return original chunk if contextualization fails
