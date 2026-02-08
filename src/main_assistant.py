"""
Main voice assistant application
Integrates all components: hotword detection, STT, LLM, TTS, and modules
"""

import threading
import time
import queue
from typing import Callable, Optional

# Import our components
from src.hotword.wakeword_detector import WakeWordDetector
from src.tts.pocket_tts import PocketTTS, GemmaSTT, AudioInput
from src.llm.gemma_wrapper import GemmaWrapper
from src.modules.home_control import HomeControlAPI
from src.api.rest_api import handle_home_command


class LocalVoiceAssistant:
    """
    Main class that orchestrates all components of the voice assistant
    """
    
    def __init__(self, wake_word: str = "capri", llm_model: str = "google/gemma-2b-it"):
        self.wake_word = wake_word.lower()
        self.llm_model = llm_model
        
        # Initialize components
        self.wake_word_detector = WakeWordDetector(wake_word=self.wake_word)
        self.stt = GemmaSTT()  # Placeholder STT - in practice use Whisper tiny or similar
        self.tts = PocketTTS()
        self.llm = GemmaWrapper(model_name=llm_model, quantize=True)
        self.home_control = HomeControlAPI()
        self.audio_input = AudioInput()
        
        # Set up callback for wake word detection
        self.wake_word_detector.set_callback(self.on_wake_word_detected)
        
        # Conversation context
        self.conversation_history = []
        
        # Control flags
        self.is_running = False
        self.response_queue = queue.Queue()
        
        print(f"Voice assistant initialized with wake word: '{self.wake_word}'")
    
    def on_wake_word_detected(self):
        """
        Callback function triggered when wake word is detected
        """
        print("\nWake word detected! Listening for command...")
        
        # Record user command
        user_audio = self.audio_input.record_audio(duration=5)
        
        # Convert speech to text
        user_text = self.stt.transcribe(user_audio)
        print(f"Recognized: {user_text}")
        
        # Process the command
        self.process_command(user_text)
    
    def process_command(self, user_input: str):
        """
        Process the user's command and generate response
        """
        if not user_input or user_input.strip() == "":
            self.tts.speak("Sorry, I didn't catch that. Could you repeat?")
            return
        
        # Check if this is a home automation command
        is_home_command = any(keyword in user_input.lower() for keyword in 
                             ['light', 'turn on', 'turn off', 'temperature', 'thermostat', 'set'])
        
        if is_home_command:
            response = handle_home_command(user_input, self.home_control)
        else:
            # Use the LLM for general conversation
            response = self.llm.generate_response(user_input)
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_input})
        self.conversation_history.append({"role": "assistant", "content": response})
        
        # Keep history manageable
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Respond to user
        print(f"Assistant: {response}")
        self.tts.speak(response)
    
    def start(self):
        """
        Start the voice assistant
        """
        print("Starting voice assistant...")
        self.is_running = True
        
        try:
            # Start wake word detection in a separate thread
            detection_thread = threading.Thread(target=self.wake_word_detector.start_listening)
            detection_thread.daemon = True
            detection_thread.start()
            
            print(f"Assistant is now listening for wake word: '{self.wake_word}'")
            print("Press Ctrl+C to stop...")
            
            # Keep main thread alive
            while self.is_running:
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\nStopping voice assistant...")
            self.stop()
    
    def stop(self):
        """
        Stop the voice assistant
        """
        print("Stopping assistant...")
        self.is_running = False
        self.wake_word_detector.stop_listening()
        
        # Clean up resources
        self.llm.unload_model()
        
        print("Assistant stopped.")


def main():
    """
    Main entry point for the voice assistant
    """
    print("Initializing Local Voice Assistant...")
    
    # Create assistant instance
    assistant = LocalVoiceAssistant(
        wake_word="capri",  # Activation word
        llm_model="google/gemma-2b-it"  # Use the instruction-tuned model
    )
    
    try:
        # Start the assistant
        assistant.start()
    except Exception as e:
        print(f"Error running assistant: {e}")
        assistant.stop()


if __name__ == "__main__":
    main()