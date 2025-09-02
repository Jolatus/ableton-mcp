# AbletonMCP - Ableton Live Model Context Protocol Integration
[![smithery badge](https://smithery.ai/badge/@ahujasid/ableton-mcp)](https://smithery.ai/server/@ahujasid/ableton-mcp)

AbletonMCP connects Ableton Live to Claude AI through the Model Context Protocol (MCP), allowing Claude to directly interact with and control Ableton Live. This integration enables prompt-assisted music production, track creation, and Live session manipulation.

### Join the Community

Give feedback, get inspired, and build on top of the MCP: [Discord](https://discord.gg/3ZrMyGKnaU). Made by [Siddharth](https://x.com/sidahuj)

## Features

- **Two-way communication**: Connect Claude AI to Ableton Live through a socket-based server
- **Track manipulation**: Create, modify, and manipulate MIDI and audio tracks
- **Instrument and effect selection**: Claude can access and load the right instruments, effects and sounds from Ableton's library
- **Clip creation**: Create and edit MIDI clips with notes
- **Session control**: Start and stop playback, fire clips, and control transport

## Components

The system consists of two main components:

1. **Ableton Remote Script** (`Ableton_Remote_Script/__init__.py`): A MIDI Remote Script for Ableton Live that creates a socket server to receive and execute commands
2. **MCP Server** (`server.py`): A Python server that implements the Model Context Protocol and connects to the Ableton Remote Script

## Installation

### Installing via Smithery

To install Ableton Live Integration for Claude Desktop automatically via [Smithery](https://smithery.ai/server/@ahujasid/ableton-mcp):

```bash
npx -y @smithery/cli install @ahujasid/ableton-mcp --client claude
```

### Prerequisites

- Ableton Live 10 or newer
- Python 3.8 or newer
- [uv package manager](https://astral.sh/uv)

If you're on Mac, please install uv as:
```
brew install uv
```

Otherwise, install from [uv's official website][https://docs.astral.sh/uv/getting-started/installation/]

⚠️ Do not proceed before installing UV

### Claude for Desktop Integration

[Follow along with the setup instructions video](https://youtu.be/iJWJqyVuPS8)

1. Go to Claude > Settings > Developer > Edit Config > claude_desktop_config.json to include the following:

```json
{
    "mcpServers": {
        "AbletonMCP": {
            "command": "uvx",
            "args": [
                "ableton-mcp"
            ]
        }
    }
}
```

### Cursor Integration

Run ableton-mcp without installing it permanently through uvx. Go to Cursor Settings > MCP and paste this as a command:

```
uvx ableton-mcp
```

⚠️ Only run one instance of the MCP server (either on Cursor or Claude Desktop), not both

### Installing the Ableton Remote Script

[Follow along with the setup instructions video](https://youtu.be/iJWJqyVuPS8)

1. Download the `AbletonMCP_Remote_Script/__init__.py` file from this repo

2. Copy the folder to Ableton's MIDI Remote Scripts directory. Different OS and versions have different locations. **One of these should work, you might have to look**:

   **For macOS:**
   - Method 1: Go to Applications > Right-click on Ableton Live app → Show Package Contents → Navigate to:
     `Contents/App-Resources/MIDI Remote Scripts/`
   - Method 2: If it's not there in the first method, use the direct path (replace XX with your version number):
     `/Users/[Username]/Library/Preferences/Ableton/Live XX/User Remote Scripts`
   
   **For Windows:**
   - Method 1:
     C:\Users\[Username]\AppData\Roaming\Ableton\Live x.x.x\Preferences\User Remote Scripts 
   - Method 2:
     `C:\ProgramData\Ableton\Live XX\Resources\MIDI Remote Scripts\`
   - Method 3:
     `C:\Program Files\Ableton\Live XX\Resources\MIDI Remote Scripts\`
   *Note: Replace XX with your Ableton version number (e.g., 10, 11, 12)*

4. Create a folder called 'AbletonMCP' in the Remote Scripts directory and paste the downloaded '\_\_init\_\_.py' file

3. Launch Ableton Live

4. Go to Settings/Preferences → Link, Tempo & MIDI

5. In the Control Surface dropdown, select "AbletonMCP"

6. Set Input and Output to "None"

## Usage

### Starting the Connection

1. Ensure the Ableton Remote Script is loaded in Ableton Live
2. Make sure the MCP server is configured in Claude Desktop or Cursor
3. The connection should be established automatically when you interact with Claude

### Using with Claude

Once the config file has been set on Claude, and the remote script is running in Ableton, you will see a hammer icon with tools for the Ableton MCP.

## Available Tools

Here is a comprehensive list of all the tools available through the AbletonMCP integration:

### Session & Transport
- `get_session_info()`: Get detailed information about the current Ableton session.
- `set_tempo(tempo: float)`: Set the tempo of the Ableton session.
- `start_playback()`: Start playing the Ableton session.
- `stop_playback()`: Stop playing the Ableton session.
- `undo()`: Undo the last action.
- `redo()`: Redo the last undone action.

### Track Management
- `get_track_info(track_index: int)`: Get detailed information about a specific track.
- `create_midi_track(index: int = -1)`: Create a new MIDI track.
- `create_audio_track(index: int = -1)`: Create a new audio track.
- `create_return_track()`: Create a new return track.
- `delete_track(track_index: int)`: Delete a track.
- `set_track_name(track_index: int, name: str)`: Set the name of a track.
- `group_tracks(track_indices: list)`: Group tracks together.

### Device & Preset Management
- `get_device_details(track_index: int, device_index: int)`: Get detailed information about a specific device on a track.
- `set_device_parameter(track_index: int, device_index: int, parameter_name: str, value: float)`: Set a parameter on a device.
- `randomize_device_parameters(track_index: int, device_index: int)`: Randomize the parameters of a device.
- `save_device_parameters_to_json(track_index: int, device_index: int, filepath: str)`: Saves the parameters of a device to a JSON file.
- `load_device_parameters_from_json(track_index: int, device_index: int, filepath: str)`: Loads the parameters of a device from a JSON file.

### Clip Manipulation
- `create_clip(track_index: int, clip_index: int, length: float = 4.0)`: Create a new MIDI clip.
- `add_notes_to_clip(track_index: int, clip_index: int, notes: list)`: Add MIDI notes to a clip.
- `set_clip_name(track_index: int, clip_index: int, name: str)`: Set the name of a clip.
- `delete_clip(track_index: int, clip_index: int)`: Delete a clip.
- `set_clip_color(track_index: int, clip_index: int, color: int)`: Set the color of a clip.
- `fire_clip(track_index: int, clip_index: int)`: Fire a clip.
- `stop_clip(track_index: int, clip_index: int)`: Stop a clip.
- `generate_midi(track_index: int, clip_index: int, description: str)`: Generates a MIDI clip based on a description.

### Scene Control
- `get_scene_info()`: Get information about all scenes.
- `fire_scene(scene_index: int)`: Fire a scene.
- `create_scene(scene_index: int = -1)`: Create a new scene.
- `rename_scene(scene_index: int, name: str)`: Rename a scene.

### Browser & Loading
- `get_browser_tree(category_type: str = "all")`: Get a hierarchical tree of browser categories.
- `get_browser_items_at_path(path: str)`: Get browser items at a specific path.
- `search_browser(query: str)`: Search the browser for items matching the query.
- `load_instrument_or_effect(track_index: int, uri: str)`: Load an instrument or effect onto a track.
- `load_drum_kit(track_index: int, rack_uri: str, kit_path: str)`: Load a drum rack and then load a specific drum kit into it.

### Real-time MIDI
- `send_note_on(channel: int, note: int, velocity: int)`: Send a MIDI note-on message.
- `send_note_off(channel: int, note: int)`: Send a MIDI note-off message.
- `get_midi_messages()`: Get any MIDI messages received from Ableton since the last call.

## Example Commands

Here are some examples of what you can ask Claude to do:

- "Create an 80s synthwave track" [Demo](https://youtu.be/VH9g66e42XA)
- "Create a Metro Boomin style hip-hop beat"
- "Create a new MIDI track with a synth bass instrument"
- "Add reverb to my drums"
- "Create a 4-bar MIDI clip with a simple melody"
- "Get information about the current Ableton session"
- "Load a 808 drum rack into the selected track"
- "Add a jazz chord progression to the clip in track 1"
- "Set the tempo to 120 BPM"
- "Play the clip in track 2"


## Troubleshooting

- **Connection issues**: Make sure the Ableton Remote Script is loaded, and the MCP server is configured on Claude
- **Timeout errors**: Try simplifying your requests or breaking them into smaller steps
- **Have you tried turning it off and on again?**: If you're still having connection errors, try restarting both Claude and Ableton Live

## Technical Details

### Communication Protocol

The system uses a simple JSON-based protocol over TCP sockets:

- Commands are sent as JSON objects with a `type` and optional `params`
- Responses are JSON objects with a `status` and `result` or `message`

### Limitations & Security Considerations

- Creating complex musical arrangements might need to be broken down into smaller steps
- The tool is designed to work with Ableton's default devices and browser items
- Always save your work before extensive experimentation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

This is a third-party integration and not made by Ableton.
