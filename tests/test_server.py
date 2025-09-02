import unittest
from unittest.mock import MagicMock, patch
import json
import sys

# Mock the mcp library before importing the server
from mcp.server.fastmcp import FastMCP

# A mock context object
class MockContext:
    pass

# Import the functions to be tested
from MCP_Server.server import (
    get_session_info,
    get_track_info,
    get_device_details,
    set_device_parameter,
    get_scene_info,
    fire_scene,
    create_scene,
    rename_scene,
    delete_clip,
    set_clip_color,
    set_volume,
    set_panning,
    set_send,
    create_audio_track,
    create_return_track,
    delete_track,
    search_browser,
    group_tracks,
    generate_midi,
    send_note_on,
    send_note_off,
    get_midi_messages,
    create_midi_track,
    set_track_name,
    create_clip,
    add_notes_to_clip,
    set_clip_name,
    set_tempo,
    load_instrument_or_effect,
    stop_clip,
    start_playback,
    stop_playback,
    undo,
    redo,
    randomize_device_parameters,
    save_device_parameters_to_json,
    load_device_parameters_from_json,
    get_browser_tree,
    get_browser_items_at_path,
    load_drum_kit,
)

class TestAbletonMCPServer(unittest.TestCase):

    def setUp(self):
        self.ctx = MockContext()

    @patch('MCP_Server.server.get_ableton_connection')
    def test_get_device_details(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn

        expected_response = {
            "index": 0,
            "name": "Simpler",
            "class_name": "SimplerDevice",
            "type": "instrument",
            "is_active": True,
            "parameters": [
                {"name": "Volume", "value": 0.8},
                {"name": "Pan", "value": 0.0}
            ]
        }
        mock_conn.send_command.return_value = expected_response

        # Act
        result_str = get_device_details(self.ctx, track_index=0, device_index=0)
        result = json.loads(result_str)

        # Assert
        mock_conn.send_command.assert_called_once_with("get_device_details", {"track_index": 0, "device_index": 0})
        self.assertEqual(result, expected_response)

    @patch('MCP_Server.server.get_ableton_connection')
    def test_get_track_info_with_devices(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn

        expected_response = {
            "index": 0,
            "name": "Track 1",
            "devices": [
                {
                    "index": 0,
                    "name": "Simpler",
                    "class_name": "SimplerDevice",
                    "type": "instrument",
                    "is_active": True,
                    "parameters": [
                        {"name": "Volume", "value": 0.8},
                        {"name": "Pan", "value": 0.0}
                    ]
                }
            ]
        }
        mock_conn.send_command.return_value = expected_response

        # Act
        result_str = get_track_info(self.ctx, track_index=0)
        result = json.loads(result_str)

        # Assert
        mock_conn.send_command.assert_called_once_with("get_track_info", {"track_index": 0})
        self.assertEqual(result, expected_response)

    @patch('MCP_Server.server.get_ableton_connection')
    def test_set_device_parameter(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn

        expected_response = {
            "track_index": 0,
            "device_index": 0,
            "parameter_name": "Volume",
            "value": 0.5
        }
        mock_conn.send_command.return_value = expected_response

        # Act
        result_str = set_device_parameter(self.ctx, track_index=0, device_index=0, parameter_name="Volume", value=0.5)

        # Assert
        mock_conn.send_command.assert_called_once_with("set_device_parameter", {
            "track_index": 0,
            "device_index": 0,
            "parameter_name": "Volume",
            "value": 0.5
        })
        self.assertEqual(result_str, "Set parameter 'Volume' on device 0 of track 0 to 0.5")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_get_scene_info(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        expected_response = [{"index": 0, "name": "Scene 1"}]
        mock_conn.send_command.return_value = expected_response

        # Act
        result_str = get_scene_info(self.ctx)
        result = json.loads(result_str)

        # Assert
        mock_conn.send_command.assert_called_once_with("get_scene_info")
        self.assertEqual(result, expected_response)

    @patch('MCP_Server.server.get_ableton_connection')
    def test_fire_scene(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"fired": True, "scene_index": 0}

        # Act
        result_str = fire_scene(self.ctx, scene_index=0)

        # Assert
        mock_conn.send_command.assert_called_once_with("fire_scene", {"scene_index": 0})
        self.assertEqual(result_str, "Fired scene 0")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_create_scene(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"created": True, "scene_index": 1}

        # Act
        result_str = create_scene(self.ctx, scene_index=1)

        # Assert
        mock_conn.send_command.assert_called_once_with("create_scene", {"scene_index": 1})
        self.assertEqual(result_str, "Created scene at index 1")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_rename_scene(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"renamed": True, "scene_index": 0, "name": "New Name"}

        # Act
        result_str = rename_scene(self.ctx, scene_index=0, name="New Name")

        # Assert
        mock_conn.send_command.assert_called_once_with("rename_scene", {"scene_index": 0, "name": "New Name"})
        self.assertEqual(result_str, "Renamed scene 0 to 'New Name'")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_delete_clip(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"deleted": True, "track_index": 0, "clip_index": 0}

        # Act
        result_str = delete_clip(self.ctx, track_index=0, clip_index=0)

        # Assert
        mock_conn.send_command.assert_called_once_with("delete_clip", {"track_index": 0, "clip_index": 0})
        self.assertEqual(result_str, "Deleted clip at track 0, slot 0")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_set_clip_color(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"color_set": True, "track_index": 0, "clip_index": 0, "color": 16711680}

        # Act
        result_str = set_clip_color(self.ctx, track_index=0, clip_index=0, color=16711680)

        # Assert
        mock_conn.send_command.assert_called_once_with("set_clip_color", {"track_index": 0, "clip_index": 0, "color": 16711680})
        self.assertEqual(result_str, "Set color of clip at track 0, slot 0 to 16711680")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_set_volume(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"track_index": 0, "volume": 0.5}

        # Act
        result_str = set_volume(self.ctx, track_index=0, volume=0.5)

        # Assert
        mock_conn.send_command.assert_called_once_with("set_volume", {"track_index": 0, "volume": 0.5})
        self.assertEqual(result_str, "Set volume of track 0 to 0.5")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_set_panning(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"track_index": 0, "panning": -0.5}

        # Act
        result_str = set_panning(self.ctx, track_index=0, panning=-0.5)

        # Assert
        mock_conn.send_command.assert_called_once_with("set_panning", {"track_index": 0, "panning": -0.5})
        self.assertEqual(result_str, "Set panning of track 0 to -0.5")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_set_send(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"track_index": 0, "send_index": 0, "value": 0.8}

        # Act
        result_str = set_send(self.ctx, track_index=0, send_index=0, value=0.8)

        # Assert
        mock_conn.send_command.assert_called_once_with("set_send", {"track_index": 0, "send_index": 0, "value": 0.8})
        self.assertEqual(result_str, "Set send 0 of track 0 to 0.8")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_create_audio_track(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"index": 1, "name": "Audio"}

        # Act
        result_str = create_audio_track(self.ctx, index=1)

        # Assert
        mock_conn.send_command.assert_called_once_with("create_audio_track", {"index": 1})
        self.assertEqual(result_str, "Created new audio track: Audio")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_create_return_track(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"index": 0, "name": "A Reverb"}

        # Act
        result_str = create_return_track(self.ctx)

        # Assert
        mock_conn.send_command.assert_called_once_with("create_return_track")
        self.assertEqual(result_str, "Created new return track: A Reverb")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_delete_track(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"deleted": True, "track_index": 1}

        # Act
        result_str = delete_track(self.ctx, track_index=1)

        # Assert
        mock_conn.send_command.assert_called_once_with("delete_track", {"track_index": 1})
        self.assertEqual(result_str, "Deleted track 1")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_search_browser(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        expected_response = [
            {
                "name": "Simpler",
                "uri": "query:Synths#Simpler",
                "is_folder": False,
                "is_loadable": True,
                "path": "Instruments/Simpler"
            }
        ]
        mock_conn.send_command.return_value = expected_response

        # Act
        result_str = search_browser(self.ctx, query="Simpler")
        result = json.loads(result_str)

        # Assert
        mock_conn.send_command.assert_called_once_with("search_browser", {"query": "Simpler"})
        self.assertEqual(result, expected_response)

    @patch('MCP_Server.server.get_ableton_connection')
    def test_group_tracks(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"grouped": True, "group_track_index": 2, "name": "Group 1"}

        # Act
        result_str = group_tracks(self.ctx, track_indices=[0, 1])

        # Assert
        mock_conn.send_command.assert_called_once_with("group_tracks", {"track_indices": [0, 1]})
        self.assertEqual(result_str, "Grouped tracks [0, 1] into new track 'Group 1'")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_generate_midi(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn

        # Mock the send_command to simulate the two calls made by generate_midi
        mock_conn.send_command.side_effect = [
            {"name": "new_clip", "length": 4.0},  # Response from create_clip
            {"note_count": 8}  # Response from add_notes_to_clip
        ]

        # Act
        result_str = generate_midi(self.ctx, track_index=0, clip_index=0, description="a simple C major scale")

        # Assert
        self.assertEqual(mock_conn.send_command.call_count, 2)
        mock_conn.send_command.assert_any_call("create_clip", {"track_index": 0, "clip_index": 0, "length": 4.0})
        self.assertEqual(result_str, "Generated MIDI clip with 8 notes on track 0, slot 0")

    @patch('MCP_Server.server.MidiClient')
    def test_send_note_on(self, MockMidiClient):
        # Arrange
        mock_midi_client = MockMidiClient.return_value
        import MCP_Server.server
        MCP_Server.server._midi_client = mock_midi_client

        # Act
        result_str = send_note_on(self.ctx, channel=0, note=60, velocity=100)

        # Assert
        mock_midi_client.send_note_on.assert_called_once_with(0, 60, 100)
        self.assertEqual(result_str, "Sent note on: channel=0, note=60, velocity=100")

    @patch('MCP_Server.server.MidiClient')
    def test_send_note_off(self, MockMidiClient):
        # Arrange
        mock_midi_client = MockMidiClient.return_value
        import MCP_Server.server
        MCP_Server.server._midi_client = mock_midi_client

        # Act
        result_str = send_note_off(self.ctx, channel=0, note=60)

        # Assert
        mock_midi_client.send_note_off.assert_called_once_with(0, 60)
        self.assertEqual(result_str, "Sent note off: channel=0, note=60")

    @patch('MCP_Server.server.SocketMidiServer')
    def test_get_midi_messages(self, MockSocketMidiServer):
        # Arrange
        mock_socket_midi_server = MockSocketMidiServer.return_value
        import MCP_Server.server
        MCP_Server.server._socket_midi_server = mock_socket_midi_server

        expected_messages = [{"type": "midi", "message": [144, 60, 100], "deltatime": 0.0}]
        mock_socket_midi_server.get_messages.return_value = expected_messages

        # Act
        result_str = get_midi_messages(self.ctx)
        result = json.loads(result_str)

        # Assert
        mock_socket_midi_server.get_messages.assert_called_once()
        self.assertEqual(result, expected_messages)

    @patch('MCP_Server.server.get_ableton_connection')
    def test_undo(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"undone": True}

        # Act
        result_str = undo(self.ctx)

        # Assert
        mock_conn.send_command.assert_called_once_with("undo")
        self.assertEqual(result_str, "Undone last action.")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_redo(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"redone": True}

        # Act
        result_str = redo(self.ctx)

        # Assert
        mock_conn.send_command.assert_called_once_with("redo")
        self.assertEqual(result_str, "Redone last action.")

    @patch('MCP_Server.server.get_ableton_connection')
    def test_randomize_device_parameters(self, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn
        mock_conn.send_command.return_value = {"randomized": True}

        # Act
        result_str = randomize_device_parameters(self.ctx, track_index=0, device_index=0)

        # Assert
        mock_conn.send_command.assert_called_once_with("randomize_device_parameters", {"track_index": 0, "device_index": 0})
        self.assertEqual(result_str, "Randomized parameters for device 0 on track 0")

    @patch('MCP_Server.server.get_ableton_connection')
    @patch('builtins.open', new_callable=unittest.mock.mock_open)
    @patch('json.dump')
    def test_save_device_parameters_to_json(self, mock_json_dump, mock_open, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn

        expected_parameters = [{"name": "Volume", "value": 0.8}]
        mock_conn.send_command.return_value = {"parameters": expected_parameters}

        filepath = "test.json"

        # Act
        result_str = save_device_parameters_to_json(self.ctx, track_index=0, device_index=0, filepath=filepath)

        # Assert
        mock_conn.send_command.assert_called_once_with("get_device_details", {"track_index": 0, "device_index": 0})
        mock_open.assert_called_once_with(filepath, "w")
        mock_json_dump.assert_called_once_with(expected_parameters, mock_open(), indent=2)
        self.assertEqual(result_str, f"Saved {len(expected_parameters)} parameters to {filepath}")

    @patch('MCP_Server.server.get_ableton_connection')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='[{"name": "Volume", "value": 0.5}]')
    @patch('json.load')
    def test_load_device_parameters_from_json(self, mock_json_load, mock_open, mock_get_ableton_connection):
        # Arrange
        mock_conn = MagicMock()
        mock_get_ableton_connection.return_value = mock_conn

        mock_json_load.return_value = [{"name": "Volume", "value": 0.5}]

        filepath = "test.json"

        # Act
        result_str = load_device_parameters_from_json(self.ctx, track_index=0, device_index=0, filepath=filepath)

        # Assert
        mock_open.assert_called_once_with(filepath, "r")
        mock_json_load.assert_called_once_with(mock_open())
        mock_conn.send_command.assert_called_once_with("set_device_parameters", {
            "track_index": 0,
            "device_index": 0,
            "parameters": [{"name": "Volume", "value": 0.5}]
        })
        self.assertEqual(result_str, f"Loaded 1 parameters from {filepath}")

if __name__ == '__main__':
    # Need to make sure the MCP_Server directory is in the path
    sys.path.insert(0, '.')
    unittest.main()
