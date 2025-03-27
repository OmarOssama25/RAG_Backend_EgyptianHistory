import os
import logging
import sys
import urllib.request
from pathlib import Path
from tqdm import tqdm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Custom progress bar for downloads
class DownloadProgressBar(tqdm):
    def update_to(self, b=1, bsize=1, tsize=None):
        if tsize is not None:
            self.total = tsize
        self.update(b * bsize - self.n)

def download_url(url, output_path):
    with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=url.split('/')[-1]) as t:
        urllib.request.urlretrieve(url, filename=output_path, reporthook=t.update_to)

class LLMModel:
    def __init__(self, model_name="phi-2", model_path=None):
        """
        Initialize the LLM model.
        
        Args:
            model_name (str): Name of the model to use
            model_path (str): Path to store the model
        """
        self.model_name = model_name
        self.home_dir = str(Path.home())
        self.model_path = model_path or os.path.join(self.home_dir, "phi2_model")
        self.model_loaded = False
        
    def download_model(self):
        """
        Download the Phi-2 model using transformers.
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.model_path, exist_ok=True)
            
            logger.info(f"Installing required packages for Phi-2...")
            
            # Install required packages
            try:
                import pip
                pip.main(['install', 'transformers', 'accelerate', 'torch', 'einops', 'tqdm'])
                logger.info("Required packages installed successfully")
            except Exception as e:
                logger.error(f"Error installing packages: {str(e)}")
                return False
            
            logger.info(f"Phi-2 model will be downloaded automatically when first loaded")
            return True
                
        except Exception as e:
            logger.error(f"Error in setup process: {str(e)}")
            return False
    
    def load_model(self):
        """
        Load the model for inference.
        """
        try:
            # First make sure required packages are installed
            try:
                import transformers
                import torch
            except ImportError:
                logger.info("Required packages not found. Installing...")
                if not self.download_model():
                    return False
            
            # Import here to avoid loading dependencies unless needed
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
            
            logger.info("Loading Phi-2 model and tokenizer...")
            
            # Check if CUDA is available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Using device: {device}")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained("microsoft/phi-2", trust_remote_code=True)
            
            # Load model with appropriate settings based on available hardware
            if device == "cuda":
                # For GPU: load in 8-bit if possible
                try:
                    import bitsandbytes as bnb
                    logger.info("Loading model in 8-bit quantization...")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        "microsoft/phi-2",
                        torch_dtype=torch.float16,
                        load_in_8bit=True,
                        device_map="auto",
                        trust_remote_code=True
                    )
                except ImportError:
                    # If bitsandbytes is not available, load in fp16
                    logger.info("Loading model in fp16...")
                    self.model = AutoModelForCausalLM.from_pretrained(
                        "microsoft/phi-2",
                        torch_dtype=torch.float16,
                        device_map="auto",
                        trust_remote_code=True
                    )
            else:
                # For CPU: load in fp32
                logger.info("Loading model on CPU...")
                self.model = AutoModelForCausalLM.from_pretrained(
                    "microsoft/phi-2",
                    device_map={"": device},
                    trust_remote_code=True
                )
            
            self.model_loaded = True
            logger.info("Phi-2 model loaded successfully")
            return True
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            return False
    
    def generate(self, prompt, max_tokens=512, temperature=0.7, top_p=0.9):
        """
        Generate text based on the prompt.
        
        Args:
            prompt (str): Input prompt
            max_tokens (int): Maximum number of tokens to generate
            temperature (float): Sampling temperature
            top_p (float): Top-p sampling parameter
            
        Returns:
            str: Generated text
        """
        if not self.model_loaded:
            if not self.load_model():
                return "Error: Failed to load the model."
        
        try:
            import torch
            
            # Format the prompt for Phi-2
            formatted_prompt = f"Instruct: {prompt}\nOutput:"
            
            # Tokenize the prompt
            inputs = self.tokenizer(formatted_prompt, return_tensors="pt").to(self.model.device)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=True,
                    pad_token_id=self.tokenizer.eos_token_id
                )
            
            # Decode the generated tokens
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the response part
            if "Output:" in generated_text:
                response = generated_text.split("Output:")[1].strip()
            else:
                response = generated_text.replace(formatted_prompt, "").strip()
                
            return response
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            return f"Error: {str(e)}"

# For testing
if __name__ == "__main__":
    # Print startup message
    print("Initializing Phi-2 model for testing...")
    print("This will download the model if it's not already cached (~1.5GB)")
    print("Please be patient during first-time setup.")
    
    # Initialize and test the model
    llm = LLMModel()
    response = llm.generate("Tell me about ancient Egypt and its pharaohs.")
    print("\nResponse from Phi-2:")
    print("-" * 50)
    print(response)
    print("-" * 50)