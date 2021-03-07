import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

client.connect(('www.example.com', 80))

client.send('HEAD / HTTP/1.1\r\nHost: www.example.com\r\n\r\n'.encode('utf-8'))

print(client.recv(100))