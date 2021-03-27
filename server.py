import os
import socket
import threading
import time
from datetime import datetime

# Status codes
OK = b'200 OK'
NOT_FOUND = b'404 Not Found'
BAD_REQUEST = b'400 Bad Request'
SERVER_ERROR = b'500 Server Error' 
NOT_MODIFIED = b'304 Not Modified'

def handle_connection(client, _):
    """Handle incoming client connection. 

    Args:
        client (object): Client socket
    """

    while True:
        # Get the headers from the client request
        headers = get_headers(client)
        print('[REQUEST] headers:', headers)

        # If the headers don't contain the Host: header, respond with 400: Bad Request
        if not b'Host: ' in headers:
            client.send(create_error_message(BAD_REQUEST))

        else:
            if headers.startswith(b'GET'):
                do_get(client, headers)
            elif headers.startswith(b'HEAD'):
                do_head(client, headers)
            elif headers.startswith(b'PUT') or headers.startswith(b'POST'):
                do_post_put(client, headers)
            else:
                # Send server error if command not found
                client.send(create_error_message(SERVER_ERROR))

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

def create_head_message(path):
    """Create a HTTP message for HEAD request

    Args:
        path (bytes): path of the requested file

    Returns:
        response (bytes): HTTP message
        data (bytes): content of requested file
    """
    if path.endswith(b'png') or path.endswith(b'jpg'):
        file = open(path, 'rb')
    else:
        file = open(path, 'r')
    data = file.read()
    file.close()
    
    # Create response bytes
    response = b'HTTP/1.1 ' + OK + b'\r\n'
    
    response += b'Date: ' + datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT").encode() + b'\r\n' # Returns date as needed in RFC 2616
    
    response += b'Content-Type: '

    # Currently only supports png, jpeg and html files
    if path.endswith(b'png'):
        response += b'image/png\r\n'
    elif path.endswith(b'jpg'):
        response += b'image/jpg\r\n'
    elif path.endswith(b'html'):
        response += b'text/html\r\n'

    if path.endswith(b'png') or path.endswith(b'jpg'):
        response += b'Content-Length: ' + str(len(data)).encode() + b'\r\n\r\n'
    else:
        response += b'Content-Length: ' + str(len(data) + len(b'\r\n\r\n')).encode() + b'\r\n\r\n'

    return response, data

def head_response(headers):
    """Generate the HTTP response for a HEAD request.

    Args:
        headers (bytes): Headers of the client request.

    Returns:
        response (bytes): Response to a HEAD request
        path (string): path of the requested file
        data (object): the content of the requested file if it exists or something_went_wrong.html if the requested file is not found
    """
    data = None

    # Get path of requested file
    path = headers.split(b' ')[1]

    # If path is /, server.html is served
    if path == b'/':
        path = b'server.html'
    
    if path.startswith(b'/'):
        path = path[1:] # Path without first /
    
    # Check if file exists
    if not os.path.isfile(path):
        response = create_error_message(NOT_FOUND)

    # Check if file is modified since given date
    elif b'If-Modified-Since' in headers and not is_modified_since(headers):
        response = b'HTTP/1.1 ' + NOT_MODIFIED + b'\r\n'
        response += b'Date: ' + datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT").encode() + b'\r\n' # Returns date as needed in RFC 2616
        response += b'\r\n'

    else:
        response, data = create_head_message(path)


    return response, path, data

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
    response, path, data = head_response(headers)

    # If there was an error, data will be None (so an error message will be sent)
    if data is not None:
        if path.endswith(b'png') or path.endswith(b'jpg'):
            response += data
        else:
            response += data.encode()
            response += b'\r\n\r\n'

    client.send(response)

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

def get_client_input(client, headers):
    """Get the client input from the HTTP request

    Args:
        client (object): Client socket
        headers (bytes): Headers of the client request

    Returns:
        bytes: Body of the client request
    """
    body = b''
    content_length = get_content_length(headers)
    # NOTE: we can't just do client.recv(content_length), because the buffersize in recv(bufsize) is a maximum
    #   so client.recv() can return less bytes than the given buffer size
    buff_size = 1024
    # Loop as long as the received body is not the same length as given by Content-Length
    while len(body) != content_length:
        body += client.recv(buff_size)
    return body

def do_post_put(client, headers):
    """Handle POST and PUT request. Both are similar in functionality. 
    For a POST, the data is appended to the existing file or a new file is created.
    For a PUT, a new file is created.
    NOTE: For this project I just store the incoming files in the same folder (server_text_files), 
    so I don't look at the specified given path (but I do look at the name of the file). 
    We can create different directories to match the given path, but then this directory would look ugly.

    Args:
        client (object): Client socket
        headers (bytes): Headers of the client request
    """

    # Get name of the given file (without the given directory)
    path = headers.split(b' ')[1].decode('utf-8')
    total_file_name = path.split('/')[-1] # E.g. index.html
    file_name = total_file_name.split('.')[0] # E.g. index

    # Get client input
    data = get_client_input(client, headers)

    # If POST: append to existing file or create new one if file doesn't exist
    if headers.startswith(b'POST'):
        file = open('server_text_files/' + file_name + '.txt', 'ab')
    # If PUT: create new file
    elif headers.startswith(b'PUT'):
        file = open('server_text_files/' + file_name + '.txt', 'wb')
    file.write(data)
    file.close()

    # Send response to server
    response = b'HTTP/1.1 ' + OK + b'\r\n'
    response += b'Date: ' + datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT").encode() + b'\r\n' # Returns date as needed in RFC 2616
    file = open('server.html', 'r')
    data = file.read()
    file.close()
    response += b'Content-Type: text/html\r\n'
    response += b'Content-Length: ' + str(len(data) + len(b'\r\n\r\n')).encode() + b'\r\n\r\n'
    response += data.encode()
    response += b'\r\n\r\n'
    
    client.send(response)


def is_modified_since(headers):
    """Check if the requested file is modified since the date given in the If-Modified-Since header

    Args:
        headers (bytes): Headers of the client HTTP request

    Returns:
        boolean: Is file modified since given date?
    """
    # Get path of requested file
    path = headers.split(b' ')[1].decode('utf-8')

    # If path is /, server.html is served
    if path == '/':
        path = 'server.html'
    
    if path.startswith('/'):
        path = path[1:] # Path without first /

    # Date will be given as: If-Modified-Since: Sun, 14 Mar 2021 17:10:27 GMT
    index_start = headers.index(b'If-Modified-Since: ') + len(b'If-Modified-Since: ')
    temp = headers[index_start:]
    index_end = temp.index(b'GMT') + len(b'GMT')
    date = temp[:index_end].decode('utf-8') # E.g. Sun, 14 Mar 2021 17:10:27 GMT

    # Parse RFC 2616 date to seconds since epoch
    date_to_check = time.mktime(time.strptime(date, '%a, %d %b %Y %H:%M:%S %Z'))

    # Get date/time of last modification (returns seconds since epoch)
    moddate = os.stat(path)[8]

    return moddate > date_to_check
    

def create_error_message(error):
    """Create an HTTP response for an error message

    Args:
        error (string): The type of error

    Returns:
        bytes: HTTP response
    """
    response = b'HTTP/1.1 ' + error + b'\r\n'
    response += b'Date: ' + datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT").encode() + b'\r\n' # Returns date as needed in RFC 2616
    file = open('something_went_wrong.html', 'r')
    data = file.read()
    file.close()
    response += b'Content-Type: text/html\r\n'
    response += b'Content-Length: ' + str(len(data)).encode() + b'\r\n\r\n'
    response += data.encode()
    response += b'\r\n\r\n'

    return response

def main():
    # Get ipv4 adress (socket.gethostbyname(socket.gethostname()) returns 127..., not 192...)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    server = s.getsockname()[0]
    s.close()

    port = 5050 # Just some port that's not used by the machine
    addr = (server, port)
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(addr)

    server.listen()
    
    while True:
        client, address = server.accept() # blocking: waits until client connected
        print('[NEW CONNECTION]', address[0], 'connected.')
        threading.Thread(target=handle_connection, args=(client, address)).start()

if __name__ == '__main__':
    print('[START] server is running...')
    main()
