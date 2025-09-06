# MCP_Server/server.py
from mcp.server.fastmcp import FastMCP, Context
from .midi_client import MidiClient
from .socket_midi_server import SocketMidiServer
from mcp.server.validation import get_validated_tool
from mcp.server.music_theory import chord_to_midi, parse_chord_name, NOTES
import socket
import json
import logging
import os
from dataclasses import dataclass
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, List, Union
from functools import wraps

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("AbletonMCPServer")

@dataclass
class AbletonConnection:
    host: str
    port: int
    sock: socket.socket = None

    def connect(self) -> bool:
        """Connect to the Ableton Remote Script socket server"""
        if self.sock:
            return True

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.host, self.port))
            logger.info(f"Connected to Ableton at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Ableton: {str(e)}")
            self.sock = None
            return False

    def disconnect(self):
        """Disconnect from the Ableton Remote Script"""
        if self.sock:
            try:
                self.sock.close()
            except Exception as e:
                logger.error(f"Error disconnecting from Ableton: {str(e)}")
            finally:
                self.sock = None

    def receive_full_response(self, sock, buffer_size=8192):
        """Receive the complete response, potentially in multiple chunks"""
        chunks = []
        sock.settimeout(15.0)  # Increased timeout for operations that might take longer

        try:
            while True:
                try:
                    chunk = sock.recv(buffer_size)
                    if not chunk:
                        if not chunks:
                            raise Exception("Connection closed before receiving any data")
                        break

                    chunks.append(chunk)

                    # Check if we've received a complete JSON object
                    try:
                        data = b''.join(chunks)
                        json.loads(data.decode('utf-8'))
                        logger.info(f"Received complete response ({len(data)} bytes)")
                        return data
                    except json.JSONDecodeError:
                        # Incomplete JSON, continue receiving
                        continue
                except socket.timeout:
                    logger.warning("Socket timeout during chunked receive")
                    break
                except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                    logger.error(f"Socket connection error during receive: {str(e)}")
                    raise
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise

        # If we get here, we either timed out or broke out of the loop
        if chunks:
            data = b''.join(chunks)
            logger.info(f"Returning data after receive completion ({len(data)} bytes)")
            try:
                json.loads(data.decode('utf-8'))
                return data
            except json.JSONDecodeError:
                raise Exception("Incomplete JSON response received")
        else:
            raise Exception("No data received")

    def send_command(self, command_type: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Send a command to Ableton and return the response"""
        if not self.sock and not self.connect():
            raise ConnectionError("Not connected to Ableton")

        command = {
            "type": command_type,
            "params": params or {}
        }

        # Check if this is a state-modifying command
        is_modifying_command = command_type in [
            "create_midi_track", "create_audio_track", "set_track_name",
            "create_clip", "add_notes_to_clip", "set_clip_name",
            "set_tempo", "fire_clip", "stop_clip", "set_device_parameter",
            "start_playback", "stop_playback", "load_instrument_or_effect"
        ]

        try:
            logger.info(f"Sending command: {command_type} with params: {params}")

            # Send the command
            self.sock.sendall(json.dumps(command).encode('utf-8'))
            logger.info(f"Command sent, waiting for response...")

            # For state-modifying commands, add a small delay to give Ableton time to process
            if is_modifying_command:
                import time
                time.sleep(0.1)  # 100ms delay

            # Set timeout based on command type
            timeout = 15.0 if is_modifying_command else 10.0
            self.sock.settimeout(timeout)

            # Receive the response
            response_data = self.receive_full_response(self.sock)
            logger.info(f"Received {len(response_data)} bytes of data")

            # Parse the response
            response = json.loads(response_data.decode('utf-8'))
            logger.info(f"Response parsed, status: {response.get('status', 'unknown')}")

            if response.get("status") == "error":
                logger.error(f"Ableton error: {response.get('message')}")
                raise Exception(response.get("message", "Unknown error from Ableton"))

            # For state-modifying commands, add another small delay after receiving response
            if is_modifying_command:
                import time
                time.sleep(0.1)  # 100ms delay

            return response.get("result", {})
        except socket.timeout:
            logger.error("Socket timeout while waiting for response from Ableton")
            self.sock = None
            raise Exception("Timeout waiting for Ableton response")
        except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
            logger.error(f"Socket connection error: {str(e)}")
            self.sock = None
            raise Exception(f"Connection to Ableton lost: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response from Ableton: {str(e)}")
            if 'response_data' in locals() and response_data:
                logger.error(f"Raw response (first 200 bytes): {response_data[:200]}")
            self.sock = None
            raise Exception(f"Invalid response from Ableton: {str(e)}")
        except Exception as e:
            logger.error(f"Error communicating with Ableton: {str(e)}")
            self.sock = None
            raise Exception(f"Communication error with Ableton: {str(e)}")

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage server startup and shutdown lifecycle"""
    global _midi_client, _socket_midi_server
    try:
        logger.info("AbletonMCP server starting up")

        try:
            ableton = get_ableton_connection()
            logger.info("Successfully connected to Ableton on startup")
        except Exception as e:
            logger.warning(f"Could not connect to Ableton on startup: {str(e)}")
            logger.warning("Make sure the Ableton Remote Script is running")

        _midi_client = MidiClient()
        _socket_midi_server = SocketMidiServer()
        _socket_midi_server.start()

        yield {}
    finally:
        global _ableton_connection
        if _ableton_connection:
            logger.info("Disconnecting from Ableton on shutdown")
            _ableton_connection.disconnect()
            _ableton_connection = None

        if _midi_client:
            logger.info("Disconnecting from MIDI client on shutdown")
            _midi_client.disconnect()
            _midi_client = None

        if _socket_midi_server:
            logger.info("Stopping Socket MIDI server on shutdown")
            _socket_midi_server.stop()
            _socket_midi_server.join()
            _socket_midi_server = None

        logger.info("AbletonMCP server shut down")

# Create the MCP server with lifespan support
mcp = FastMCP(
    "AbletonMCP",
    lifespan=server_lifespan
)

# Global connection for resources
_ableton_connection = None
_midi_client = None
_socket_midi_server = None

def get_ableton_connection():
    """Get or create a persistent Ableton connection"""
    global _ableton_connection

    if _ableton_connection is not None:
        try:
            # Test the connection with a simple ping
            # We'll try to send an empty message, which should fail if the connection is dead
            # but won't affect Ableton if it's alive
            _ableton_connection.sock.settimeout(1.0)
            _ableton_connection.sock.sendall(b'')
            return _ableton_connection
        except Exception as e:
            logger.warning(f"Existing connection is no longer valid: {str(e)}")
            try:
                _ableton_connection.disconnect()
            except:
                pass
            _ableton_connection = None

    # Connection doesn't exist or is invalid, create a new one
    if _ableton_connection is None:
        # Try to connect up to 3 times with a short delay between attempts
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Connecting to Ableton (attempt {attempt}/{max_attempts})...")
                _ableton_connection = AbletonConnection(host="localhost", port=9877)
                if _ableton_connection.connect():
                    logger.info("Created new persistent connection to Ableton")

                    # Validate connection with a simple command
                    try:
                        # Get session info as a test
                        _ableton_connection.send_command("get_session_info")
                        logger.info("Connection validated successfully")
                        return _ableton_connection
                    except Exception as e:
                        logger.error(f"Connection validation failed: {str(e)}")
                        _ableton_connection.disconnect()
                        _ableton_connection = None
                        # Continue to next attempt
                else:
                    _ableton_connection = None
            except Exception as e:
                logger.error(f"Connection attempt {attempt} failed: {str(e)}")
                if _ableton_connection:
                    _ableton_connection.disconnect()
                    _ableton_connection = None

            # Wait before trying again, but only if we have more attempts left
            if attempt < max_attempts:
                import time
                time.sleep(1.0)

        # If we get here, all connection attempts failed
        if _ableton_connection is None:
            logger.error("Failed to connect to Ableton after multiple attempts")
            raise Exception("Could not connect to Ableton. Make sure the Remote Script is running.")

    return _ableton_connection


# Core Tool endpoints

@mcp.tool()
@get_validated_tool
def get_session_info(ctx: Context) -> str:
    """Get detailed information about the current Ableton session"""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_session_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting session info from Ableton: {str(e)}")
        return f"Error getting session info: {str(e)}"

@mcp.tool()
@get_validated_tool
def get_track_info(ctx: Context, track_index: int) -> str:
    """
    Get detailed information about a specific track in Ableton.

    Parameters:
    - track_index: The index of the track to get information about
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_track_info", {"track_index": track_index})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting track info from Ableton: {str(e)}")
        return f"Error getting track info: {str(e)}"

@mcp.tool()
@get_validated_tool
def get_device_details(ctx: Context, track_index: int, device_index: int) -> str:
    """
    Get detailed information about a specific device on a track.

    Parameters:
    - track_index: The index of the track where the device is located
    - device_index: The index of the device on the track
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_device_details", {
            "track_index": track_index,
            "device_index": device_index
        })
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting device details from Ableton: {str(e)}")
        return f"Error getting device details: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_device_parameter(ctx: Context, track_index: int, device_index: int, parameter_name: str, value: float) -> str:
    """
    Set a parameter on a device.

    Parameters:
    - track_index: The index of the track where the device is located
    - device_index: The index of the device on the track
    - parameter_name: The name of the parameter to set
    - value: The new value for the parameter
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_device_parameter", {
            "track_index": track_index,
            "device_index": device_index,
            "parameter_name": parameter_name,
            "value": value
        })
        return f"Set parameter '{parameter_name}' on device {device_index} of track {track_index} to {value}"
    except Exception as e:
        logger.error(f"Error setting device parameter: {str(e)}")
        return f"Error setting device parameter: {str(e)}"

@mcp.tool()
@get_validated_tool
def get_scene_info(ctx: Context) -> str:
    """Get information about all scenes"""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_scene_info")
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error getting scene info: {str(e)}")
        return f"Error getting scene info: {str(e)}"

@mcp.tool()
@get_validated_tool
def fire_scene(ctx: Context, scene_index: int) -> str:
    """
    Fire a scene.

    Parameters:
    - scene_index: The index of the scene to fire
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("fire_scene", {"scene_index": scene_index})
        return f"Fired scene {scene_index}"
    except Exception as e:
        logger.error(f"Error firing scene: {str(e)}")
        return f"Error firing scene: {str(e)}"

@mcp.tool()
@get_validated_tool
def create_scene(ctx: Context, scene_index: int = -1) -> str:
    """
    Create a new scene.

    Parameters:
    - scene_index: The index to create the scene at (-1 for end)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_scene", {"scene_index": scene_index})
        return f"Created scene at index {scene_index}"
    except Exception as e:
        logger.error(f"Error creating scene: {str(e)}")
        return f"Error creating scene: {str(e)}"

@mcp.tool()
@get_validated_tool
def rename_scene(ctx: Context, scene_index: int, name: str) -> str:
    """
    Rename a scene.

    Parameters:
    - scene_index: The index of the scene to rename
    - name: The new name for the scene
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("rename_scene", {"scene_index": scene_index, "name": name})
        return f"Renamed scene {scene_index} to '{name}'"
    except Exception as e:
        logger.error(f"Error renaming scene: {str(e)}")
        return f"Error renaming scene: {str(e)}"

@mcp.tool()
@get_validated_tool
def delete_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Delete a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("delete_clip", {"track_index": track_index, "clip_index": clip_index})
        return f"Deleted clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error deleting clip: {str(e)}")
        return f"Error deleting clip: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_clip_color(ctx: Context, track_index: int, clip_index: int, color: int) -> str:
    """
    Set the color of a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - color: The new color for the clip (as an integer)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_color", {"track_index": track_index, "clip_index": clip_index, "color": color})
        return f"Set color of clip at track {track_index}, slot {clip_index} to {color}"
    except Exception as e:
        logger.error(f"Error setting clip color: {str(e)}")
        return f"Error setting clip color: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_volume(ctx: Context, track_index: int, volume: float) -> str:
    """
    Set the volume of a track.

    Parameters:
    - track_index: The index of the track to set the volume for
    - volume: The new volume for the track (0.0 to 1.0)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_volume", {"track_index": track_index, "volume": volume})
        return f"Set volume of track {track_index} to {volume}"
    except Exception as e:
        logger.error(f"Error setting volume: {str(e)}")
        return f"Error setting volume: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_panning(ctx: Context, track_index: int, panning: float) -> str:
    """
    Set the panning of a track.

    Parameters:
    - track_index: The index of the track to set the panning for
    - panning: The new panning for the track (-1.0 to 1.0)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_panning", {"track_index": track_index, "panning": panning})
        return f"Set panning of track {track_index} to {panning}"
    except Exception as e:
        logger.error(f"Error setting panning: {str(e)}")
        return f"Error setting panning: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_send(ctx: Context, track_index: int, send_index: int, value: float) -> str:
    """
    Set the send level of a track.

    Parameters:
    - track_index: The index of the track to set the send level for
    - send_index: The index of the send to set
    - value: The new send level (0.0 to 1.0)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_send", {"track_index": track_index, "send_index": send_index, "value": value})
        return f"Set send {send_index} of track {track_index} to {value}"
    except Exception as e:
        logger.error(f"Error setting send: {str(e)}")
        return f"Error setting send: {str(e)}"

@mcp.tool()
@get_validated_tool
def create_midi_track(ctx: Context, index: int = -1) -> str:
    """
    Create a new MIDI track in the Ableton session.

    Parameters:
    - index: The index to insert the track at (-1 = end of list)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_midi_track", {"index": index})
        return f"Created new MIDI track: {result.get('name', 'unknown')}"
    except Exception as e:
        logger.error(f"Error creating MIDI track: {str(e)}")
        return f"Error creating MIDI track: {str(e)}"

@mcp.tool()
@get_validated_tool
def create_audio_track(ctx: Context, index: int = -1) -> str:
    """
    Create a new audio track in the Ableton session.

    Parameters:
    - index: The index to insert the track at (-1 = end of list)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_audio_track", {"index": index})
        return f"Created new audio track: {result.get('name', 'unknown')}"
    except Exception as e:
        logger.error(f"Error creating audio track: {str(e)}")
        return f"Error creating audio track: {str(e)}"

@mcp.tool()
@get_validated_tool
def create_return_track(ctx: Context) -> str:
    """Create a new return track in the Ableton session."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_return_track")
        return f"Created new return track: {result.get('name', 'unknown')}"
    except Exception as e:
        logger.error(f"Error creating return track: {str(e)}")
        return f"Error creating return track: {str(e)}"

@mcp.tool()
@get_validated_tool
def delete_track(ctx: Context, track_index: int) -> str:
    """
    Delete a track.

    Parameters:
    - track_index: The index of the track to delete
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("delete_track", {"track_index": track_index})
        return f"Deleted track {track_index}"
    except Exception as e:
        logger.error(f"Error deleting track: {str(e)}")
        return f"Error deleting track: {str(e)}"

@mcp.tool()
@get_validated_tool
def search_browser(ctx: Context, query: str) -> str:
    """
    Search the browser for items matching the query.

    Parameters:
    - query: The search query
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("search_browser", {"query": query})
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Error searching browser: {str(e)}")
        return f"Error searching browser: {str(e)}"

@mcp.tool()
@get_validated_tool
def group_tracks(ctx: Context, track_indices: List[int]) -> str:
    """
    Group tracks together.

    Parameters:
    - track_indices: A list of track indices to group
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("group_tracks", {"track_indices": track_indices})
        return f"Grouped tracks {track_indices} into new track '{result.get('name', 'unknown')}'"
    except Exception as e:
        logger.error(f"Error grouping tracks: {str(e)}")
        return f"Error grouping tracks: {str(e)}"

@mcp.tool()
@get_validated_tool
def generate_midi(ctx: Context, track_index: int, clip_index: int, description: str) -> str:
    """
    Generates a MIDI clip based on a description.

    Parameters:
    - track_index: The index of the track to create the clip on
    - clip_index: The index of the clip slot to create the clip in
    - description: A description of the MIDI to generate (e.g., "a simple C major scale")
    """
    try:
        # For now, we'll just parse the description in a very simple way.
        # In the future, this could be replaced with a call to an LLM.
        notes = []
        if "c major scale" in description.lower():
            notes = [
                {"pitch": 60, "start_time": 0.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 62, "start_time": 0.5, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 64, "start_time": 1.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 65, "start_time": 1.5, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 67, "start_time": 2.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 69, "start_time": 2.5, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 71, "start_time": 3.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 72, "start_time": 3.5, "duration": 0.5, "velocity": 100, "mute": False},
            ]
        else:
            return "I'm sorry, I can only generate a C major scale right now."

        ableton = get_ableton_connection()

        # First, create a new clip
        ableton.send_command("create_clip", {"track_index": track_index, "clip_index": clip_index, "length": 4.0})

        # Then, add the notes to the clip
        result = ableton.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })

        return f"Generated MIDI clip with {len(notes)} notes on track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error generating MIDI: {str(e)}")
        return f"Error generating MIDI: {str(e)}"

@mcp.tool()
@get_validated_tool
def send_note_on(ctx: Context, channel: int, note: int, velocity: int) -> str:
    """
    Send a MIDI note-on message.

    Parameters:
    - channel: The MIDI channel (0-15)
    - note: The MIDI note number (0-127)
    - velocity: The note velocity (0-127)
    """
    try:
        if not _midi_client:
            raise Exception("MIDI client not initialized")
        _midi_client.send_note_on(channel, note, velocity)
        return f"Sent note on: channel={channel}, note={note}, velocity={velocity}"
    except Exception as e:
        logger.error(f"Error sending note on: {str(e)}")
        return f"Error sending note on: {str(e)}"

@mcp.tool()
@get_validated_tool
def send_note_off(ctx: Context, channel: int, note: int) -> str:
    """
    Send a MIDI note-off message.

    Parameters:
    - channel: The MIDI channel (0-15)
    - note: The MIDI note number (0-127)
    """
    try:
        if not _midi_client:
            raise Exception("MIDI client not initialized")
        _midi_client.send_note_off(channel, note)
        return f"Sent note off: channel={channel}, note={note}"
    except Exception as e:
        logger.error(f"Error sending note off: {str(e)}")
        return f"Error sending note off: {str(e)}"

@mcp.tool()
@get_validated_tool
def get_midi_messages(ctx: Context) -> str:
    """Get any MIDI messages received from Ableton since the last call."""
    try:
        if not _socket_midi_server:
            raise Exception("Socket MIDI server not initialized")
        messages = _socket_midi_server.get_messages()
        return json.dumps(messages, indent=2)
    except Exception as e:
        logger.error(f"Error getting MIDI messages: {str(e)}")
        return f"Error getting MIDI messages: {str(e)}"


@mcp.tool()
@get_validated_tool
def set_track_name(ctx: Context, track_index: int, name: str) -> str:
    """
    Set the name of a track.

    Parameters:
    - track_index: The index of the track to rename
    - name: The new name for the track
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_track_name", {"track_index": track_index, "name": name})
        return f"Renamed track to: {result.get('name', name)}"
    except Exception as e:
        logger.error(f"Error setting track name: {str(e)}")
        return f"Error setting track name: {str(e)}"

@mcp.tool()
@get_validated_tool
def create_clip(ctx: Context, track_index: int, clip_index: int, length: float = 4.0) -> str:
    """
    Create a new MIDI clip in the specified track and clip slot.

    Parameters:
    - track_index: The index of the track to create the clip in
    - clip_index: The index of the clip slot to create the clip in
    - length: The length of the clip in beats (default: 4.0)
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("create_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "length": length
        })
        return f"Created new clip at track {track_index}, slot {clip_index} with length {length} beats"
    except Exception as e:
        logger.error(f"Error creating clip: {str(e)}")
        return f"Error creating clip: {str(e)}"

@mcp.tool()
@get_validated_tool
def add_notes_to_clip(
    ctx: Context,
    track_index: int,
    clip_index: int,
    notes: List[Dict[str, Union[int, float, bool]]]
) -> str:
    """
    Add MIDI notes to a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - notes: List of note dictionaries, each with pitch, start_time, duration, velocity, and mute
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })
        return f"Added {len(notes)} notes to clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error adding notes to clip: {str(e)}")
        return f"Error adding notes to clip: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_clip_name(ctx: Context, track_index: int, clip_index: int, name: str) -> str:
    """
    Set the name of a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - name: The new name for the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_name", {
            "track_index": track_index,
            "clip_index": clip_index,
            "name": name
        })
        return f"Renamed clip at track {track_index}, slot {clip_index} to '{name}'"
    except Exception as e:
        logger.error(f"Error setting clip name: {str(e)}")
        return f"Error setting clip name: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_tempo(ctx: Context, tempo: float) -> str:
    """
    Set the tempo of the Ableton session.

    Parameters:
    - tempo: The new tempo in BPM
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_tempo", {"tempo": tempo})
        return f"Set tempo to {tempo} BPM"
    except Exception as e:
        logger.error(f"Error setting tempo: {str(e)}")
        return f"Error setting tempo: {str(e)}"


@mcp.tool()
@get_validated_tool
def load_instrument_or_effect(ctx: Context, track_index: int, uri: str) -> str:
    """
    Load an instrument or effect onto a track using its URI.

    Parameters:
    - track_index: The index of the track to load the instrument on
    - uri: The URI of the instrument or effect to load (e.g., 'query:Synths#Instrument%20Rack:Bass:FileId_5116')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": uri
        })

        # Check if the instrument was loaded successfully
        if result.get("loaded", False):
            new_devices = result.get("new_devices", [])
            if new_devices:
                return f"Loaded instrument with URI '{uri}' on track {track_index}. New devices: {', '.join(new_devices)}"
            else:
                devices = result.get("devices_after", [])
                return f"Loaded instrument with URI '{uri}' on track {track_index}. Devices on track: {', '.join(devices)}"
        else:
            return f"Failed to load instrument with URI '{uri}'"
    except Exception as e:
        logger.error(f"Error loading instrument by URI: {str(e)}")
        return f"Error loading instrument by URI: {str(e)}"

@mcp.tool()
@get_validated_tool
def fire_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Start playing a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("fire_clip", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return f"Started playing clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error firing clip: {str(e)}")
        return f"Error firing clip: {str(e)}"

@mcp.tool()
@get_validated_tool
def stop_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Stop playing a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_clip", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return f"Stopped clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error stopping clip: {str(e)}")
        return f"Error stopping clip: {str(e)}"

@mcp.tool()
@get_validated_tool
def start_playback(ctx: Context) -> str:
    """Start playing the Ableton session."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("start_playback")
        return "Started playback"
    except Exception as e:
        logger.error(f"Error starting playback: {str(e)}")
        return f"Error starting playback: {str(e)}"

@mcp.tool()
@get_validated_tool
def stop_playback(ctx: Context) -> str:
    """Stop playing the Ableton session."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("stop_playback")
        return "Stopped playback"
    except Exception as e:
        logger.error(f"Error stopping playback: {str(e)}")
        return f"Error stopping playback: {str(e)}"

@mcp.tool()
@get_validated_tool
def undo(ctx: Context) -> str:
    """Undo the last action."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("undo")
        if result.get("undone"):
            return "Undone last action."
        else:
            return f"Could not undo: {result.get('message', 'Unknown reason')}"
    except Exception as e:
        logger.error(f"Error undoing: {str(e)}")
        return f"Error undoing: {str(e)}"

@mcp.tool()
@get_validated_tool
def redo(ctx: Context) -> str:
    """Redo the last undone action."""
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("redo")
        if result.get("redone"):
            return "Redone last action."
        else:
            return f"Could not redo: {result.get('message', 'Unknown reason')}"
    except Exception as e:
        logger.error(f"Error redoing: {str(e)}")
        return f"Error redoing: {str(e)}"

@mcp.tool()
@get_validated_tool
def randomize_device_parameters(ctx: Context, track_index: int, device_index: int) -> str:
    """
    Randomize the parameters of a device.

    Parameters:
    - track_index: The index of the track where the device is located
    - device_index: The index of the device on the track
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("randomize_device_parameters", {
            "track_index": track_index,
            "device_index": device_index
        })
        return f"Randomized parameters for device {device_index} on track {track_index}"
    except Exception as e:
        logger.error(f"Error randomizing parameters: {str(e)}")
        return f"Error randomizing parameters: {str(e)}"

@mcp.tool()
@get_validated_tool
def save_device_parameters_to_json(ctx: Context, track_index: int, device_index: int, filepath: str) -> str:
    """
    Saves the parameters of a device to a JSON file.

    Parameters:
    - track_index: The index of the track where the device is located
    - device_index: The index of the device on the track
    - filepath: The path to the JSON file to save the parameters to
    """
    try:
        ableton = get_ableton_connection()
        device_details = ableton.send_command("get_device_details", {
            "track_index": track_index,
            "device_index": device_index
        })

        parameters = device_details.get("parameters", [])

        with open(filepath, "w") as f:
            json.dump(parameters, f, indent=2)

        return f"Saved {len(parameters)} parameters to {filepath}"
    except Exception as e:
        logger.error(f"Error saving device parameters: {str(e)}")
        return f"Error saving device parameters: {str(e)}"

@mcp.tool()
@get_validated_tool
def load_device_parameters_from_json(ctx: Context, track_index: int, device_index: int, filepath: str) -> str:
    """
    Loads the. parameters of a device from a JSON file.

    Parameters:
    - track_index: The index of the track where the device is located
    - device_index: The index of the device on the track
    - filepath: The path to the JSON file to load the parameters from
    """
    try:
        with open(filepath, "r") as f:
            parameters = json.load(f)

        ableton = get_ableton_connection()
        result = ableton.send_command("set_device_parameters", {
            "track_index": track_index,
            "device_index": device_index,
            "parameters": parameters
        })

        return f"Loaded {len(parameters)} parameters from {filepath}"
    except Exception as e:
        logger.error(f"Error loading device parameters: {str(e)}")
        return f"Error loading device parameters: {str(e)}"

@mcp.tool()
@get_validated_tool
def setup_sidechain(ctx: Context, source_track_index: int, target_track_index: int) -> str:
    """
    Setup sidechain compression from a source track to a target track.

    Parameters:
    - source_track_index: The index of the track to use as the sidechain source
    - target_track_index: The index of the track to apply the compressor to
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("setup_sidechain", {
            "source_track_index": source_track_index,
            "target_track_index": target_track_index
        })
        return f"Setup sidechain from track {result.get('source_track')} to track {result.get('target_track')}"
    except Exception as e:
        logger.error(f"Error setting up sidechain: {str(e)}")
        return f"Error setting up sidechain: {str(e)}"

@mcp.tool()
@get_validated_tool
def humanize_clip(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Add random variations to the timing and velocity of notes in a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("humanize_clip", {
            "track_index": track_index,
            "clip_index": clip_index
        })
        return f"Humanized clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error humanizing clip: {str(e)}")
        return f"Error humanizing clip: {str(e)}"

@mcp.tool()
@get_validated_tool
def build_a_drum_beat(ctx: Context, genre: str) -> str:
    """
    Build a drum beat for a specific genre.

    Parameters:
    - genre: The genre of the drum beat to build (e.g., "house", "trap")
    """
    try:
        ableton = get_ableton_connection()

        # 1. Create a new MIDI track
        new_track_info = ableton.send_command("create_midi_track", {"index": -1})
        track_index = new_track_info.get("index")

        # 2. Search for a drum rack
        query = ""
        if genre.lower() == "house":
            query = "909 Core Kit"
        elif genre.lower() == "trap":
            query = "808 Core Kit"
        else:
            return f"I don't know how to build a {genre} drum beat yet."

        search_results = ableton.send_command("search_browser", {"query": query})
        if not search_results:
            return f"Could not find a drum rack for {genre}."

        drum_rack_uri = search_results[0].get("uri")

        # 3. Load the drum rack
        ableton.send_command("load_browser_item", {"track_index": track_index, "item_uri": drum_rack_uri})

        # 4. Generate a MIDI clip
        notes = []
        if genre.lower() == "house":
            # Four-on-the-floor kick drum
            notes = [
                {"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 127, "mute": False},
                {"pitch": 36, "start_time": 1.0, "duration": 0.5, "velocity": 127, "mute": False},
                {"pitch": 36, "start_time": 2.0, "duration": 0.5, "velocity": 127, "mute": False},
                {"pitch": 36, "start_time": 3.0, "duration": 0.5, "velocity": 127, "mute": False},
                # Clap on 2 and 4
                {"pitch": 39, "start_time": 1.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 39, "start_time": 3.0, "duration": 0.5, "velocity": 100, "mute": False},
            ]
        elif genre.lower() == "trap":
            # Trap beat
            notes = [
                {"pitch": 36, "start_time": 0.0, "duration": 0.5, "velocity": 127, "mute": False},
                {"pitch": 36, "start_time": 1.5, "duration": 0.5, "velocity": 127, "mute": False},
                {"pitch": 39, "start_time": 1.0, "duration": 0.5, "velocity": 100, "mute": False},
                {"pitch": 39, "start_time": 3.0, "duration": 0.5, "velocity": 100, "mute": False},
            ]

        ableton.send_command("create_clip", {"track_index": track_index, "clip_index": 0, "length": 4.0})
        ableton.send_command("add_notes_to_clip", {"track_index": track_index, "clip_index": 0, "notes": notes})

        return f"Built a {genre} drum beat on track {track_index}"
    except Exception as e:
        logger.error(f"Error building drum beat: {str(e)}")
        return f"Error building drum beat: {str(e)}"

@mcp.tool()
@get_validated_tool
def harmonize_melody(ctx: Context, track_index: int, clip_index: int) -> str:
    """
    Harmonize a melody with a simple chord progression.

    Parameters:
    - track_index: The index of the track containing the melody
    - clip_index: The index of the clip slot containing the melody
    """
    try:
        ableton = get_ableton_connection()

        # 1. Get the melody notes (we don't use them for now, but we would in a real implementation)
        # notes = ableton.send_command("get_notes", {"track_index": track_index, "clip_index": clip_index})

        # 2. Create a new MIDI track for the chords
        new_track_info = ableton.send_command("create_midi_track", {"index": -1})
        chord_track_index = new_track_info.get("index")

        # 3. Load a piano instrument
        # This is a guess, and might need to be adjusted
        piano_uri = "query:Sounds#Piano & Keys"
        search_results = ableton.send_command("search_browser", {"query": "Grand Piano"})
        if not search_results:
            return "Could not find a Grand Piano instrument."
        piano_uri = search_results[0].get("uri")
        ableton.send_command("load_browser_item", {"track_index": chord_track_index, "item_uri": piano_uri})

        # 4. Generate a I-IV-V-I chord progression in C major
        chords = [
            # C major (I)
            [{"pitch": 60, "start_time": 0.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 64, "start_time": 0.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 67, "start_time": 0.0, "duration": 1.0, "velocity": 100, "mute": False}],
            # F major (IV)
            [{"pitch": 65, "start_time": 1.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 69, "start_time": 1.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 72, "start_time": 1.0, "duration": 1.0, "velocity": 100, "mute": False}],
            # G major (V)
            [{"pitch": 67, "start_time": 2.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 71, "start_time": 2.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 74, "start_time": 2.0, "duration": 1.0, "velocity": 100, "mute": False}],
            # C major (I)
            [{"pitch": 60, "start_time": 3.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 64, "start_time": 3.0, "duration": 1.0, "velocity": 100, "mute": False},
             {"pitch": 67, "start_time": 3.0, "duration": 1.0, "velocity": 100, "mute": False}],
        ]

        notes = [note for chord in chords for note in chord]

        ableton.send_command("create_clip", {"track_index": chord_track_index, "clip_index": 0, "length": 4.0})
        ableton.send_command("add_notes_to_clip", {"track_index": chord_track_index, "clip_index": 0, "notes": notes})

        return f"Harmonized melody on track {chord_track_index}"
    except Exception as e:
        logger.error(f"Error harmonizing melody: {str(e)}")
        return f"Error harmonizing melody: {str(e)}"

@mcp.tool()
@get_validated_tool
def get_browser_tree(ctx: Context, category_type: str = "all") -> str:
    """
    Get a hierarchical tree of browser categories from Ableton.

    Parameters:
    - category_type: Type of categories to get ('all', 'instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects')
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_tree", {
            "category_type": category_type
        })

        # Check if we got any categories
        if "available_categories" in result and len(result.get("categories", [])) == 0:
            available_cats = result.get("available_categories", [])
            return (f"No categories found for '{category_type}'. "
                   f"Available browser categories: {', '.join(available_cats)}")

        # Format the tree in a more readable way
        total_folders = result.get("total_folders", 0)
        formatted_output = f"Browser tree for '{category_type}' (showing {total_folders} folders):\n\n"

        def format_tree(item, indent=0):
            output = ""
            if item:
                prefix = "  " * indent
                name = item.get("name", "Unknown")
                path = item.get("path", "")
                has_more = item.get("has_more", False)

                # Add this item
                output += f"{prefix}• {name}"
                if path:
                    output += f" (path: {path})"
                if has_more:
                    output += " [...]"
                output += "\n"

                # Add children
                for child in item.get("children", []):
                    output += format_tree(child, indent + 1)
            return output

        # Format each category
        for category in result.get("categories", []):
            formatted_output += format_tree(category)
            formatted_output += "\n"

        return formatted_output
    except Exception as e:
        error_msg = str(e)
        if "Browser is not available" in error_msg:
            logger.error(f"Browser is not available in Ableton: {error_msg}")
            return f"Error: The Ableton browser is not available. Make sure Ableton Live is fully loaded and try again."
        elif "Could not access Live application" in error_msg:
            logger.error(f"Could not access Live application: {error_msg}")
            return f"Error: Could not access the Ableton Live application. Make sure Ableton Live is running and the Remote Script is loaded."
        else:
            logger.error(f"Error getting browser tree: {error_msg}")
            return f"Error getting browser tree: {error_msg}"

@mcp.tool()
@get_validated_tool
def get_browser_items_at_path(ctx: Context, path: str) -> str:
    """
    Get browser items at a specific path in Ableton's browser.

    Parameters:
    - path: Path in the format "category/folder/subfolder"
            where category is one of the available browser categories in Ableton
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("get_browser_items_at_path", {
            "path": path
        })

        # Check if there was an error with available categories
        if "error" in result and "available_categories" in result:
            error = result.get("error", "")
            available_cats = result.get("available_categories", [])
            return (f"Error: {error}\n"
                   f"Available browser categories: {', '.join(available_cats)}")

        return json.dumps(result, indent=2)
    except Exception as e:
        error_msg = str(e)
        if "Browser is not available" in error_msg:
            logger.error(f"Browser is not available in Ableton: {error_msg}")
            return f"Error: The Ableton browser is not available. Make sure Ableton Live is fully loaded and try again."
        elif "Could not access Live application" in error_msg:
            logger.error(f"Could not access Live application: {error_msg}")
            return f"Error: Could not access the Ableton Live application. Make sure Ableton Live is running and the Remote Script is loaded."
        elif "Unknown or unavailable category" in error_msg:
            logger.error(f"Invalid browser category: {error_msg}")
            return f"Error: {error_msg}. Please check the available categories using get_browser_tree."
        elif "Path part" in error_msg and "not found" in error_msg:
            logger.error(f"Path not found: {error_msg}")
            return f"Error: {error_msg}. Please check the path and try again."
        else:
            logger.error(f"Error getting browser items at path: {error_msg}")
            return f"Error getting browser items at path: {error_msg}"

@mcp.tool()
@get_validated_tool
def load_drum_kit(ctx: Context, track_index: int, rack_uri: str, kit_path: str) -> str:
    """
    Load a drum rack and then load a specific drum kit into it.

    Parameters:
    - track_index: The index of the track to load on
    - rack_uri: The URI of the drum rack to load (e.g., 'Drums/Drum Rack')
    - kit_path: Path to the drum kit inside the browser (e.g., 'drums/acoustic/kit1')
    """
    try:
        ableton = get_ableton_connection()

        # Step 1: Load the drum rack
        result = ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": rack_uri
        })

        if not result.get("loaded", False):
            return f"Failed to load drum rack with URI '{rack_uri}'"

        # Step 2: Get the drum kit items at the specified path
        kit_result = ableton.send_command("get_browser_items_at_path", {
            "path": kit_path
        })

        if "error" in kit_result:
            return f"Loaded drum rack but failed to find drum kit: {kit_result.get('error')}"

        # Step 3: Find a loadable drum kit
        kit_items = kit_result.get("items", [])
        loadable_kits = [item for item in kit_items if item.get("is_loadable", False)]

        if not loadable_kits:
            return f"Loaded drum rack but no loadable drum kits found at '{kit_path}'"

        # Step 4: Load the first loadable kit
        kit_uri = loadable_kits[0].get("uri")
        load_result = ableton.send_command("load_browser_item", {
            "track_index": track_index,
            "item_uri": kit_uri
        })

        return f"Loaded drum rack and kit '{loadable_kits[0].get('name')}' on track {track_index}"
    except Exception as e:
        logger.error(f"Error loading drum kit: {str(e)}")
        return f"Error loading drum kit: {str(e)}"

# Main execution
def main():
    """Run the MCP server"""
    mcp.run(transport="sse", port=8000)

@mcp.tool()
@get_validated_tool
def loop_clip(ctx: Context, track_index: int, clip_index: int, is_looping: bool) -> str:
    """
    Set whether a clip should loop or not.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - is_looping: Whether the clip should be set to loop or not
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("loop_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "is_looping": is_looping
        })

        loop_status = "enabled" if is_looping else "disabled"
        return f"Looping {loop_status} for clip at track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error setting clip looping: {str(e)}")
        return f"Error setting clip looping: {str(e)}"

@mcp.tool()
@get_validated_tool
def set_clip_length(ctx: Context, track_index: int, clip_index: int, length: float) -> str:
    """
    Set the length of a clip.

    Parameters:
    - track_index: The index of the track containing the clip
    - clip_index: The index of the clip slot containing the clip
    - length: The new length of the clip in beats
    """
    try:
        ableton = get_ableton_connection()
        result = ableton.send_command("set_clip_length", {
            "track_index": track_index,
            "clip_index": clip_index,
            "length": length
        })
        return f"Set length of clip at track {track_index}, slot {clip_index} to {length} beats"
    except Exception as e:
        logger.error(f"Error setting clip length: {str(e)}")
        return f"Error setting clip length: {str(e)}"

@mcp.tool()
@get_validated_tool
def generate_intelligent_midi(ctx: Context, track_index: int, clip_index: int, description: str) -> str:
    """
    Generates a MIDI clip based on a detailed description.

    Parameters:
    - track_index: The index of the track to create the clip on
    - clip_index: The index of the clip slot to create the clip in
    - description: A detailed description of the MIDI to generate
                   (e.g., "a 4-bar funky bassline in C minor with a syncopated rhythm")
    """
    try:
        # In a real implementation, this would call an LLM to generate the notes.
        # For now, we'll use a simple parser.
        notes = []
        if "bassline" in description.lower():
            # Generate a simple bassline
            for i in range(16):
                if i % 4 != 3: # Add some syncopation
                    notes.append({"pitch": 36, "start_time": i * 0.25, "duration": 0.2, "velocity": 100, "mute": False})
        elif "chords" in description.lower():
            # Generate a simple chord progression
            chords = [[60, 64, 67], [65, 69, 72], [67, 71, 76], [60, 64, 67]]
            for i, chord in enumerate(chords):
                for note in chord:
                    notes.append({"pitch": note, "start_time": i, "duration": 0.9, "velocity": 90, "mute": False})
        else:
            return "I'm sorry, I can only generate simple basslines and chords right now."

        ableton = get_ableton_connection()

        # Create a new clip
        ableton.send_command("create_clip", {"track_index": track_index, "clip_index": clip_index, "length": 4.0})

        # Add the notes to the clip
        result = ableton.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })

        return f"Generated intelligent MIDI clip with {len(notes)} notes on track {track_index}, slot {clip_index}"
    except Exception as e:
        logger.error(f"Error generating intelligent MIDI: {str(e)}")
        return f"Error generating intelligent MIDI: {str(e)}"

@mcp.tool()
@get_validated_tool
def generate_chord_progression(ctx: Context, track_index: int, clip_index: int, progression: str, beats_per_chord: float = 4.0, octave: int = 4) -> str:
    """
    Generates a MIDI clip with a specified chord progression.

    Parameters:
    - track_index: The index of the track to create the clip on.
    - clip_index: The index of the clip slot to create the clip in.
    - progression: A comma-separated string of chord names (e.g., "Cmaj7, G7, Am, F").
    - beats_per_chord: The duration of each chord in beats.
    - octave: The MIDI octave for the root note of the chords.
    """
    try:
        chord_names = [name.strip() for name in progression.split(',')]
        notes = []
        current_time = 0.0

        for chord_name in chord_names:
            try:
                midi_notes = chord_to_midi(chord_name, octave)
                for pitch in midi_notes:
                    notes.append({
                        "pitch": pitch,
                        "start_time": current_time,
                        "duration": beats_per_chord * 0.9,  # Leave a small gap
                        "velocity": 90,
                        "mute": False
                    })
                current_time += beats_per_chord
            except ValueError as e:
                return f"Error parsing chord '{chord_name}': {e}"

        if not notes:
            return "No valid chords were found in the progression."

        clip_length = len(chord_names) * beats_per_chord

        ableton = get_ableton_connection()

        # Create a new clip
        ableton.send_command("create_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "length": clip_length
        })

        # Add the notes to the clip
        result = ableton.send_command("add_notes_to_clip", {
            "track_index": track_index,
            "clip_index": clip_index,
            "notes": notes
        })

        return f"Generated chord progression '{progression}' with {len(notes)} notes on track {track_index}, slot {clip_index}."

    except Exception as e:
        logger.error(f"Error generating chord progression: {str(e)}")
        return f"Error generating chord progression: {str(e)}"

@mcp.tool()
@get_validated_tool
def generate_progression_with_bassline(
    ctx: Context,
    progression: str,
    beats_per_chord: float = 4.0,
    chord_octave: int = 4,
    bass_octave: int = 2,
    bass_pattern: str = "root_on_beat"
) -> str:
    """
    Generates a MIDI clip with a chord progression and a corresponding bassline on two new tracks.

    Parameters:
    - progression: A comma-separated string of chord names (e.g., "Cmaj7, G7, Am, F").
    - beats_per_chord: The duration of each chord in beats.
    - chord_octave: The MIDI octave for the chords.
    - bass_octave: The MIDI octave for the bassline.
    - bass_pattern: The rhythmic pattern for the bassline ('root_on_beat', 'quarter_notes', 'eighth_notes').
    """
    try:
        ableton = get_ableton_connection()

        # 1. Create tracks
        chord_track_info = ableton.send_command("create_midi_track", {"name": "Chords"})
        bass_track_info = ableton.send_command("create_midi_track", {"name": "Bassline"})
        chord_track_index = chord_track_info.get("index")
        bass_track_index = bass_track_info.get("index")

        if chord_track_index is None or bass_track_index is None:
            return "Error: Could not create new tracks for the progression."

        # 2. Generate notes
        chord_names = [name.strip() for name in progression.split(',')]
        chord_notes = []
        bass_notes = []
        current_time = 0.0

        for chord_name in chord_names:
            try:
                # Generate chord notes
                midi_chord = chord_to_midi(chord_name, chord_octave)
                for pitch in midi_chord:
                    chord_notes.append({"pitch": pitch, "start_time": current_time, "duration": beats_per_chord * 0.9, "velocity": 90})

                # Generate bass notes
                root_note_name, _ = parse_chord_name(chord_name)
                root_midi = NOTES[root_note_name] + (bass_octave * 12)

                if bass_pattern == "root_on_beat":
                    bass_notes.append({"pitch": root_midi, "start_time": current_time, "duration": beats_per_chord * 0.9, "velocity": 100})
                elif bass_pattern == "quarter_notes":
                    for i in range(int(beats_per_chord)):
                        bass_notes.append({"pitch": root_midi, "start_time": current_time + i, "duration": 0.9, "velocity": 100})
                elif bass_pattern == "eighth_notes":
                    for i in range(int(beats_per_chord * 2)):
                        bass_notes.append({"pitch": root_midi, "start_time": current_time + i * 0.5, "duration": 0.4, "velocity": 100})

                current_time += beats_per_chord

            except (ValueError, KeyError) as e:
                return f"Error parsing chord '{chord_name}': {e}"

        clip_length = len(chord_names) * beats_per_chord

        # 3. Create clips and add notes
        ableton.send_command("create_clip", {"track_index": chord_track_index, "clip_index": 0, "length": clip_length})
        ableton.send_command("add_notes_to_clip", {"track_index": chord_track_index, "clip_index": 0, "notes": chord_notes})

        ableton.send_command("create_clip", {"track_index": bass_track_index, "clip_index": 0, "length": clip_length})
        ableton.send_command("add_notes_to_clip", {"track_index": bass_track_index, "clip_index": 0, "notes": bass_notes})

        return f"Generated chord progression on track {chord_track_index} and bassline on track {bass_track_index}."

    except Exception as e:
        logger.error(f"Error generating progression with bassline: {str(e)}")
        return f"Error generating progression with bassline: {str(e)}"


@mcp.tool()
@get_validated_tool
def intelligent_randomize(ctx: Context, track_index: int, device_index: int, style: str = "subtle") -> str:
    """
    Intelligently randomizes the parameters of a device based on a specified style.

    Parameters:
    - track_index: The index of the track where the device is located.
    - device_index: The index of the device on the track.
    - style: The randomization style ('subtle', 'rhythmic', 'chaotic').
    """
    try:
        import random

        ableton = get_ableton_connection()

        # 1. Get device parameters
        device_details_str = get_device_details(ctx, track_index, device_index)
        device_details = json.loads(device_details_str)
        parameters = device_details.get("parameters", [])

        if not parameters:
            return f"Device at track {track_index}, device {device_index} has no parameters to randomize."

        changed_params = []

        # 2. Apply randomization based on style
        for param in parameters:
            # Skip read-only or un-automatable parameters
            if param.get("is_automatable") is False:
                continue

            param_name = param["name"]
            min_val, max_val = param["min"], param["max"]

            should_randomize = False
            new_value = param["value"]

            if style == "subtle":
                # Randomize a small subset of parameters by a small amount
                if random.random() < 0.2:
                    should_randomize = True
                    change_range = (max_val - min_val) * 0.1
                    new_value = param["value"] + random.uniform(-change_range, change_range)

            elif style == "rhythmic":
                # Focus on rhythmic parameters
                if any(k in param_name.lower() for k in ["rate", "sync", "lfo", "env", "attack", "decay", "release"]):
                    if random.random() < 0.7:
                        should_randomize = True
                        new_value = random.uniform(min_val, max_val)

            elif style == "chaotic":
                # Randomize most parameters
                if random.random() < 0.8:
                    should_randomize = True
                    new_value = random.uniform(min_val, max_val)

            if should_randomize:
                # Clamp the new value to be within the min/max range
                new_value = max(min_val, min(max_val, new_value))

                # Set the parameter
                set_device_parameter(ctx, track_index, device_index, param_name, new_value)
                changed_params.append(param_name)

        if not changed_params:
            return f"No parameters were randomized for device on track {track_index} with style '{style}'."

        return f"Intelligently randomized {len(changed_params)} parameters on device {device_index} of track {track_index} with style '{style}'."

    except Exception as e:
        logger.error(f"Error during intelligent randomization: {str(e)}")
        return f"Error during intelligent randomization: {str(e)}"

def _get_genre_recipe(genre, key):
    """A helper function to store and retrieve recipes for different genres."""
    # Note: Key parsing is basic for this example. A more robust implementation
    # would use the music_theory module to transpose progressions.
    root_note = key.split(' ')[0]

    recipes = {
        "lo-fi hip hop": {
            "tempo": 85,
            "drum_rack_query": "Kit-Core 909",
            "drum_pattern": [
                # Kick
                {"pitch": 36, "start_time": 0.0, "duration": 0.1, "velocity": 110},
                {"pitch": 36, "start_time": 1.0, "duration": 0.1, "velocity": 80},
                {"pitch": 36, "start_time": 2.5, "duration": 0.1, "velocity": 100},
                # Snare
                {"pitch": 38, "start_time": 1.0, "duration": 0.1, "velocity": 120},
                {"pitch": 38, "start_time": 3.0, "duration": 0.1, "velocity": 110},
                # Hi-hat
                {"pitch": 42, "start_time": 0.0, "duration": 0.1, "velocity": 90},
                {"pitch": 42, "start_time": 0.5, "duration": 0.1, "velocity": 70},
                {"pitch": 42, "start_time": 1.0, "duration": 0.1, "velocity": 90},
                {"pitch": 42, "start_time": 1.5, "duration": 0.1, "velocity": 70},
                {"pitch": 42, "start_time": 2.0, "duration": 0.1, "velocity": 90},
                {"pitch": 42, "start_time": 2.5, "duration": 0.1, "velocity": 70},
                {"pitch": 42, "start_time": 3.0, "duration": 0.1, "velocity": 90},
                {"pitch": 42, "start_time": 3.5, "duration": 0.1, "velocity": 70},
            ],
            "chord_instrument_query": "Electric Piano",
            "bass_instrument_query": "Bass Guitar",
            "progression": f"{root_note}maj7, G#dim7, {root_note}min7, D#7" # Example progression
        },
        "house": {
            "tempo": 125,
            "drum_rack_query": "Kit-Core 808",
            "drum_pattern": [
                # Four-on-the-floor Kick
                {"pitch": 36, "start_time": 0.0, "duration": 0.1, "velocity": 127},
                {"pitch": 36, "start_time": 1.0, "duration": 0.1, "velocity": 127},
                {"pitch": 36, "start_time": 2.0, "duration": 0.1, "velocity": 127},
                {"pitch": 36, "start_time": 3.0, "duration": 0.1, "velocity": 127},
                # Off-beat hi-hat
                {"pitch": 42, "start_time": 0.5, "duration": 0.1, "velocity": 100},
                {"pitch": 42, "start_time": 1.5, "duration": 0.1, "velocity": 100},
                {"pitch": 42, "start_time": 2.5, "duration": 0.1, "velocity": 100},
                {"pitch": 42, "start_time": 3.5, "duration": 0.1, "velocity": 100},
                # Clap on 2 and 4
                {"pitch": 39, "start_time": 1.0, "duration": 0.1, "velocity": 110},
                {"pitch": 39, "start_time": 3.0, "duration": 0.1, "velocity": 110},
            ],
            "chord_instrument_query": "Piano",
            "bass_instrument_query": "Synth Bass",
            "progression": f"{root_note}min7, Fmaj7, {root_note}min7, G7" # Example progression
        }
    }
    return recipes.get(genre.lower())

@mcp.tool()
@get_validated_tool
def create_song_starter(ctx: Context, genre: str, key: str) -> str:
    """
    Creates a full song starter with drums, bass, and chords based on a genre and key.

    Parameters:
    - genre: The genre of the song starter (e.g., "lo-fi hip hop", "house").
    - key: The musical key of the song (e.g., "C major", "A minor").
    """
    try:
        recipe = _get_genre_recipe(genre, key)
        if not recipe:
            return f"I don't have a recipe for the genre '{genre}'. Available genres: lo-fi hip hop, house."

        ableton = get_ableton_connection()

        # 1. Set tempo
        set_tempo(ctx, recipe["tempo"])

        # 2. Create Drums
        drum_track_info = ableton.send_command("create_midi_track", {"name": "Drums"})
        drum_track_index = drum_track_info.get("index")
        if drum_track_index is not None:
            search_results = ableton.send_command("search_browser", {"query": recipe["drum_rack_query"]})
            if search_results:
                drum_rack_uri = search_results[0].get("uri")
                ableton.send_command("load_browser_item", {"track_index": drum_track_index, "item_uri": drum_rack_uri})
                ableton.send_command("create_clip", {"track_index": drum_track_index, "clip_index": 0, "length": 4.0})
                ableton.send_command("add_notes_to_clip", {"track_index": drum_track_index, "clip_index": 0, "notes": recipe["drum_pattern"]})

        # 3. Create Chords and Bass
        progression_result = generate_progression_with_bassline(
            ctx,
            progression=recipe["progression"],
            beats_per_chord=4.0,
            chord_octave=4,
            bass_octave=2,
            bass_pattern="quarter_notes"
        )

        # 4. Load instruments for Chords and Bass (we need to get their track indices)
        # This part is tricky as generate_progression_with_bassline doesn't return the indices.
        # We'll assume they are the last two created tracks.
        session_info = json.loads(get_session_info(ctx))
        tracks = session_info.get("tracks", [])
        chord_track = next((t for t in reversed(tracks) if t["name"] == "Chords"), None)
        bass_track = next((t for t in reversed(tracks) if t["name"] == "Bassline"), None)

        if chord_track:
            search_results = ableton.send_command("search_browser", {"query": recipe["chord_instrument_query"]})
            if search_results:
                instrument_uri = search_results[0].get("uri")
                ableton.send_command("load_browser_item", {"track_index": chord_track["index"], "item_uri": instrument_uri})

        if bass_track:
            search_results = ableton.send_command("search_browser", {"query": recipe["bass_instrument_query"]})
            if search_results:
                instrument_uri = search_results[0].get("uri")
                ableton.send_command("load_browser_item", {"track_index": bass_track["index"], "item_uri": instrument_uri})

        return f"Successfully created a '{genre}' song starter in the key of {key}."

    except Exception as e:
        logger.error(f"Error creating song starter: {str(e)}")
        return f"Error creating song starter: {str(e)}"

@mcp.tool()
@get_validated_tool
def analyze_mix(ctx: Context) -> str:
    """
    Analyzes the current mix and provides suggestions for improvement.
    """
    try:
        suggestions = []
        ableton = get_ableton_connection()
        session_info = json.loads(get_session_info(ctx))
        tracks = session_info.get("tracks", [])

        # --- Analyze Master Track ---
        master_track = session_info.get("master_track", {})
        if master_track.get("volume", 0.0) > 0.85: # Corresponds to 0 dB in Ableton
            suggestions.append("Master track volume is high. Consider lowering it to create more headroom.")

        # --- Analyze Individual Tracks ---
        pan_left_count = 0
        pan_right_count = 0

        for track_info in tracks:
            track_index = track_info["index"]
            track_details_str = get_track_info(ctx, track_index)
            track_details = json.loads(track_details_str)

            # Analyze volume
            if track_details.get("volume", 0.0) >= 0.85:
                suggestions.append(f"Track '{track_details['name']}' is very loud. Consider lowering its volume.")

            # Analyze panning
            panning = track_details.get("panning", 0.0)
            if panning < -0.1:
                pan_left_count += 1
            elif panning > 0.1:
                pan_right_count += 1

            # Analyze devices
            for device in track_details.get("devices", []):
                if "eq" in device["name"].lower():
                    suggestions.append(f"On track '{track_details['name']}', consider using a high-pass filter on the EQ to remove unnecessary low-end rumble.")
                if "compressor" in device["name"].lower():
                    suggestions.append(f"On track '{track_details['name']}', a good starting point for the compressor is a 4:1 ratio with a medium attack and fast release.")

        if abs(pan_left_count - pan_right_count) > len(tracks) / 3:
            suggestions.append("The stereo image seems unbalanced. Check the panning of your tracks.")

        if not suggestions:
            return "The mix looks balanced. Good job!"

        return "Here are some suggestions for your mix:\n- " + "\n- ".join(suggestions)

    except Exception as e:
        logger.error(f"Error analyzing mix: {str(e)}")
        return f"Error analyzing mix: {str(e)}"

@mcp.tool()
@get_validated_tool
def auto_mix_tracks(ctx: Context) -> str:
    """
    Automatically applies some basic mixing decisions to the tracks in the session.
    """
    try:
        actions_taken = []
        ableton = get_ableton_connection()
        session_info = json.loads(get_session_info(ctx))
        tracks = session_info.get("tracks", [])

        # Simple auto-panning logic
        pan_amount = 0.2
        pan_direction = 1  # 1 for right, -1 for left

        for track_info in tracks:
            track_index = track_info["index"]
            track_details_str = get_track_info(ctx, track_index)
            track_details = json.loads(track_details_str)
            track_name = track_details.get("name", "").lower()

            # Auto-leveling
            if track_details.get("volume", 0.0) > 0.85:
                set_volume(ctx, track_index, 0.8)
                actions_taken.append(f"Lowered volume on track '{track_name}'.")

            # Auto-panning
            if any(k in track_name for k in ["kick", "snare", "bass", "vocal"]):
                # Keep key elements centered
                set_panning(ctx, track_index, 0.0)
                actions_taken.append(f"Centered track '{track_name}'.")
            else:
                set_panning(ctx, track_index, pan_amount * pan_direction)
                actions_taken.append(f"Panned track '{track_name}' {'right' if pan_direction == 1 else 'left'}.")
                pan_direction *= -1 # Alternate sides

        if not actions_taken:
            return "No mixing actions were taken. The mix seems to have a good starting balance."

        return "Auto-mix applied:\n- " + "\n- ".join(actions_taken)

    except Exception as e:
        logger.error(f"Error during auto-mixing: {str(e)}")
        return f"Error during auto-mixing: {str(e)}"

if __name__ == "__main__":
    main()