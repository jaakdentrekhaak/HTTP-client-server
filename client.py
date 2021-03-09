import socket
from bs4 import BeautifulSoup
import os
from pathlib import Path


HTTP_COMMANDS = ('HEAD', 'GET', 'PUT', 'POST') # Possible HTTP commands for this implementation


# Get URI (e.g. http://www.google.com)
uri = input('URI: 1. example, 2. google, 3. tcpipguide, 4. jmarshall, 5. tldp, 6. tinyos, 7. linux-ip: ') or 'www.example.com'

if uri == '1':
    uri = 'www.example.com'
elif uri == '2':
    uri = 'www.google.com'
elif uri == '3':
    uri = 'www.tcpipguide.com'
elif uri == '4':
    uri = 'www.jmarshall.com'
elif uri == '5':
    uri = 'www.tldp.org'
elif uri == '6':
    uri = 'www.tinyos.net'
elif uri == '7':
    uri = 'www.linux-ip.net'

# Parse URI (e.g. www.google.com)
if uri.startswith('http://'):
    uri = uri[len('http://'):]

# Get port
port = input('Port (press enter to use default): ') or 80

# Create TCP socket with ipv4
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server
try:  
    server = socket.gethostbyname(uri) # TODO: also possible that user wants to connect to given ipv4 adress
except socket.gaierror:  
    # this means could not resolve the host  
    print ('There was an error resolving the host') 
    exit()
client.connect((server, port))


def make_GET(path):
    """Generate GET message with given path

    Args:
        path (string): path to request

    Returns:
        string: GET message
    """
    msg = f'GET {path} HTTP/1.1\r\n'
    msg += f'Host:{uri}\r\n'
    msg += '\r\n'

    return msg

def do_command(cmd):
    """Send HTTP request to the server depending on the type of command

    Args:
        cmd (string): One of the possible HTTP commands
    """
    if cmd not in HTTP_COMMANDS:
        print('[INVALID COMMAND] Command not recognized')
        exit()

    if cmd == 'HEAD':
        msg = 'HEAD / HTTP/1.1\r\n'
        msg += f'Host:{uri}\r\n'
        msg += '\r\n'
    elif cmd == 'GET':
        msg = make_GET('/')
    elif cmd == 'PUT':
        put_text = input('PUT text: ')
        msg = 'PUT / HTTP/1.1\r\n'
        msg += f'Host:{uri}\r\n'
        msg += 'Content-Type: text/html\r\n'
        msg += f'Content-Length: {len(put_text)}\r\n'
        msg += '\r\n'
        msg += put_text + '\r\n'
        msg += '\r\n'
    elif cmd == 'POST':
        post_text = input('POST text: ')
        msg = 'POST / HTTP/1.1\r\n'
        msg += f'Host:{uri}\r\n'
        msg += 'Content-Type: text/html\r\n'
        msg += f'Content-Length: {len(post_text)}\r\n'
        msg += '\r\n'
        msg += post_text + '\r\n'
        msg += '\r\n'

    client.send(msg.encode()) # Encode with default utf-8

def get_html_body(resp):
    """Return html body from HTTP response

    Args:
        resp (bytes): HTTP response

    Returns:
        string: HTML body
    """
    # Get HTML body
    # TODO: maybe use content-length and transfer-encoding?
    start = resp.index(b'<!doctype html>')
    end = resp.index(b'</html>') + len(b'</html>')
    body = resp[start:end]

    return body

def store_html(html):
    """Store html into HTML file

    Args:
        html (BeautifulSoup): HTML
    """
    # Store HTML body
    file = open('received.html', 'w')
    file.write(html.prettify())
    file.close()


def store_img(img, path):
    """Store image response from server in local directory

    Args:
        img (bytes): image response from server
        path (string): path where image needs to be stored
    """
    # path = /blabla/blabla/blabla.png
    dirs = path.split('/') # Result: ['', 'blabla', 'blabla', 'blabla.png']
    dirs = dirs[:-1] # Result: ['', 'blabla', 'blabla']
    dirs = '.' + '/'.join(dirs) # Result: './blabla/blabla'

    # Create directory if it doesn't exist
    Path(dirs).mkdir(parents=True, exist_ok=True)

    file = open('.' + path, 'wb')
    file.write(img)
    file.close()


def request_img(url):
    """Request the image from the server and store it locally in the same relative path.
    External urls should just be downloaded in a folder, but are not used.

    Args:
        url (string): url/path of the image
    """
    ## Local images (GET to current server)
    if not url.startswith('http'):
        if not url.startswith('/'):
            url = '/' + url
        msg = make_GET(url)
        client.send(msg.encode())
        resp = handle_get_response()
        store_img(resp, url)


    ## External images (open other socket to external server)
    # TODO
    print('External message not yet implemented')


def fix_html(html):
    """Find missing images in the given html, request them from the server and
    store them locally.

    Images can be stored locally:
        e.g. /images/nav_logo229.png
    or loaded from external website:
        e.g. https://ssl.gstatic.com/gb/images/b_8d5afc09.png
    
    Images will be stored in <img ... src="">

    Args:
        html (BeautifulSoup): HTML body
    """

    imgs = html.findAll('img')

    for img in imgs:
        request_img(img['src'])

def receive_response():
    """Receive response from server after request

    Returns:
        bytes: HTTP response from server
    """
    resp = b''
    while True:
        received = client.recv(1024)
        resp += received
        # TODO: use Content-Length and Transfer-Encoding: chunked
        if received.endswith(b'\r\n\r\n'):
            break
    return resp

def get_content_length(head):
    """Return Content-Length of response

    Args:
        head (bytes): header of HTTP response

    Returns:
        int: length of the body of the HTTP response
    """
    keyword = b'Content-Length:'
    _, keyword, after_keyword = head.partition(keyword)

    # after_keyword now contains something like 1562\r\n..., so we only need the part before \r\n
    ind = after_keyword.index(b'\r')
    return int(after_keyword[:ind])


def handle_get_response():
    """Receive HTTP response from server and return response body

    Returns:
        bytes: HTTP response body
    """
    header = b''
    
    # First get headers: read byte per byte until we have the headers
    # If we get b'\r\n\r\n', the header is read
    while not header.endswith(b'\r\n\r\n'):
        response = client.recv(1)
        header += response
    
    # See if we need to use content-length or transfer-encoding
    if b'Content-Length' in header:
        body = b''
        content_length = get_content_length(header)
        # NOTE: we can't just do client.recv(content_length), because the buffersize in recv(bufsize) is a maximum
        #   so client.recv() can return less bytes than the given buffer size
        buff_size = 1024
        # Loop as long as the received body is not the same length as given by Content-Length
        while len(body) != content_length:
            body += client.recv(buff_size)
    else:
        print('Transfer-Encoding not yet implemented')
    
    return body


def main():
    # Get HTTP command
    command = input('HTTP command: ')

    do_command(command)


    # Store HTML body in file
    if command == 'GET':
        # Get HTML body
        body = handle_get_response()

        # Prettify body
        soup = BeautifulSoup(body, 'html.parser')

        # Store body
        store_html(soup)

        # Fix html with images
        fix_html(soup)
    
    # Print headers
    elif command == 'HEAD':
        # Get response from server
        response = receive_response()

        print(response.decode('utf-8'))

    # Close connection
    # TODO: send 'Connection: close' header to server
    client.close()

main()