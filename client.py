import socket
import re
from bs4 import BeautifulSoup

HTTP_COMMANDS = ('HEAD', 'GET', 'PUT', 'POST') # Possible HTTP commands for this implementation


# Get URI (e.g. http://www.google.com)
uri = input('URI (press enter for www.google.com): ')

# Parse URI (e.g. www.google.com)
if uri.startswith('http://'):
    uri = uri[len('http://'):]

# Use www.google.com as default URI
if not uri:
    uri = 'www.google.com'


# Get port
port = input('Port (press enter to use default): ')

# Use default port if no port specified
if not port:
    port = 80

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Create TCP socket with ipv4

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
    open('received.html', 'w').close() # Remove contents of html file
    file = open('received.html', 'w')
    file.write(html.prettify())
    file.close()

def request_img(url):
    """Request the image from the server and store it locally in the same relative path.
    External urls should just be downloaded in a folder, but are not used.

    Args:
        url (string): url/path of the image
    """
    ## Local images (GET to current server)
    if url.startswith('/'):
        msg = make_GET(url)
        client.send(msg.encode())
        resp = receive_response()
        # TODO: continue


    ## External images (open other socket to external server)


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

    Returns:
        string: fixed HTML body
    """

    imgs = html.findAll('img')

    for img in imgs:
        request_img(img['src'])


    return html

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

def main():
    # Get HTTP command
    command = input('HTTP command: ')

    do_command(command)

    # Get response from server
    response = receive_response()

    # Store HTML body in file
    if command == 'GET':
        # Get HTML body
        body = get_html_body(response)

        # Prettify body
        soup = BeautifulSoup(body, 'html.parser')

        # Store body
        store_html(soup)

        # # Fix html with images
        # fix_html(soup)
    
    elif command == 'HEAD':
        print(response.decode('utf-8'))

    # Close connection
    # TODO: send 'Connection: close' header to server
    client.close()

main()