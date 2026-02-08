"""
Module for home automation control
This module provides interfaces to control smart home devices
"""

import json
import requests
from typing import Dict, List, Optional


class HomeControlAPI:
    """
    Interface for controlling smart home devices
    This is a modular component that can be enabled/disabled as needed
    """
    
    def __init__(self, config_file: str = "home_config.json"):
        self.config_file = config_file
        self.devices = {}
        self.load_config()
    
    def load_config(self):
        """
        Load home automation configuration from file
        """
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.devices = config.get('devices', {})
        except FileNotFoundError:
            print(f"Configuration file {self.config_file} not found. Using default settings.")
            self.devices = {}
        except json.JSONDecodeError:
            print(f"Invalid JSON in {self.config_file}. Using default settings.")
            self.devices = {}
    
    def discover_devices(self) -> List[Dict]:
        """
        Discover available smart home devices
        """
        # In a real implementation, this would scan the network for devices
        # For now, return the configured devices
        discovered = []
        for device_id, device_info in self.devices.items():
            discovered.append({
                'id': device_id,
                'name': device_info.get('name', device_id),
                'type': device_info.get('type', 'unknown'),
                'status': device_info.get('status', 'offline')
            })
        
        return discovered
    
    def control_device(self, device_id: str, action: str, params: Optional[Dict] = None) -> bool:
        """
        Control a specific device
        
        Args:
            device_id: ID of the device to control
            action: Action to perform (on, off, set, etc.)
            params: Additional parameters for the action
        """
        if device_id not in self.devices:
            print(f"Device {device_id} not found in configuration")
            return False
        
        device_info = self.devices[device_id]
        device_type = device_info.get('type', 'generic')
        
        # Determine how to control the device based on its type and protocol
        if device_info.get('protocol') == 'http':
            return self._control_http_device(device_info, action, params)
        elif device_info.get('protocol') == 'mqtt':
            return self._control_mqtt_device(device_info, action, params)
        else:
            print(f"Unsupported protocol for device {device_id}")
            return False
    
    def _control_http_device(self, device_info: Dict, action: str, params: Optional[Dict]) -> bool:
        """
        Control a device via HTTP API
        """
        try:
            url = device_info.get('url', '')
            headers = device_info.get('headers', {})
            payload = {
                'action': action,
                'params': params or {}
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=5)
            return response.status_code == 200
        except requests.RequestException as e:
            print(f"Error controlling HTTP device: {e}")
            return False
    
    def _control_mqtt_device(self, device_info: Dict, action: str, params: Optional[Dict]) -> bool:
        """
        Control a device via MQTT
        Note: This requires the paho-mqtt library
        """
        try:
            import paho.mqtt.publish as publish
            
            mqtt_config = device_info.get('mqtt', {})
            topic = mqtt_config.get('topic', f"home/{device_info.get('id')}/{action}")
            payload = json.dumps({
                'action': action,
                'params': params or {}
            })
            
            auth = mqtt_config.get('auth')
            if auth:
                auth_tuple = {'username': auth.get('username'), 'password': auth.get('password')}
            else:
                auth_tuple = None
            
            publish.single(
                topic,
                payload=payload,
                hostname=mqtt_config.get('host', 'localhost'),
                port=mqtt_config.get('port', 1883),
                auth=auth_tuple,
                client_id=f"voice_assistant_{device_info.get('id')}"
            )
            
            return True
        except ImportError:
            print("paho-mqtt library not installed for MQTT control")
            return False
        except Exception as e:
            print(f"Error controlling MQTT device: {e}")
            return False
    
    def get_device_status(self, device_id: str) -> Optional[Dict]:
        """
        Get the status of a specific device
        """
        if device_id not in self.devices:
            return None
        
        # In a real implementation, this would query the device for its status
        # For now, return the stored status
        return self.devices[device_id].get('status')
    
    def toggle_light(self, light_id: str) -> bool:
        """
        Convenience method to toggle a light
        """
        current_status = self.get_device_status(light_id)
        if current_status == 'on':
            return self.control_device(light_id, 'off')
        else:
            return self.control_device(light_id, 'on')
    
    def set_brightness(self, light_id: str, brightness: int) -> bool:
        """
        Set brightness of a light (0-100)
        """
        if not 0 <= brightness <= 100:
            print("Brightness must be between 0 and 100")
            return False
        
        return self.control_device(light_id, 'set', {'brightness': brightness})
    
    def set_temperature(self, thermostat_id: str, temperature: float) -> bool:
        """
        Set temperature of a thermostat
        """
        return self.control_device(thermostat_id, 'set', {'temperature': temperature})


# Example usage and integration with voice assistant
def handle_home_command(command: str, home_control: HomeControlAPI) -> str:
    """
    Parse and execute home automation commands
    This function would be called by the main assistant when a home control command is detected
    """
    command_lower = command.lower()
    
    # Light control examples
    if "turn on" in command_lower and "light" in command_lower:
        # Extract light name from command - simplified parsing
        if "bedroom" in command_lower:
            success = home_control.toggle_light("bedroom_light")
            return "Bedroom light turned on." if success else "Failed to control bedroom light."
        elif "living room" in command_lower or "livingroom" in command_lower:
            success = home_control.toggle_light("living_room_light")
            return "Living room light turned on." if success else "Failed to control living room light."
        else:
            return "Which light would you like me to turn on?"
    
    elif "turn off" in command_lower and "light" in command_lower:
        if "bedroom" in command_lower:
            success = home_control.toggle_light("bedroom_light")
            return "Bedroom light turned off." if success else "Failed to control bedroom light."
        elif "living room" in command_lower or "livingroom" in command_lower:
            success = home_control.toggle_light("living_room_light")
            return "Living room light turned off." if success else "Failed to control living room light."
        else:
            return "Which light would you like me to turn off?"
    
    elif "set brightness" in command_lower or ("dim" in command_lower and "light" in command_lower):
        # Extract brightness level (simplified)
        if "low" in command_lower or "dim" in command_lower:
            brightness = 30
        elif "medium" in command_lower:
            brightness = 60
        elif "high" in command_lower or "bright" in command_lower:
            brightness = 100
        else:
            # Try to extract numeric value
            import re
            numbers = re.findall(r'\d+', command)
            brightness = int(numbers[0]) if numbers else 50
        
        success = home_control.set_brightness("bedroom_light", brightness)
        return f"Brightness set to {brightness}%." if success else "Failed to set brightness."
    
    elif "set temperature" in command_lower or "thermostat" in command_lower:
        import re
        numbers = re.findall(r'\d+', command)
        if numbers:
            temp = float(numbers[0])
            success = home_control.set_temperature("thermostat_main", temp)
            return f"Temperature set to {temp}°F." if success else "Failed to set temperature."
        else:
            return "What temperature would you like to set?"
    
    else:
        return "I'm not sure how to handle that home automation command."


# Example configuration structure
EXAMPLE_CONFIG = {
    "devices": {
        "bedroom_light": {
            "name": "Bedroom Light",
            "type": "light",
            "protocol": "http",
            "url": "http://192.168.1.100/api/light/bedroom",
            "headers": {"Authorization": "Bearer YOUR_TOKEN"},
            "status": "off"
        },
        "living_room_light": {
            "name": "Living Room Light",
            "type": "light",
            "protocol": "mqtt",
            "mqtt": {
                "host": "192.168.1.200",
                "port": 1883,
                "topic": "home/living_room/light",
                "auth": {
                    "username": "mqtt_user",
                    "password": "mqtt_pass"
                }
            },
            "status": "off"
        },
        "thermostat_main": {
            "name": "Main Thermostat",
            "type": "thermostat",
            "protocol": "http",
            "url": "http://192.168.1.150/api/thermostat",
            "headers": {"Authorization": "Bearer YOUR_TOKEN"},
            "status": "idle"
        }
    }
}


if __name__ == "__main__":
    # Example usage
    home_api = HomeControlAPI()
    
    # Print available devices
    devices = home_api.discover_devices()
    print("Available devices:", devices)
    
    # Example command handling
    response = handle_home_command("turn on bedroom light", home_api)
    print(response)