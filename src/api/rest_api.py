"""
REST API for the voice assistant
Allows external applications to interact with the assistant programmatically
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import asyncio
import threading
import queue

# Import our assistant components
from src.llm.gemma_wrapper import GemmaWrapper
from src.tts.pocket_tts import PocketTTS
from src.modules.home_control import HomeControlAPI

app = FastAPI(title="Local Voice Assistant API", version="0.1.0")


class UserInput(BaseModel):
    text: str
    context_id: Optional[str] = None


class HomeControlRequest(BaseModel):
    device_id: str
    action: str
    params: Optional[Dict[str, Any]] = {}


# Global instances of our components
assistant_llm = None
assistant_tts = None
home_control = None
conversation_contexts = {}  # Store conversation contexts by context_id


@app.on_event("startup")
async def startup_event():
    """Initialize components when the API starts"""
    global assistant_llm, assistant_tts, home_control
    
    print("Initializing assistant components...")
    
    # Initialize LLM (using a smaller model for API-based access)
    try:
        assistant_llm = GemmaWrapper(model_name="google/gemma-2b-it", quantize=True)
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        # Fallback to alternative model
        from src.llm.gemma_wrapper import DasDThinkingModel
        assistant_llm = DasDThinkingModel()
    
    assistant_tts = PocketTTS()
    home_control = HomeControlAPI()
    
    print("Assistant components initialized.")


@app.post("/chat", summary="Send text input to the assistant")
async def chat(input_data: UserInput):
    """
    Process user input and return assistant response
    """
    try:
        # Get or create conversation context
        context_id = input_data.context_id or "default"
        if context_id not in conversation_contexts:
            conversation_contexts[context_id] = []
        
        # Check if this is a home automation command
        if any(keyword in input_data.text.lower() for keyword in 
               ['light', 'turn on', 'turn off', 'temperature', 'thermostat', 'set']):
            response = handle_home_command(input_data.text, home_control)
        else:
            # Use the LLM for general conversation
            response = assistant_llm.generate_response(input_data.text)
        
        # Add to conversation context
        conversation_contexts[context_id].append({
            "role": "user",
            "content": input_data.text
        })
        conversation_contexts[context_id].append({
            "role": "assistant", 
            "content": response
        })
        
        # Keep context size manageable
        if len(conversation_contexts[context_id]) > 10:  # Keep last 10 exchanges
            conversation_contexts[context_id] = conversation_contexts[context_id][-10:]
        
        return {
            "response": response,
            "context_id": context_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.get("/devices", summary="List available smart home devices")
async def list_devices():
    """
    Get a list of available smart home devices
    """
    try:
        devices = home_control.discover_devices()
        return {"devices": devices}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving devices: {str(e)}")


@app.post("/home/control", summary="Control a smart home device")
async def control_home_device(request: HomeControlRequest):
    """
    Control a specific smart home device
    """
    try:
        success = home_control.control_device(
            request.device_id, 
            request.action, 
            request.params
        )
        
        if success:
            return {"status": "success", "message": f"Device {request.device_id} controlled successfully"}
        else:
            raise HTTPException(status_code=400, detail=f"Failed to control device {request.device_id}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error controlling device: {str(e)}")


@app.post("/tts", summary="Convert text to speech")
async def text_to_speech(input_data: UserInput):
    """
    Convert text to speech and play it
    """
    try:
        # In a real implementation, this might return an audio file
        # For now, we'll just trigger the speaking function
        assistant_tts.speak(input_data.text)
        
        return {"status": "success", "message": "Text spoken successfully"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error with TTS: {str(e)}")


@app.get("/health", summary="Check API health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "components": {
            "llm": "loaded" if assistant_llm is not None else "not loaded",
            "tts": "loaded" if assistant_tts is not None else "not loaded",
            "home_control": "loaded" if home_control is not None else "not loaded"
        }
    }


@app.get("/", summary="Root endpoint")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "Local Voice Assistant API",
        "version": "0.1.0",
        "endpoints": [
            {"method": "POST", "path": "/chat", "description": "Send text to assistant"},
            {"method": "GET", "path": "/devices", "description": "List smart home devices"},
            {"method": "POST", "path": "/home/control", "description": "Control home device"},
            {"method": "POST", "path": "/tts", "description": "Text to speech"},
            {"method": "GET", "path": "/health", "description": "Health check"}
        ]
    }


# Additional utility functions
def handle_home_command(command: str, home_control_api: HomeControlAPI) -> str:
    """
    Handle home automation commands
    """
    from src.modules.home_control import handle_home_command as home_handler
    return home_handler(command, home_control_api)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)