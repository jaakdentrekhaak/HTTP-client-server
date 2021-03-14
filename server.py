import socket
import threading
from email.utils import formatdate # For formatting date to HTTP date

# Status codes
OK = b'200 OK'
NOT_FOUND = b'404 Not Found'
BAD_REQUEST = b'400 Bad Request'
SERVER_ERROR = b'500 Server Error' 
NOT_MODIFIED = b'304 Not Modified'

# Get ipv4 adress (socket.gethostbyname(socket.gethostname()) returns 127..., not 192...)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
server = s.getsockname()[0]
s.close()

port = 5050 # Just some port that's not used by the machine
addr = (server, port)
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(addr)

def handle_connection(client, _):

    # Get the headers from the client request
    headers = get_headers(client)
    print('headers:', headers)

    # If the headers don't contain the Host: header, respond with 400: Bad Request
    if not b'Host: ' in headers:
        pass # TODO

    # TODO: check in the first line if HTTP/1.1 is used
    
    if headers.startswith(b'GET'):
        do_get(client, headers)

def get_headers(client):
    """Extract the headers from the HTTP client request

    Args:
        client (object): client socket

    Returns:
        bytes: headers from request
    """
    headers = b''

    # The headers always end with b'\r\n\r\n'
    while not headers.endswith(b'\r\n\r\n'):
        response = client.recv(1)
        headers += response
    
    return headers

def do_head(client, headers):
    pass

def do_get(client, headers):
    # Get path of requested file
    path = headers.split(b' ')[1]

    # If path is /, server.html is served
    if path == b'/':
        path = b'server.html'
    
    if path.startswith(b'/'):
        path = path[1:] # Path without first /
    
    try:
        file = open(path, 'r').read()
    except:
        # If file not found, send 404 Not Found
        # TODO
        print('File doesn\'t exist')
        exit()
    
    # Create response bytes
    response = b'HTTP/1.1 ' + OK + b'\r\n'
    
    response += b'Date: ' + formatdate(timeval=None, localtime=False, usegmt=True).encode() + b'\r\n' # Returns date as needed in RFC 2616
    
    response += b'Content-Type: '
    # Currently only supports png, jpeg and html files
    if path.endswith(b'png'):
        response += b'image/png\r\n'
    elif path.endswith(b'jpg'):
        response += b'image/jpg\r\n'
    elif path.endswith(b'html'):
        response += b'text/html\r\n'

    response += b'Content-Length: ' + str(len(file) + len(b'\r\n\r\n')).encode() + b'\r\n'

    response += b'\r\n'

    response += file.encode() # TODO: does this work with images?

    response += b'\r\n\r\n'

    print('response:', response)

    client.send(response)


def do_post(client):
    pass

def do_put(client):
    pass

def main():
    server.listen()
    
    while True:
        client, address = server.accept() # blocking: waits until client connected
        print('[NEW CONNECTION]', address[0], 'connected.')
        threading.Thread(target=handle_connection, args=(client, address)).start()

print('[STARTING] server is starting...')
main()