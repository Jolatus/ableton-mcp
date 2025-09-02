import socket
import threading
import json
import queue

class SocketMidiServer(threading.Thread):
    def __init__(self):
        super(SocketMidiServer, self).__init__()
        self.running = False
        self.message_queue = queue.Queue()
        self.server = None

    def run(self):
        self.running = True
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind(("localhost", 9878))
        self.server.listen(1)

        while self.running:
            try:
                client, address = self.server.accept()
                handler = threading.Thread(target=self.handle_client, args=(client,))
                handler.daemon = True
                handler.start()
            except Exception as e:
                if self.running:
                    print(f"Error in SocketMidiServer: {e}")

        if self.server:
            self.server.close()

    def stop(self):
        self.running = False
        # To unblock the accept call
        try:
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("localhost", 9878))
        except:
            pass
        if self.server:
            self.server.close()

    def handle_client(self, client):
        buffer = ''
        while self.running:
            try:
                data = client.recv(4096)
                if not data:
                    break

                buffer += data.decode('utf-8')

                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    try:
                        message = json.loads(line)
                        self.message_queue.put(message)
                    except json.JSONDecodeError:
                        pass
            except Exception:
                break
        client.close()

    def get_messages(self):
        messages = []
        while not self.message_queue.empty():
            messages.append(self.message_queue.get_nowait())
        return messages
