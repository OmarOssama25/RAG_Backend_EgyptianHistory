import os
import sys
import logging
import json
import argparse
from pathlib import Path

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.llm import LLMModel
from rag.retriever import Retriever
from rag.utils import get_data_dir

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Generator:
    def __init__(self, pdf_name=None):
        """
        Initialize the generator.
        
        Args:
            pdf_name (str): Name of the PDF file (without extension)
        """
        self.pdf_name = pdf_name or "egyptian_history"
        self.llm = LLMModel()
        self.retriever = Retriever(self.pdf_name)
    
    def generate_prompt(self, query, context):
        """
        Generate a prompt for the LLM based on the query and context.
        
        Args:
            query (str): User query
            context (list): List of context chunks
            
        Returns:
            str: Formatted prompt
        """
        # Format context
        formatted_context = ""
        for i, item in enumerate(context):
            chunk = item["chunk"]
            score = item["score"]
            text = chunk["text"]
            page_num = chunk["page_num"]
            
            formatted_context += f"[Document {i+1}] (Page {page_num}):\n{text}\n\n"
        
        # Create the prompt
        prompt = f"""Answer the following question based on the provided context. If the answer cannot be found in the context, say so.

Context:
{formatted_context}

Question: {query}

Answer:"""
        
        return prompt
    
    def generate_response(self, query, top_k=5):
        """
        Generate a response to the query using RAG.
        
        Args:
            query (str): User query
            top_k (int): Number of top results to retrieve
            
        Returns:
            dict: Response with answer and sources
        """
        try:
            # Retrieve relevant chunks
            results = self.retriever.search(query, top_k=top_k)
            
            if not results:
                return {
                    "answer": "I couldn't find any relevant information to answer your question.",
                    "sources": []
                }
            
            # Generate prompt
            prompt = self.generate_prompt(query, results)
            
            # Generate response
            answer = self.llm.generate(prompt)
            
            # Format sources
            sources = []
            for item in results:
                chunk = item["chunk"]
                sources.append({
                    "page": chunk["page_num"],
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                })
            
            return {
                "answer": answer,
                "sources": sources
            }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"An error occurred: {str(e)}",
                "sources": []
            }

def main():
    parser = argparse.ArgumentParser(description="Generate a response to a query using RAG")
    parser.add_argument("query", help="User query")
    parser.add_argument("--pdf-name", help="Name of the PDF file (without extension)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to retrieve")
    
    args = parser.parse_args()
    
    generator = Generator(pdf_name=args.pdf_name)
    response = generator.generate_response(args.query, top_k=args.top_k)
    
    print(json.dumps(response))

if __name__ == "__main__":
    main()