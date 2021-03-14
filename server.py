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

    while True:
        # Get the headers from the client request
        headers = get_headers(client)
        print('[REQUEST] headers:', headers)

        # If the headers don't contain the Host: header, respond with 400: Bad Request
        if not b'Host: ' in headers:
            response = b'HTTP/1.1 ' + BAD_REQUEST + b'\r\n'
            response += b'Date: ' + formatdate(timeval=None, localtime=False, usegmt=True).encode() + b'\r\n' # Returns date as needed in RFC 2616
            file = open('something_went_wrong.html', 'r').read()
            response += b'Content-Type: text/html\r\n'
            response += b'Content-Length: ' + str(len(file)).encode() + b'\r\n\r\n'
            response += file.encode()
            response += b'\r\n\r\n'
            client.send(response)

        else:
            modified = True
            if b'If-Modified-Since' in headers:
                # Check if file is modified since given date.
                date = get_modified_since(headers)
                # If file not modified: modified = False and return 304 Not Modified
                # TODO
            if modified:
                if headers.startswith(b'GET'):
                    do_get(client, headers)
                elif headers.startswith(b'HEAD'):
                    do_head(client, headers)
                elif headers.startswith(b'POST'):
                    do_post(client, headers)
                elif headers.startswith(b'PUT'):
                    do_put(client, headers)
                else:
                    print('[UNKNOWN CMD] The given command is unknown')

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

def head_response(headers):
    """Generate the HTTP response for a HEAD request.

    Args:
        headers (bytes): Headers of the client request.

    Returns:
        response (bytes): Response to a HEAD request
        path (string): path of the requested file
        file (object): the requested file if it exists or something_went_wrong.html if the requested file is not found
    """
    # Get path of requested file
    path = headers.split(b' ')[1]

    # If path is /, server.html is served
    if path == b'/':
        path = b'server.html'
    
    if path.startswith(b'/'):
        path = path[1:] # Path without first /
    
    try: # If requested file exists
        if path.endswith(b'png') or path.endswith(b'jpg'):
            file = open(path, 'rb').read()
        else:
            file = open(path, 'r').read()
        
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

        if path.endswith(b'png') or path.endswith(b'jpg'):
            response += b'Content-Length: ' + str(len(file)).encode() + b'\r\n\r\n'
        else:
            response += b'Content-Length: ' + str(len(file) + len(b'\r\n\r\n')).encode() + b'\r\n\r\n'

    except IOError: # If requested file doesn't exist
        # If file not found, send 404 Not Found
        # Create response bytes
        response = b'HTTP/1.1 ' + NOT_FOUND + b'\r\n'
        
        response += b'Date: ' + formatdate(timeval=None, localtime=False, usegmt=True).encode() + b'\r\n' # Returns date as needed in RFC 2616
        
        file = open('something_went_wrong.html', 'r').read()
        response += b'Content-Type: text/html\r\n'
        response += b'Content-Length: ' + str(len(file)).encode() + b'\r\n\r\n'
        response += file.encode()
        response += b'\r\n\r\n'

    return response, path, file

def do_head(client, headers):
    """Send response to a HEAD request.

    Args:
        client (object): Client socket
        headers (bytes): Headers of the client request
    """
    response, _, _ = head_response(headers)

    client.send(response)

def do_get(client, headers):
    """Send a response to a GET request.

    Args:
        client (object): Client socket
        headers (bytes): Headers of the client request
    """
    # The response to a GET request is the same as for a HEAD request, except now the requested file is included (if found)
    response, path, file = head_response(headers)

    if path.endswith(b'png') or path.endswith(b'jpg'):
        response += file
    else:
        response += file.encode()
        response += b'\r\n\r\n'

    client.send(response)


def do_post(client, headers):
    pass

def do_put(client, headers):
    pass

def get_modified_since(headers):
    pass
    # TODO

def main():
    server.listen()
    
    while True:
        client, address = server.accept() # blocking: waits until client connected
        print('[NEW CONNECTION]', address[0], 'connected.')
        threading.Thread(target=handle_connection, args=(client, address)).start()

print('[STARTING] server is starting...')
main()