import rtmidi
import threading
import socket
import json
import time

class MidiServer(threading.Thread):
    def __init__(self, mcp):
        super(MidiServer, self).__init__()
        self.mcp = mcp
        self.midi_in = rtmidi.MidiIn()
        self.midi_out = rtmidi.MidiOut()
        self.running = False
        self.sock = None

    def run(self):
        self.mcp.log_message("Starting MIDI server...")
        self.running = True

        try:
            self.midi_in.open_virtual_port("AbletonMCP In")
            self.midi_out.open_virtual_port("AbletonMCP Out")
            self.midi_in.set_callback(self.handle_message)
            self.mcp.log_message("MIDI server started.")

            self.connect_to_server()

            while self.running:
                # Keep the thread alive
                time.sleep(1)

        except Exception as e:
            self.mcp.log_message(f"Error starting MIDI server: {e}")
        finally:
            self.midi_in.close_port()
            self.midi_out.close_port()
            if self.sock:
                self.sock.close()
            self.mcp.log_message("MIDI server stopped.")

    def connect_to_server(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(("localhost", 9878))
            self.mcp.log_message("MIDI server connected to MCP server.")
        except Exception as e:
            self.mcp.log_message(f"MIDI server could not connect to MCP server: {e}")
            self.sock = None

    def stop(self):
        self.running = False

    def handle_message(self, event, data):
        message, deltatime = event
        self.mcp.log_message(f"MIDI Message: {message}, deltatime: {deltatime}")
        self.send_to_server({"type": "midi", "message": message, "deltatime": deltatime})

    def send_message(self, message):
        self.midi_out.send_message(message)

    def send_to_server(self, data):
        if self.sock:
            try:
                self.sock.sendall(json.dumps(data).encode('utf-8'))
            except Exception as e:
                self.mcp.log_message(f"Error sending MIDI to server: {e}")
                self.sock = None
                self.connect_to_server()
