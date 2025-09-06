import rtmidi

class MidiClient:
    def __init__(self):
        self.midi_out = rtmidi.MidiOut()
        self.available_ports = self.midi_out.get_ports()
        self.port_name = "AbletonMCP Out"
        self.port = None

        for i, port_name in enumerate(self.available_ports):
            if self.port_name in port_name:
                self.port = self.midi_out.open_port(i)
                break

        if not self.port:
            # If the port is not found, we can't send MIDI messages.
            # We should probably log a warning here.
            print(f"Warning: MIDI port '{self.port_name}' not found.")

    def send_note_on(self, channel, note, velocity):
        if self.port:
            self.port.send_message([0x90 | channel, note, velocity])

    def send_note_off(self, channel, note):
        if self.port:
            self.port.send_message([0x80 | channel, note, 0])

    def disconnect(self):
        if self.port:
            self.port.close_port()
