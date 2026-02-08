import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import gc
import warnings
warnings.filterwarnings("ignore")

class GemmaWrapper:
    """
    Wrapper for Gemma models (2B or 7B) optimized for local execution
    Supports both 2B and 7B variants with quantization for better performance on limited hardware
    """
    
    def __init__(self, model_name="unsloth/gemma-3n-E2B-it-GGUF", quantize=True):
        self.model_name = model_name
        self.quantize = quantize
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        self.llm_pipeline = None
        
        print(f"Initializing LLM on device: {self.device}")
        self.load_model()
    
    def load_model(self):
        """
        Load the Gemma model with optional quantization
        """
        print(f"Loading model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        
        # Set pad token if not present
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Configure model loading with quantization if enabled
        model_kwargs = {
            "torch_dtype": torch.bfloat16 if self.device.type == "cuda" else torch.float32,
            "device_map": "auto" if self.device.type == "cuda" else None
        }
        
        # Apply quantization if enabled and CUDA is available
        if self.quantize and self.device.type == "cuda":
            try:
                from transformers import BitsAndBytesConfig
                model_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4"
                )
            except ImportError:
                print("BitsAndBytes not available, loading without quantization")
                pass
        
        # Load model
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **model_kwargs
        )
        
        # Create text generation pipeline
        self.llm_pipeline = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            device_map="auto" if self.device.type == "cuda" else None,
            torch_dtype=torch.bfloat16 if self.device.type == "cuda" else torch.float32,
            max_new_tokens=256,
            do_sample=True,
            temperature=0.7,
            top_k=50,
            top_p=0.95
        )
        
        print(f"Model loaded successfully on {self.device}")
    
    def generate_response(self, prompt: str, max_length: int = 512, temperature: float = 0.7):
        """
        Generate response from the model based on the input prompt
        """
        if not self.llm_pipeline:
            raise RuntimeError("Model not properly initialized")
        
        # Format the prompt according to Gemma requirements
        formatted_prompt = f"<start_of_turn>user\n{prompt}<end_of_turn>\n<start_of_turn>model\n"
        
        try:
            # Generate response
            outputs = self.llm_pipeline(
                formatted_prompt,
                max_new_tokens=max_length,
                temperature=temperature,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            response = outputs[0]['generated_text']
            
            # Remove the original prompt from the response
            response = response[len(formatted_prompt):]
            
            # Take only the model's response part (before next user turn)
            if "<end_of_turn>" in response:
                response = response.split("<end_of_turn>")[0]
            
            return response.strip()
        
        except Exception as e:
            print(f"Error generating response: {e}")
            return "Sorry, I couldn't process that request."
    
    def chat(self, user_input: str, context: list = None):
        """
        Maintain a conversation context with the model
        """
        if context is None:
            context = []
        
        # Build conversation history
        conversation = ""
        for msg in context:
            role = msg['role']
            content = msg['content']
            if role == 'user':
                conversation += f"<start_of_turn>user\n{content}<end_of_turn>\n"
            elif role == 'assistant':
                conversation += f"<start_of_turn>model\n{content}<end_of_turn>\n"
        
        # Add current user input
        conversation += f"<start_of_turn>user\n{user_input}<end_of_turn>\n<start_of_turn>model\n"
        
        try:
            outputs = self.llm_pipeline(
                conversation,
                max_new_tokens=256,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            response = outputs[0]['generated_text']
            response = response[len(conversation):]
            
            # Take only the model's response part
            if "<end_of_turn>" in response:
                response = response.split("<end_of_turn>")[0]
            
            return response.strip()
        
        except Exception as e:
            print(f"Error in chat: {e}")
            return "Sorry, I couldn't process that request."
    
    def clear_memory(self):
        """
        Clear GPU memory cache
        """
        if self.device.type == "cuda":
            with torch.no_grad():
                torch.cuda.empty_cache()
            gc.collect()
    
    def unload_model(self):
        """
        Unload the model to free memory
        """
        self.model = None
        self.tokenizer = None
        self.llm_pipeline = None
        
        if self.device.type == "cuda":
            torch.cuda.empty_cache()
        
        gc.collect()


class DasDThinkingModel:
    """
    Alternative lightweight model implementation if Gemma proves too heavy
    This is a placeholder for alternative approaches like distilled models
    """
    
    def __init__(self, model_name="microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None
        
        print(f"Loading alternative model: {self.model_name}")
        self.load_model()
    
    def load_model(self):
        """
        Load a lighter alternative model
        """
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(self.model_name)
        
        # Add padding token if missing
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def generate_response(self, prompt: str):
        """
        Generate response using the alternative model
        """
        inputs = self.tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model.generate(
                inputs,
                max_length=len(inputs[0]) + 100,
                num_return_sequences=1,
                do_sample=True,
                temperature=0.7
            )
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        response = response[len(prompt):].strip()
        
        # Truncate at the first newline or sentence boundary
        if '\n' in response:
            response = response.split('\n')[0]
        
        return response