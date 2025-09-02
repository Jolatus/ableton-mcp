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

if __name__ == '__main__':
    # Need to make sure the MCP_Server directory is in the path
    sys.path.insert(0, '.')
    unittest.main()
