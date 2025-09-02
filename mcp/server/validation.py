from functools import wraps
from typing import Callable, Any, Dict, Tuple, List
import logging

logger = logging.getLogger("MCPValidation")

class ValidationError(ValueError):
    """Custom exception for validation errors."""
    pass

def validate_range(name: str, value: Any, min_val: float, max_val: float):
    """Validate that a value is within a given range."""
    if not isinstance(value, (int, float)):
        raise ValidationError(f"Parameter '{name}' must be a number.")
    if not (min_val <= value <= max_val):
        raise ValidationError(f"Parameter '{name}' must be between {min_val} and {max_val}.")

def validate_type(name: str, value: Any, expected_type: type):
    """Validate that a value is of a specific type."""
    if not isinstance(value, expected_type):
        raise ValidationError(f"Parameter '{name}' must be of type {expected_type.__name__}.")

def validate_list_of(name: str, value: Any, item_type: type):
    """Validate that a value is a list of a specific type."""
    if not isinstance(value, list):
        raise ValidationError(f"Parameter '{name}' must be a list.")
    for item in value:
        if not isinstance(item, item_type):
            raise ValidationError(f"All items in list '{name}' must be of type {item_type.__name__}.")

def validate_not_empty(name: str, value: Any):
    """Validate that a value is not empty."""
    if not value:
        raise ValidationError(f"Parameter '{name}' cannot be empty.")

def validate_notes(name: str, value: Any):
    """Validate the structure of a list of MIDI notes."""
    validate_list_of(name, value, dict)
    for i, note in enumerate(value):
        if not all(k in note for k in ["pitch", "start_time", "duration", "velocity"]):
            raise ValidationError(f"Note at index {i} in '{name}' is missing required keys.")
        validate_range(f"{name}[{i}].pitch", note["pitch"], 0, 127)
        validate_range(f"{name}[{i}].velocity", note["velocity"], 0, 127)
        validate_type(f"{name}[{i}].start_time", note["start_time"], (int, float))
        validate_type(f"{name}[{i}].duration", note["duration"], (int, float))

def get_validated_tool(tool_func: Callable) -> Callable:
    """
    Decorator to add input validation to a tool function based on its signature.
    """
    @wraps(tool_func)
    def wrapper(ctx, **kwargs):
        sig = tool_func.__annotations__
        for name, expected_type in sig.items():
            if name in ['return', 'ctx']:
                continue

            if name not in kwargs:
                # This should be caught by the MCP framework, but we check just in case
                raise ValidationError(f"Missing required parameter: '{name}'")

            value = kwargs[name]

            # Simple type validation
            if expected_type == int:
                validate_type(name, value, int)
            elif expected_type == float:
                validate_type(name, value, (int, float))
            elif expected_type == str:
                validate_type(name, value, str)
            elif expected_type == bool:
                validate_type(name, value, bool)
            elif hasattr(expected_type, '__origin__') and expected_type.__origin__ == list:
                item_type = expected_type.__args__[0]
                if item_type == int:
                    validate_list_of(name, value, int)
                elif item_type == dict:
                    validate_list_of(name, value, dict)
                # Add more list item types if needed

            # Parameter-specific validation rules
            if name == "track_index":
                validate_range(name, value, 0, 999) # Assuming max 999 tracks
            if name == "device_index":
                validate_range(name, value, 0, 127) # Assuming max 127 devices per track
            if name == "clip_index":
                validate_range(name, value, 0, 999) # Assuming max 999 clips per track
            if name == "scene_index":
                validate_range(name, value, -1, 999) # -1 is valid for create_scene
            if name == "parameter_name" or name == "name" or name == "description" or name == "query" or name == "filepath" or name == "uri" or name == "path" or name == "genre":
                validate_not_empty(name, value)
            if name == "value":
                # This is generic, but we can add context-specific validation if needed
                validate_type(name, value, (int, float))
            if name == "volume":
                validate_range(name, value, 0.0, 1.0)
            if name == "panning":
                validate_range(name, value, -1.0, 1.0)
            if name == "send_index":
                validate_range(name, value, 0, 11) # Ableton has 12 sends (0-11)
            if name == "color":
                validate_type(name, value, int)
            if name == "index":
                validate_range(name, value, -1, 999)
            if name == "notes":
                validate_notes(name, value)
            if name == "channel":
                validate_range(name, value, 0, 15)
            if name == "note":
                validate_range(name, value, 0, 127)
            if name == "velocity":
                validate_range(name, value, 0, 127)
            if name == "length" or name == "tempo":
                validate_range(name, value, 0.0, 999.0)
            if name == "category_type":
                validate_type(name, value, str)
            if name == "is_looping":
                validate_type(name, value, bool)
            if name == "description":
                validate_not_empty(name, value)


        try:
            return tool_func(ctx, **kwargs)
        except ValidationError as e:
            logger.error(f"Validation failed for tool '{tool_func.__name__}': {e}")
            return f"Validation Error: {e}"
        except Exception as e:
            logger.error(f"Error executing tool '{tool_func.__name__}': {e}")
            return f"Error: {e}"

    return wrapper
