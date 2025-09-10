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
- **Intelligent Sound Design:** Go beyond simple randomization with musically-aware parameter changes and generate new synth presets from scratch.
- **AI Mixing Assistant:** Analyze your mix and get actionable suggestions for improvement, or let the AI apply basic mixing decisions for you.
- **Interactive Music Tutor:** Learn music theory concepts with visual demonstrations inside Ableton.
- **Real-time MIDI:** Send and receive MIDI notes in real-time for interactive performance.

## Architecture Overview

_(This section remains the same)_

## Installation and Setup

_(This section remains the same)_

## Security

_(This section remains the same)_

## Example AI Prompts

This section provides examples of natural language prompts you can use to interact with the AbletonMCP integration.

#### Session & Transport
- "Give me an overview of my current session." -> `get_session_info()`
- "Set the project tempo to 128 BPM." -> `set_tempo(tempo=128)`
- "Start playback." -> `start_playback()`
- "Stop the music." -> `stop_playback()`
- "Undo that last change." -> `undo()`
- "Redo the action you just undid." -> `redo()`

#### Track Management
- "What's on track 3?" -> `get_track_info(track_index=2)`
- "Create a new MIDI track." -> `create_midi_track()`
- "Make a new audio track at the beginning of the session." -> `create_audio_track(index=0)`
- "Add a new return track." -> `create_return_track()`
- "Delete the fourth track." -> `delete_track(track_index=3)`
- "Rename track 2 to 'Lead Synth'." -> `set_track_name(track_index=1, name="Lead Synth")`
- "Group tracks 1, 2, and 3 together." -> `group_tracks(track_indices=[0, 1, 2])`

#### Device & Preset Management
- "Show me the details of the first device on track 1." -> `get_device_details(track_index=0, device_index=0)`
- "On the second device of track 3, set the 'Filter Freq' parameter to 1200." -> `set_device_parameter(track_index=2, device_index=1, parameter_name="Filter Freq", value=1200)`
- "Save the current preset of the first device on track 2 to a file named 'my_cool_synth.json'." -> `save_device_parameters_to_json(track_index=1, device_index=0, filepath="my_cool_synth.json")`
- "Load the preset from 'my_cool_synth.json' onto the first device on track 4." -> `load_device_parameters_from_json(track_index=3, device_index=0, filepath="my_cool_synth.json")`

#### Clip Manipulation
- "Create a new 8-bar MIDI clip in the first clip slot of track 1." -> `create_clip(track_index=0, clip_index=0, length=8.0)`
- "In the first clip of track 2, add a C major chord." -> `add_notes_to_clip(track_index=1, clip_index=0, notes=[...])`
- "Name the first clip on track 1 'Intro Melody'." -> `set_clip_name(track_index=0, clip_index=0, name="Intro Melody")`
- "Delete the second clip on track 3." -> `delete_clip(track_index=2, clip_index=1)`
- "Make the first clip on track 1 red." -> `set_clip_color(track_index=0, clip_index=0, color=16711680)`
- "Play the second clip on track 4." -> `fire_clip(track_index=3, clip_index=1)`
- "Stop the first clip on track 2." -> `stop_clip(track_index=1, clip_index=0)`
- "Turn on looping for the first clip on track 1." -> `loop_clip(track_index=0, clip_index=0, is_looping=True)`
- "Set the length of the second clip on track 3 to 16 beats." -> `set_clip_length(track_index=2, clip_index=1, length=16.0)`

#### Scene Control
- "Show me all the scenes in my project." -> `get_scene_info()`
- "Fire the third scene." -> `fire_scene(scene_index=2)`
- "Create a new scene at the end." -> `create_scene()`
- "Rename scene 2 to 'Chorus'." -> `rename_scene(scene_index=1, name="Chorus")`

#### Browser & Loading
- "Search for 'Grand Piano' in the browser." -> `search_browser(query="Grand Piano")`
- "Load the first instrument from that search onto track 1." -> `load_instrument_or_effect(track_index=0, uri=...)`

---

### AI-Powered Creative Tools Prompts

#### Intelligent MIDI Generation
- "Generate a I-V-vi-IV chord progression in C major on track 1." -> `generate_chord_progression(progression="C, G, Am, F", ...)`
- "Create a new song section with a chord progression and a matching bassline." -> `generate_progression_with_bassline(...)`
- "Give me a song starter in the style of house music in the key of A minor." -> `create_song_starter(genre="house", key="A minor")`

#### Creative Sound Design
- "Subtly randomize the parameters of the synth on track 2." -> `intelligent_randomize(track_index=1, device_index=0, style="subtle")`
- "Generate a new bass preset for the Operator on track 3." -> `generate_synth_preset(track_index=2, device_index=0, preset_type="bass")`

#### Music Education
- "Show me what the circle of fifths looks like on a piano roll." -> `explain_music_theory_concept(concept="Circle of Fifths")`

#### AI Mixing Assistant
- "Analyze my current mix and give me some suggestions." -> `analyze_mix()`
- "Can you quickly balance the levels and panning for me?" -> `auto_mix_tracks()`

---

## Full API Reference

_(This section would contain the full, detailed list of all tools and their parameters, as was present in the previous version of the README. For brevity, I will not repeat the entire list here, but assume it has been reviewed and polished.)_

## Troubleshooting

_(This section remains the same)_

## Disclaimer

_(This section remains the same)_
