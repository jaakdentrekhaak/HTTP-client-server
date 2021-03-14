import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = '192.168.1.31'

client.connect((server, 5050))

msg = 'GET / HTTP/1.1\r\n'
msg += 'Host: 192.168.1.31\r\n'
msg += '\r\n'

client.send(msg.encode())
response = b''
while not response.endswith(b'\r\n\r\n'):
    response += client.recv(1024)

print(response)