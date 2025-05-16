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
    def __init__(self, pdf_name=None, times_name=None):
        """
        Initialize the generator.
        
        Args:
            pdf_name (str): Name of the PDF file (without extension)
            times_name (str): Name of the times/schedule data file (without extension)
        """
        self.pdf_name = pdf_name or "egyptian_history"
        self.times_name = times_name or "monument_data"
        self.llm = LLMModel()
        self.retriever = Retriever(self.pdf_name, self.times_name)
    
    def classify_intent(self, query):
        """
        Classify the user query as conversational, information-seeking, or schedule-seeking.
        
        Args:
            query (str): User query
            
        Returns:
            str: "conversational", "information-seeking", or "schedule-seeking".
        """
        classification_prompt = f"""
        Task: Classify the user query into exactly ONE category.
        
        Categories:
        - "conversational": General chat, greetings, small talk, personal questions, opinions
        - "information-seeking": Questions about Egyptian history, facts, or specific knowledge that requires document search
        - "schedule-seeking": Requests for visiting schedules, planning a trip, or itinerary suggestions for Egyptian monuments/locations
        
        Examples:
        - "Hello, how are you?" → "conversational"
        - "Tell me about Egyptian pyramids" → "information-seeking"
        - "What's a good schedule for visiting Cairo on Sunday?" → "schedule-seeking"
        - "Can you help me plan a trip to Alexandria on Tuesday?" → "schedule-seeking"
        - "When was the Great Pyramid built?" → "information-seeking"
        
        User query: "{query}"
        
        Classification (respond with exactly one word - conversational, information-seeking, or schedule-seeking):
        """
        
        # Get classification from model
        response = self.llm.generate(classification_prompt, max_tokens=20)
        
        # Normalize response
        response = response.lower().strip()
        
        # Extract category
        if "conversational" in response:
            logger.info(f"Query classified as conversational: {query}")
            return "conversational"
        elif "schedule-seeking" in response:
            logger.info(f"Query classified as schedule-seeking: {query}")
            return "schedule-seeking"
        else:
            logger.info(f"Query classified as information-seeking: {query}")
            return "information-seeking"
    
    def get_schedule_parameters(self, query):
        """
        Extract filter parameters from schedule-seeking query.
        
        Args:
            query (str): User query
            
        Returns:
            dict: Contains 'city' and 'day' keys if successful, or 'error' key if failed
        """
        
        parameter_prompt = f"""
        Extract the following parameters from the user's query about visiting Egyptian monuments or locations:
        
        1. City: The Egyptian city mentioned in the query (e.g., Cairo, Alexandria, Luxor, Aswan, Giza)
        2. Day: The day of the week mentioned (e.g., Monday, Tuesday, etc.)
        
        User query: "{query}"
        
        Format your response EXACTLY as follows with NO additional text:
        city=<extracted city>;day=<extracted day>
        
        If either parameter is missing, respond with the appropriate error code:
        - If no city is mentioned or it's unclear: error=missing_city
        - If the city is not in Egypt: error=city_not_in_egypt
        - If no day is mentioned or it's unclear: error=missing_day
        """
        
        response = self.llm.generate(parameter_prompt, max_tokens=50).strip()
        
        # Parse response
        if response.startswith("error="):
            error_type = response.split("=")[1].strip()
            return {"error": error_type}
        
        try:
            # Convert "city=cairo;day=sunday" to {"city": "cairo", "day": "sunday"}
            params = {}
            for pair in response.split(";"):
                if "=" in pair:
                    key, value = pair.split("=", 1)
                    params[key.strip().lower()] = value.strip().lower()
            
            # Validate required parameters
            if "city" not in params:
                return {"error": "missing_city"}
            if "day" not in params:
                return {"error": "missing_day"}
                
            return {
                "city": params["city"],
                "day": params["day"]
            }
        except Exception as e:
            logger.error(f"Error parsing parameters: {str(e)}")
            return {"error": "invalid_format"}
    
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
                role = exchange.get("role", "")
                content = exchange.get("content", "")
                if role == "user":
                    formatted_history += f"Human: {content}\n"
                else:
                    formatted_history += f"Assistant: {content}\n"
            formatted_history += "\n"
        
        # Create the prompt
        prompt = f"""You are a friendly Egyptian history expert assistant. Respond conversationally to the following message.
        Your tone should be warm and helpful. Focus on creating a natural conversation flow.

        {formatted_history}
        Human: {query}

        Assistant:"""
        
        # Generate response
        answer = self.llm.generate(prompt)
        
        return {
            "answer": answer,
            "sources": [],
            "query_type": "conversational"
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
            text = chunk["text"]
            page_num = chunk.get("page_num", "N/A")
            
            formatted_context += f"[Document {i+1}] (Page {page_num}):\n{text}\n\n"
        
        # Create the enhanced prompt with strict instructions
        prompt = f"""You are an expert on Egyptian history answering a question based on specific documents.

TASK: Answer the following question using ONLY information from the provided context.

CONTEXT:
{formatted_context}

GUIDELINES:
- Answer based ONLY on the provided context documents
- If the information isn't in the context, say: "I don't find specific information about this in the Egyptian history documents."
- Avoid mentioning the sources or documents in your answer
- Focus on providing accurate, concise information
- If information conflicts between sources, acknowledge this in your answer

QUESTION: {query}

ANSWER:"""
        
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
                    "query_type": "information-seeking"
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
                    "page": chunk.get("page_num", "N/A"),
                    "text": chunk["text"][:200] + "..." if len(chunk["text"]) > 200 else chunk["text"]
                })
            
            return {
                "answer": answer,
                "sources": sources,
                "query_type": "information-seeking"
            }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"An error occurred: {str(e)}",
                "sources": [],
                "query_type": "information-seeking"
            }
    
    def generate_schedule_response(self, query):
        """
        Generate a schedule response for Egyptian monument visits.
        
        Args:
            query (str): User query
            
        Returns:
            dict: Response with schedule information or error
        """
        try:
            # Step 1: Extract parameters from query
            parameters = self.get_schedule_parameters(query)
            
            # Step 2: Handle parameter errors
            if "error" in parameters:
                error_msg = {
                    "missing_city": "I need to know which Egyptian city you want to visit. Could you specify the city?",
                    "missing_day": "I need to know which day of the week you plan to visit. Could you specify the day?",
                    "city_not_in_egypt": "I can only provide schedules for cities in Egypt. Please specify an Egyptian city.",
                    "invalid_format": "I couldn't understand your request. Please specify which Egyptian city and day you want to visit."
                }.get(parameters["error"], "There was an error understanding your request.")
                
                return {
                    "answer": error_msg,
                    "query_type": "schedule-seeking"
                }
            
            # Step 3: Get relevant location data from the retriever
            results = self.retriever.getTimes(query, parameters["city"])
            
            if not results or len(results) == 0:
                return {
                    "answer": f"I don't have information about monuments or locations in {parameters['city']}. Could you try another Egyptian city?",
                    "query_type": "schedule-seeking"
                }
            
            # Step 4: Create an optimized schedule using extracted parameters and location data
            schedule_prompt = f"""
            Create an optimized one-day tour schedule for visiting monuments in {parameters['city']} on {parameters['day']}.
            
            Available locations and their opening hours:
            {json.dumps([{
                "location": item["Location"],
                "hours": item["Time"]
            } for item in results], indent=2)}
            
            Follow these guidelines:
            1. Start the day at 8:00 AM and end by 6:00 PM
            2. Include 3-5 major attractions based on proximity
            3. Allow appropriate travel time between locations (15-30 minutes)
            4. Include a lunch break around noon (1 hour)
            5. Allocate realistic visiting times for each location (1-2 hours)
            6. Consider the opening hours of each location
            7. You are a friendly tour guide assistant. Do not ever mention anything about entries or guidelines and speak like a normal human would. 

            Format your response as a complete schedule with times, locations, and brief descriptions.
            """
            
            # Generate the schedule
            schedule_response = self.llm.generate(schedule_prompt)
            
            return {
                "answer": schedule_response,
                "city": parameters["city"],
                "day": parameters["day"],
                "query_type": "schedule-seeking"
            }
            
        except Exception as e:
            logger.error(f"Error generating schedule: {str(e)}")
            return {
                "answer": f"I couldn't create a schedule at this time. Please try again with specific Egyptian city and day information.",
                "query_type": "schedule-seeking"
            }

    def generate_response(self, query, conversation_history=None, top_k=5):
        """
        Generate a response to the query using either conversational, information-seeking or schedule-seeking approach.
        
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
            elif intent == "information-seeking":
                return self.generate_information_response(query, top_k)
            elif intent == "schedule-seeking":
                return self.generate_schedule_response(query)
            else:
                # Fallback to information-seeking as default
                return self.generate_information_response(query, top_k)
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "answer": f"I'm sorry, I encountered an error while processing your request. Could you try rephrasing your question?",
                "sources": [],
                "query_type": "error"
            }

def main():
    parser = argparse.ArgumentParser(description="Generate a response to a query using RAG")
    parser.add_argument("query", help="User query")
    parser.add_argument("--pdf-name", help="Name of the PDF file (without extension)")
    parser.add_argument("--times-name", help="Name of the file containing the time database (without extension)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of top results to retrieve")
    parser.add_argument("--conversation-history", help="JSON string of conversation history")
    
    args = parser.parse_args()
    
    generator = Generator(pdf_name=args.pdf_name, times_name=args.times_name)
    
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