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
    create_midi_track,
    set_track_name,
    create_clip,
    add_notes_to_clip,
    set_clip_name,
    set_tempo,
    load_instrument_or_effect,
    fire_clip,
    stop_clip,
    start_playback,
    stop_playback,
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

if __name__ == '__main__':
    # Need to make sure the MCP_Server directory is in the path
    sys.path.insert(0, '.')
    unittest.main()
