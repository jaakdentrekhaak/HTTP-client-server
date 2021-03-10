# import socket

# client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# server = socket.gethostbyname('www.google.com')

# client.connect((server, 80))

# msg = 'GET / HTTP/1.1\r\n'
# msg += f'Host: www.google.com\r\n'
# msg += '\r\n'

# client.send(msg.encode())
# response = b''
# while not response.endswith(b'\r\n\r\n'):
#     response += client.recv(1024)

# # ind = response.index(b'<html>')

# # print(len(response[ind:]))

# response = response.replace(b'\r\n', b'YEEEEET')

# file = open('test.txt', 'wb')
# file.write(response)

uri = 'www.example.com'

file = open('received.html', 'r')
html = file.read()
msg = 'PUT /received.html HTTP/1.1\r\n'
msg += f'Host: {uri}\r\n'
msg += 'Content-Type: text/html\r\n'
msg += f'Content-Length: {len(html)}\r\n'
msg += '\r\n'
msg += html + '\r\n'
msg += '\r\n'

print(msg)