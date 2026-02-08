# Local Voice Assistant

A privacy-focused, locally-run voice assistant similar to Alexa or Cortana that runs on consumer hardware with limited resources (4GB RAM).

## Features

- **Wake Word Detection**: Activate the assistant with a customizable wake word (default: "capri")
- **Lightweight LLM**: Uses small models like Gemma 2B that can run on CPU with limited RAM
- **Modular Architecture**: Pluggable components for different capabilities
- **Home Automation**: Control smart home devices via HTTP/MQTT APIs
- **API Access**: REST API for programmatic access
- **Local Processing**: All processing happens on-device, no cloud required

## Requirements

- Python 3.8+
- At least 4GB RAM (8GB recommended for better performance)
- Linux/macOS (Windows support may require additional configuration)
- Microphone and speakers for voice interaction

## Installation

1. Clone this repository
2. Install system dependencies:
   ```bash
   sudo apt-get install portaudio19-dev python3-pyaudio  # On Debian/Ubuntu
   ```
3. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Voice Mode
```bash
python run_assistant.py --mode voice
```
The assistant will listen for the wake word "capri" and respond to voice commands.

### API Mode
```bash
python run_assistant.py --mode api --port 8000
```
Access the API at `http://localhost:8000` with documentation at `http://localhost:8000/docs`

## Configuration

### Home Automation
To configure home automation devices, create a `home_config.json` file in the project root:

```json
{
  "devices": {
    "bedroom_light": {
      "name": "Bedroom Light",
      "type": "light",
      "protocol": "http",
      "url": "http://192.168.1.100/api/light/bedroom",
      "headers": {"Authorization": "Bearer YOUR_TOKEN"},
      "status": "off"
    }
  }
}
```

## Models Supported

The system is designed to work with various lightweight models:

- **Gemma 2B/7B**: Google's efficient open models
- **Alternative models**: Can be swapped in the LLM wrapper

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Wake Word     │───▶│   Speech-to-Text │───▶│     LLM         │
│   Detection     │    │       (STT)      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌──────────────────┐    ┌───────▼─────────┐
│   Text-to-Speech│◀───│   Response       │◀───│   Modules       │
│       (TTS)     │    │   Generation     │    │ (Home Control, │
└─────────────────┘    └──────────────────┘    │  Calendar, etc.)│
                                              └─────────────────┘
```

## API Endpoints

When running in API mode, the following endpoints are available:

- `GET /` - API information
- `POST /chat` - Send text to assistant
- `GET /devices` - List smart home devices  
- `POST /home/control` - Control home device
- `POST /tts` - Text to speech
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation

## Customization

### Changing the Wake Word
Edit the `wake_word` parameter in `src/main_assistant.py`.

### Adding New Modules
Create new modules in the `src/modules/` directory following the same pattern as `home_control.py`.

## Performance Tips

- Use quantized models to reduce memory usage
- Adjust model parameters for faster inference
- Consider using a dedicated audio interface for better voice detection

## Limitations

- Accuracy depends on ambient noise conditions
- Response time varies based on hardware specifications
- Wake word detection is basic (production systems should use dedicated models)

## Roadmap

- Improved wake word detection
- Better speech recognition
- Support for more home automation protocols
- Voice biometric authentication