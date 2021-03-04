import socket

SERVER = "192.168.1.31" # TODO: use socket library to get ipv4 instead of hardcoding
PORT = 5050 # Just some port that's not used by the machine
ADDR = (SERVER, PORT)

HEADER = 64 # TODO: figure out what is the right size (bytes) for the received message
FORMAT = 'utf-8' # Find different format when it comes to images

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create TCP socket
client.connect(ADDR)

def send(msg):
    message = msg.encode(FORMAT)
    client.send(message)

while True:
    send(input('Enter message: '))
    if bool(client.recv(HEADER).decode(FORMAT)) == False:
        break

print('[CLIENT TERMINATE] Server terminated the connection to this client')