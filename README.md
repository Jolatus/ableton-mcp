# AbletonMCP - Ableton Live Model Context Protocol Integration
[![smithery badge](https://smithery.ai/badge/@ahujasid/ableton-mcp)](https://smithery.ai/server/@ahujasid/ableton-mcp)

AbletonMCP connects Large Language Models like Claude to Ableton Live, allowing the AI to directly interact with and control your DAW. This integration enables prompt-assisted music production, track creation, and Live session manipulation.

### Join the Community

Give feedback, get inspired, and build on top of the MCP: [Discord](https://discord.gg/3ZrMyGKnaU). Made by [Siddharth](https://x.com/sidahuj)

## Architecture Overview

The AbletonMCP system is composed of three main components that work together to bridge the gap between your natural language commands and actions in Ableton Live.

```
+-----------------+      +----------------------+      +--------------------------+
|   LLM Client    |      |   MCP Server         |      |   Ableton Live           |
| (Claude, etc.)  |<---->| (ableton_mcp_server.py)|<---->| (MIDI Remote Script)     |
+-----------------+      +----------------------+      +--------------------------+
       ^                         ^      ^                          ^
       |                         |      |                          |
       | HTTP/S (SSE)            |      | Socket                   | MIDI
       | or Stdio                |      | (Commands/Responses)     | (Real-time Notes)
       |                         |      |                          |
       v                         v      v                          v
+-----------------+      +----------------------+      +--------------------------+
|   User          |      |   MIDI Client        |<---->|   MIDI Server            |
|   Interface     |      | (midi_client.py)     |      | (midi_server.py)         |
+-----------------+      +----------------------+      +--------------------------+
```

1.  **Ableton Remote Script (`AbletonMCP_Remote_Script`)**:
    *   This is a Python script that runs directly inside Ableton Live as a MIDI Remote Script (also known as a Control Surface).
    *   It opens a TCP socket server that listens for commands from the MCP Server.
    *   It's responsible for executing the commands it receives by interacting with the Ableton Live API (e.g., creating a track, adding a device, playing a clip).
    *   It also includes a `MidiServer` that runs in a separate thread. This server creates a virtual MIDI port and listens for incoming MIDI notes from the `SocketMidiServer`, which it then forwards to a selected track in Ableton.

2.  **MCP Server (`MCP_Server`)**:
    *   This is the central hub of the system. It's a Python server that implements the Model Context Protocol (MCP).
    *   It exposes a set of "tools" that an LLM can call. When a tool is called, the server translates the request into a command that the Ableton Remote Script can understand.
    *   It communicates with the Remote Script over a TCP socket, sending commands and receiving responses.
    *   It includes a `MidiClient` for sending real-time MIDI messages to the `MidiServer` in the Remote Script, and a `SocketMidiServer` for receiving MIDI messages from Ableton.
    *   It can be run in two modes:
        *   **Standard I/O:** For use with local clients like the Claude for Desktop app.
        *   **HTTP/S (SSE):** For use with web-based clients or other services that need to connect over the network.

3.  **LLM Client**:
    *   This is the interface you use to interact with the system (e.g., Claude, Cursor, or any other MCP-compatible client).
    *   You give it natural language prompts (e.g., "create a new MIDI track").
    *   The LLM interprets your prompt and decides which tool from the MCP Server to call to fulfill your request.

## Installation and Setup

### Prerequisites

- Ableton Live 10 or newer.
- Python 3.8 or newer.
- `uv` package manager. If you don't have it, you can install it easily:
  - **macOS (via Homebrew):** `brew install uv`
  - **Other systems:** `pip install uv` or follow the [official installation guide](https://docs.astral.sh/uv/getting-started/installation/).

### Step 1: Install the MCP Server

You can install the server using `uvx`, which is a command provided by `uv` to run packages in temporary virtual environments.

**For Claude for Desktop:**

1.  Go to Claude > Settings > Developer > Edit Config > `claude_desktop_config.json`.
2.  Add the following configuration to the `mcpServers` object:

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

**For Cursor:**

1.  Go to Cursor Settings > MCP.
2.  Paste the following command in the command input field:
    ```
    uvx ableton-mcp
    ```

**Important:** Only run one instance of the MCP server at a time (either in Cursor or Claude Desktop, not both).

### Step 2: Install the Ableton Remote Script

1.  Download the `AbletonMCP_Remote_Script` folder from this repository.
2.  Copy the entire `AbletonMCP_Remote_Script` folder into Ableton's MIDI Remote Scripts directory. The location of this directory varies depending on your operating system and Ableton version. Here are some common locations:

    *   **macOS:**
        *   Right-click on the Ableton Live application in your Applications folder and select "Show Package Contents". Navigate to `Contents/App-Resources/MIDI Remote Scripts/`.
        *   Alternatively, check `/Users/[YourUsername]/Library/Preferences/Ableton/Live XX/User Remote Scripts` (where `XX` is your Ableton version).
    *   **Windows:**
        *   `C:\Users\[YourUsername]\AppData\Roaming\Ableton\Live x.x.x\Preferences\User Remote Scripts`
        *   `C:\ProgramData\Ableton\Live XX\Resources\MIDI Remote Scripts\`

3.  Launch Ableton Live.
4.  Go to Settings/Preferences → Link, Tempo & MIDI.
5.  In one of the "Control Surface" dropdowns, select "AbletonMCP".
6.  Set the "Input" and "Output" for the AbletonMCP control surface to "None".

## Security

When you run the MCP server in HTTP mode, you are potentially exposing your Ableton Live session to the network. It is crucial to take steps to secure the server.

### API Key Authentication

The server uses API key authentication to ensure that only authorized clients can send commands.

-   The server expects an API key to be provided in the `Authorization` header of every HTTP request (e.g., `Authorization: Bearer your-api-key`).
-   You must set the `ABLETON_MCP_API_KEY` environment variable on the machine running the server. If this variable is not set, the server will use a default, insecure key and will not be secure.

**Setting the Environment Variable:**

-   **macOS/Linux:**
    ```bash
    export ABLETON_MCP_API_KEY="your-super-secret-and-long-api-key"
    ```
-   **Windows (PowerShell):**
    ```powershell
    $env:ABLETON_MCP_API_KEY="your-super-secret-and-long-api-key"
    ```

### Running with HTTPS (SSL/TLS)

To encrypt the traffic between the client and the server, you should run the server with HTTPS. For local development, you can generate a self-signed certificate.

1.  **Generate a certificate:**
    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    ```
2.  **Run the server with the certificate:**
    Modify the `main` function in `MCP_Server/ableton_mcp_server.py` to include the paths to your key and certificate files:
    ```python
    def main():
        """Run the MCP server"""
        mcp.run(
            transport="sse",
            port=8000,
            ssl_keyfile="key.pem",
            ssl_certfile="cert.pem"
        )
    ```

**Note:** For production use, you should always use a certificate from a trusted Certificate Authority (CA).

## API Reference

Here is a comprehensive list of all the tools available through the AbletonMCP integration.

### Session & Transport
- `get_session_info()`: Get detailed information about the current Ableton session, including tracks, scenes, and tempo.
- `set_tempo(tempo: float)`: Set the tempo of the Ableton session in BPM.
- `start_playback()`: Start playing the Ableton session from the current arrangement position.
- `stop_playback()`: Stop playing the Ableton session.
- `undo()`: Undo the last action performed in Ableton.
- `redo()`: Redo the last undone action.

### Track Management
- `get_track_info(track_index: int)`: Get detailed information about a specific track, including its name, devices, and clips.
- `create_midi_track(index: int = -1)`: Create a new MIDI track. If `index` is not provided, the track is created at the end.
- `create_audio_track(index: int = -1)`: Create a new audio track.
- `create_return_track()`: Create a new return track.
- `delete_track(track_index: int)`: Delete a track at the specified index.
- `set_track_name(track_index: int, name: str)`: Set the name of a track.
- `group_tracks(track_indices: list)`: Group a list of tracks together.

### Device & Preset Management
- `get_device_details(track_index: int, device_index: int)`: Get detailed information about a specific device on a track, including all its parameters.
- `set_device_parameter(track_index: int, device_index: int, parameter_name: str, value: float)`: Set a parameter on a device.
- `randomize_device_parameters(track_index: int, device_index: int)`: Randomize the parameters of a device.
- `save_device_parameters_to_json(track_index: int, device_index: int, filepath: str)`: Saves the parameters of a device to a JSON file.
- `load_device_parameters_from_json(track_index: int, device_index: int, filepath: str)`: Loads the parameters of a device from a JSON file.

### Clip Manipulation
- `create_clip(track_index: int, clip_index: int, length: float = 4.0)`: Create a new MIDI clip.
- `add_notes_to_clip(track_index: int, clip_index: int, notes: list)`: Add MIDI notes to a clip. Each note should be a dictionary with `pitch`, `start_time`, `duration`, and `velocity`.
- `set_clip_name(track_index: int, clip_index: int, name: str)`: Set the name of a clip.
- `delete_clip(track_index: int, clip_index: int)`: Delete a clip.
- `set_clip_color(track_index: int, clip_index: int, color: int)`: Set the color of a clip using an integer representation.
- `fire_clip(track_index: int, clip_index: int)`: Start playing a clip.
- `stop_clip(track_index: int, clip_index: int)`: Stop a clip.
- `loop_clip(track_index: int, clip_index: int, is_looping: bool)`: Set whether a clip should loop.
- `set_clip_length(track_index: int, clip_index: int, length: float)`: Set the length of a clip in beats.

### Intelligent MIDI Generation
- `generate_midi(track_index: int, clip_index: int, description: str)`: Generates a MIDI clip based on a simple description (e.g., "a C major scale").
- `generate_intelligent_midi(track_index: int, clip_index: int, description: str)`: Generates a more complex MIDI clip based on a detailed description (e.g., "a funky bassline in C minor").
- `build_a_drum_beat(genre: str)`: Build a drum beat for a specific genre (e.g., "house", "trap").
- `harmonize_melody(track_index: int, clip_index: int)`: Harmonize a melody with a simple chord progression.

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
- `send_note_on(channel: int, note: int, velocity: int)`: Send a MIDI note-on message in real-time.
- `send_note_off(channel: int, note: int)`: Send a MIDI note-off message in real-time.
- `get_midi_messages()`: Get any MIDI messages received from Ableton since the last call.

## Troubleshooting

- **Connection Issues:**
  - Ensure the "AbletonMCP" Control Surface is selected in Ableton's preferences and that no other scripts are using the same underlying ports.
  - Make sure the MCP server is running (either via your client like Claude or Cursor, or manually).
  - If you're running the server in HTTP mode, ensure that your client can reach the server's address and port, and that your firewall is not blocking the connection.

- **Timeout Errors:**
  - Some commands, like searching the browser or loading complex devices, can take a few moments. If you experience timeouts, try to simplify your requests or wait for the previous command to complete before sending a new one.
  - Restarting Ableton Live can sometimes resolve performance issues.

- **"No module named 'mcp'" errors:**
  - This usually means that the Python environment is not set up correctly. Ensure that you are using `uvx` to run the server, as this will handle the installation of all necessary dependencies in a temporary environment.

- **"Have you tried turning it off and on again?":**
  - Seriously. A clean restart of both Ableton Live and your LLM client can resolve many transient issues.

## Disclaimer

This is a third-party integration and is not officially supported by Ableton. Use it at your own risk, and always save your work before performing complex operations.
