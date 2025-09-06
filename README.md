# AbletonMCP - Ableton Live Model Context Protocol Integration
[![smithery badge](https://smithery.ai/badge/@ahujasid/ableton-mcp)](https://smithery.ai/server/@ahujasid/ableton-mcp)

AbletonMCP connects Large Language Models like Claude to Ableton Live, allowing the AI to directly interact with and control your DAW. This integration enables prompt-assisted music production, track creation, and Live session manipulation.

### Join the Community

Give feedback, get inspired, and build on top of the MCP: [Discord](https://discord.gg/3ZrMyGKnaU). Made by [Siddharth](https://x.com/sidahuj)

## Features

- **Full Session Control:** Manage tracks, scenes, clips, and transport controls.
- **Instrument and Effect Loading:** Search Ableton's browser and load any device onto any track.
- **AI-Powered Music Generation:**
    - Generate complex chord progressions from simple descriptions.
    - Create full song starters with drums, bass, and chords for different genres.
- **Intelligent Sound Design:** Go beyond simple randomization with musically-aware parameter changes.
- **AI Mixing Assistant:** Analyze your mix and get actionable suggestions for improvement, or let the AI apply basic mixing decisions for you.
- **Real-time MIDI:** Send and receive MIDI notes in real-time for interactive performance.

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

1.  **Ableton Remote Script (`AbletonMCP_Remote_Script`)**: A Python script running inside Ableton Live that executes commands received from the MCP Server. It also hosts a MIDI server for real-time note input.
2.  **MCP Server (`MCP_Server`)**: The central hub that translates LLM tool calls into commands for Ableton. It contains the core logic for all the AI-powered features.
3.  **LLM Client**: The interface (e.g., Claude, Cursor) where you type your prompts.

## Installation and Setup

_(Instructions for installation remain the same)_

...

## API Reference

Here is a comprehensive list of all the tools available through the AbletonMCP integration.

### Session & Transport
- `get_session_info()`: Get detailed information about the current Ableton session.
- `set_tempo(tempo: float)`: Set the tempo of the Ableton session in BPM.
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
- `loop_clip(track_index: int, clip_index: int, is_looping: bool)`: Set whether a clip should loop.
- `set_clip_length(track_index: int, clip_index: int, length: float)`: Set the length of a clip in beats.

### Scene Control
- `get_scene_info()`: Get information about all scenes.
- `fire_scene(scene_index: int)`: Fire a scene.
- `create_scene(scene_index: int = -1)`: Create a new scene.
- `rename_scene(scene_index: int, name: str)`: Rename a scene.

### Browser & Loading
- `search_browser(query: str)`: Search the browser for items matching the query.
- `load_instrument_or_effect(track_index: int, uri: str)`: Load an instrument or effect onto a track.

---

### **New: AI-Powered Creative Tools**

This suite of tools leverages music theory and rule-based systems to provide intelligent assistance for songwriting, sound design, and mixing.

#### **Intelligent MIDI Generation**
- `generate_chord_progression(track_index: int, clip_index: int, progression: str, beats_per_chord: float = 4.0, octave: int = 4)`: Generates a MIDI clip with a specified chord progression.
  - **Example:** `generate_chord_progression(track_index=0, clip_index=0, progression="Cmaj7, G7, Am, F")`
- `generate_progression_with_bassline(...)`: Generates both a chord progression and a corresponding bassline on two new tracks.
  - **Example:** `generate_progression_with_bassline(progression="Am, G, C, F", bass_pattern="eighth_notes")`
- `create_song_starter(genre: str, key: str)`: Creates a full song starter with drums, bass, and chords based on a genre.
  - **Example:** `create_song_starter(genre="lo-fi hip hop", key="A minor")`

#### **Creative Sound Design**
- `intelligent_randomize(track_index: int, device_index: int, style: str = "subtle")`: Intelligently randomizes device parameters based on a style ('subtle', 'rhythmic', 'chaotic').
  - **Example:** `intelligent_randomize(track_index=0, device_index=0, style="rhythmic")`

#### **AI Mixing Assistant**
- `analyze_mix()`: Analyzes the current mix and provides suggestions for improvement (e.g., headroom, stereo balance, EQ).
- `auto_mix_tracks()`: Automatically applies basic mixing decisions for volume and panning to create a balanced starting point.

---

### Real-time MIDI
- `send_note_on(channel: int, note: int, velocity: int)`: Send a MIDI note-on message in real-time.
- `send_note_off(channel: int, note: int)`: Send a MIDI note-off message in real-time.
- `get_midi_messages()`: Get any MIDI messages received from Ableton since the last call.

## Troubleshooting

_(Instructions for troubleshooting remain the same)_

...

## Disclaimer

This is a third-party integration and is not officially supported by Ableton. Use it at your own risk, and always save your work before performing complex operations.
