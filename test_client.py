import socket
import time

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server = '192.168.1.31'

client.connect((server, 5050))

msg = 'GET /server.jpg HTTP/1.1\r\n'
msg += 'Host: 192.168.1.31\r\n'
msg += 'If-Modified-Since: Sun, 13 Mar 2021 17:10:27 GMT\r\n'
msg += '\r\n'

client.send(msg.encode())

def get_content_length(headers):
    """Return Content-Length of response

    Args:
        headers (bytes): headers of HTTP response

    Returns:
        int: length of the body of the HTTP response
    """
    keyword = b'Content-Length:'
    _, keyword, after_keyword = headers.partition(keyword)

    # after_keyword now contains something like 1562\r\n..., so we only need the part before \r\n
    ind = after_keyword.index(b'\r')
    return int(after_keyword[:ind])


headers = b''
# The headers always end with b'\r\n\r\n'
while not headers.endswith(b'\r\n\r\n'):
    response = client.recv(1)
    headers += response


body = b''
content_length = get_content_length(headers)
# NOTE: we can't just do client.recv(content_length), because the buffersize in recv(bufsize) is a maximum
#   so client.recv() can return less bytes than the given buffer size
buff_size = 1024
# Loop as long as the received body is not the same length as given by Content-Length
while len(body) != content_length:
    body += client.recv(buff_size)

print(body)