import rtmidi
import threading

class MidiServer(threading.Thread):
    def __init__(self, mcp):
        super(MidiServer, self).__init__()
        self.mcp = mcp
        self.midi_in = rtmidi.MidiIn()
        self.midi_out = rtmidi.MidiOut()
        self.running = False

    def run(self):
        self.mcp.log_message("Starting MIDI server...")
        self.running = True

        try:
            self.midi_in.open_virtual_port("AbletonMCP In")
            self.midi_out.open_virtual_port("AbletonMCP Out")
            self.midi_in.set_callback(self.handle_message)
            self.mcp.log_message("MIDI server started.")

            while self.running:
                # Keep the thread alive
                pass
        except Exception as e:
            self.mcp.log_message(f"Error starting MIDI server: {e}")
        finally:
            self.midi_in.close_port()
            self.midi_out.close_port()
            self.mcp.log_message("MIDI server stopped.")

    def stop(self):
        self.running = False

    def handle_message(self, event, data):
        message, deltatime = event
        self.mcp.log_message(f"MIDI Message: {message}, deltatime: {deltatime}")

    def send_message(self, message):
        self.midi_out.send_message(message)
