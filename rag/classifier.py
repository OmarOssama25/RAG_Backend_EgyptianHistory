import logging
import json
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntentClassifier:
    def __init__(self, llm=None):
        """
        Initialize the intent classifier.
        
        Args:
            llm: LLM instance to use for classification (if None, one will be created)
        """
        if llm is None:
            # Import here to avoid circular imports
            sys.path.append('..')
            from models.llm import LLMModel
            self.llm = LLMModel()
        else:
            self.llm = llm
    
    def classify(self, query):
        """
        Classify the user query as conversational or information-seeking.
        
        Args:
            query (str): User query
            
        Returns:
            str: "conversational" or "information-seeking"
        """
        try:
            # Create classification prompt
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
                return "conversational"
            elif "information-seeking" in response:
                return "information-seeking"
            else:
                # Default to information-seeking for ambiguous cases
                logger.warning(f"Ambiguous classification: {response}. Defaulting to information-seeking.")
                return "information-seeking"
                
        except Exception as e:
            logger.error(f"Error classifying query: {str(e)}")
            # Default to information-seeking on error
            return "information-seeking"

# For testing
if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = sys.argv[1]
        classifier = IntentClassifier()
        result = classifier.classify(query)
        print(json.dumps({"classification": result}))
    else:
        print("Usage: python classifier.py 'your query here'")
