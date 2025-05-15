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
    
    def classify_intent(self, query):
        """
        Classify the user query as conversational or information-seeking.
        
        Args:
            query (str): User query
            
        Returns:
            str: "conversational" or "information-seeking"
        """
        classification_prompt = f"""
        You are an AI assistant designed to classify user messages into exactly ONE of these categories:
        1. Conversational: Greetings, small talk, personal questions, opinions, etc.
        2. Information-Seeking: Questions requiring document search or specific knowledge about Egyptian history
        
        User message: "{query}"
        
        Respond with just the category name: either "conversational" or "information-seeking".
        """
        
        # Get classification from model
        response = self.llm.generate(classification_prompt, max_tokens=20)
        
        # Normalize response
        response = response.lower().strip()
        
        # Extract category
        if "conversational" in response:
            logger.info(f"Query classified as conversational: {query}")
            return "conversational"
        else:
            logger.info(f"Query classified as information-seeking: {query}")
            return "information-seeking"
    
    def generate_conversational_response(self, query, conversation_history=None):
        """
        Generate a conversational response without document retrieval.
        
        Args:
            query (str): User query
            conversation_history (list): Previous conversation exchanges
            
        Returns:
            dict: Response with answer
        """
        # Format conversation history
        formatted_history = ""
        if conversation_history and len(conversation_history) > 0:
            formatted_history = "Previous conversation:\n"
            for exchange in conversation_history:
                role = exchange["role"]
                content = exchange["content"]
                if role == "user":
                    formatted_history += f"Human: {content}\n"
                else:
                    formatted_history += f"Assistant: {content}\n"
            formatted_history += "\n"
        
        # Create the prompt
        prompt = f"""You are a friendly Egyptian history expert assistant. Respond conversationally to the following message.
        Do not mention documents or searching for information, just respond naturally as in a conversation.

        {formatted_history}
        Human: {query}

        Assistant:"""
        
        # Generate response
        answer = self.llm.generate(prompt)
        
        return {
            "answer": answer,
            "sources": [],
            "is_conversational": True
        }
    
    def generate_prompt(self, query, context):
        """
        Generate a prompt for the LLM based on the query and context.
        Enhanced to reduce hallucinations.
        
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
        
        # Create the enhanced prompt with strict instructions
        prompt = f"""Answer the following question based ONLY on the provided context. 

IMPORTANT INSTRUCTIONS:
1. If the exact answer is not explicitly stated in the context, respond with "I don't find specific information about this in the Egyptian history documents."
2. Do not use any prior knowledge.
3. If information in the documents conflicts, acknowledge this in your answer.
4. NEVER make up information or infer beyond what is explicitly stated.
5. No redundant information, information only said once.
6. Don't ever ever mention sources to the user.

Context:
{formatted_context}

Question: {query}

Answer:"""
        
        return prompt
    
    def generate_information_response(self, query, top_k=5):
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
                    "answer": "I couldn't find any relevant information about this in the Egyptian history documents.",
                    "sources": [],
                    "is_conversational": False
                }
            
            # Generate prompt
            prompt = self.generate_prompt(query, results)
            
            # Generate response
            answer = self.llm.generate(prompt)
            
            # Format sources with improved attribution
            sources = []
            for i, item in enumerate(results):
                chunk = item["chunk"]
                # Use original text if available (not the contextualized version)
                display_text = chunk.get("original_text", chunk["text"])
                
                sources.append({
                    "page": chunk["page_num"],
                    "text": display_text[:200] + "..." if len(display_text) > 200 else display_text,
                    "reference": f"[{i+1}]",  # Add reference number for footnote-style citations
                    "score": item["score"]
                })
            
            # Add footnote-style references to the answer
            footnoted_answer = answer
            for i, source in enumerate(sources):
                ref_marker = f"[{i+1}]"
                if ref_marker not in footnoted_answer:
                    # Only add reference if it's not already in the answer
                    relevant_text = source["text"][:30].replace("\n", " ")
                    if relevant_text in answer:
                        footnoted_answer = footnoted_answer.replace(
                            relevant_text, 
                            f"{relevant_text} {ref_marker}", 
                            1
                        )
            
            return {
                "answer": footnoted_answer,
                "sources": sources,
                "is_conversational": False
            }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"An error occurred: {str(e)}",
                "sources": [],
                "is_conversational": False
            }
    
    def generate_response(self, query, conversation_history=None, top_k=5):
        """
        Generate a response to the query using either conversational or RAG approach.
        
        Args:
            query (str): User query
            conversation_history (list): Previous conversation exchanges
            top_k (int): Number of top results to retrieve
            
        Returns:
            dict: Response with answer and sources
        """
        try:
            # Classify the query intent
            intent = self.classify_intent(query)
            
            # Generate appropriate response based on intent
            if intent == "conversational":
                return self.generate_conversational_response(query, conversation_history)
            else:
                return self.generate_information_response(query, top_k)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"An error occurred: {str(e)}",
                "sources": [],
                "is_conversational": False
            }

def main():
    parser = argparse.ArgumentParser(description="Generate a response to a query using RAG")
    parser.add_argument("query", help="User query")
    parser.add_argument("--pdf-name", help="Name of the PDF file (without extension)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to retrieve")
    parser.add_argument("--conversation-history", help="JSON string of conversation history")
    
    args = parser.parse_args()
    
    generator = Generator(pdf_name=args.pdf_name)
    
    # Parse conversation history if provided
    conversation_history = None
    if args.conversation_history:
        try:
            conversation_history = json.loads(args.conversation_history)
        except json.JSONDecodeError:
            logger.error("Failed to parse conversation history JSON")
    
    response = generator.generate_response(
        args.query, 
        conversation_history=conversation_history,
        top_k=args.top_k
    )
    
    print(json.dumps(response))

if __name__ == "__main__":
    main()
