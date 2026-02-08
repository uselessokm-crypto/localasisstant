import numpy as np
import sounddevice as sd
from scipy import signal
import threading
import queue
import time

class WakeWordDetector:
    """
    Detects a specific wake word ('capri' in this case) using audio processing
    """
    
    def __init__(self, wake_word="capri", threshold=0.7, sample_rate=16000, chunk_size=1024):
        self.wake_word = wake_word.lower()
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.callback = None
        
        # Simple keyword spotting parameters
        self.energy_threshold = 0.01  # Minimum energy to consider audio
        self.silence_duration = 1.0   # Seconds of silence to reset detection
        
    def set_callback(self, callback_func):
        """Set callback function to be called when wake word is detected"""
        self.callback = callback_func
    
    def audio_callback(self, indata, frames, time, status):
        """Callback for audio stream"""
        if status:
            print(f"Audio status: {status}")
        
        # Add audio data to queue
        audio_data = indata.copy().flatten()
        self.audio_queue.put(audio_data)
    
    def detect_wake_word(self, audio_data):
        """
        Simple wake word detection based on energy and basic pattern matching
        In a real implementation, you'd use a proper wake word detection model
        """
        # Calculate energy of the audio segment
        energy = np.mean(np.abs(audio_data)**2)
        
        # Simple check - if energy is above threshold, we consider it possible speech
        if energy > self.energy_threshold:
            # In a real implementation, you would use a dedicated wake word model here
            # For now, we'll simulate detection by returning True occasionally
            # when the audio energy is significant
            return energy > (self.energy_threshold * 3)  # Arbitrary multiplier for demo
            
        return False
    
    def start_listening(self):
        """Start listening for the wake word"""
        self.is_listening = True
        print(f"Listening for wake word: '{self.wake_word}'...")
        
        # Start audio stream
        with sd.InputStream(callback=self.audio_callback, 
                           channels=1, 
                           samplerate=self.sample_rate,
                           blocksize=self.chunk_size):
            
            last_detection_time = time.time()
            
            while self.is_listening:
                try:
                    # Get audio data from queue
                    if not self.audio_queue.empty():
                        audio_chunk = self.audio_queue.get_nowait()
                        
                        # Check for wake word
                        if self.detect_wake_word(audio_chunk):
                            current_time = time.time()
                            
                            # Prevent multiple detections in short interval
                            if current_time - last_detection_time > 2.0:
                                print(f"Wake word '{self.wake_word}' detected!")
                                
                                if self.callback:
                                    self.callback()  # Call the registered callback
                                
                                last_detection_time = current_time
                
                except queue.Empty:
                    time.sleep(0.01)  # Small delay to prevent busy waiting
                except Exception as e:
                    print(f"Error in wake word detection: {e}")
                    break
    
    def stop_listening(self):
        """Stop listening for the wake word"""
        self.is_listening = False