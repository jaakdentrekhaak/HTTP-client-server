import socket

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = socket.gethostbyname('www.tldp.org')

client.connect((server, 80))

msg = 'GET / HTTP/1.1\r\n'
msg += f'Host: www.tldp.org\r\n'
msg += '\r\n'

client.send(msg.encode())

response = client.recv(1024)

# ind = response.index(b'<html>')

# print(len(response[ind:]))

print(response)