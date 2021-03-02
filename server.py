# NOTE: for the demo we have to explain the difference between HTTP/1.0 and HTTP/1.1,
# in the assignment we use HTTP/1.1
import socket

SERVER = "192.168.1.31" # TODO: use socket library to get ipv4 instead of hardcoding
PORT = 5050 # Just some port that's not used by the machine

HEADER = 64 # TODO: figure out what is the right size (bytes) for the received message
FORMAT = 'utf-8' # Find different format when it comes to images
DISCONNECT_MESSAGE = 'disconnect'

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

ADDR = (SERVER, PORT)
server.bind(ADDR)

def start(): # TODO: this will only work for one client at a time -> use threading library to start different threads in parallel for multiple client connection
    server.listen()
    
    while True:
        conn, addr = server.accept() # blocking: waits until client connected
        print('[NEW CONNECTION]', addr[0], 'connected.')
        connected = True
        while connected:
            msg = conn.recv(HEADER).decode(FORMAT).rstrip() # rstrip: remove special characters
            print('[MESSAGE]', msg)
            if msg == DISCONNECT_MESSAGE:
                connected = False
        print('[CLOSE CONNECTION]', addr[0], 'disconnected')
        conn.close()

print('[STARTING] server is starting...')
start()