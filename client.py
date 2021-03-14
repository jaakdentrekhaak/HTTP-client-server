import socket
from bs4 import BeautifulSoup
import os
from pathlib import Path


HTTP_COMMANDS = ('HEAD', 'GET', 'PUT', 'POST') # Possible HTTP commands for this implementation


# Get URI (e.g. http://www.google.com)
uri = input('URI: 1. example, 2. google, 3. tcpipguide, 4. jmarshall, 5. tldp, 6. tinyos, 7. linux-ip: ') or 'www.example.com'

# If number is entered -> map to website
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
port = input('Port (press enter to use default 80): ') or 80
port = int(port)

# Create TCP socket with ipv4
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect to server
if uri.startswith('192'): # possible that user wants to connect to given ipv4 adress
        server = uri
else:
    try:
        server = socket.gethostbyname(uri)
    except socket.gaierror:  
        # this means could not resolve the host  
        print ('There was an error resolving the host') 
        exit()
client.connect((server, port))

def create_get_message(path):
    """Generate GET message with given path

    Args:
        path (string): path to request

    Returns:
        string: GET message
    """
    msg = f'GET {path} HTTP/1.1\r\n'
    msg += f'Host: {uri}\r\n'
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
        msg += f'Host: {uri}\r\n'
        msg += '\r\n'
    elif cmd == 'GET':
        msg = create_get_message('/')
    elif cmd == 'PUT':
        file = open('received.html', 'r')
        html = file.read()
        msg = 'PUT /new.html HTTP/1.1\r\n' # Just the name for our file to create on the server
        msg += f'Host: {uri}\r\n'
        msg += 'Content-Type: text/html\r\n'
        msg += f'Content-Length: {len(html)}\r\n'
        msg += '\r\n'
        msg += html + '\r\n'
        msg += '\r\n'
    elif cmd == 'POST':
        post_text = input('POST text: ')
        msg = 'POST / HTTP/1.1\r\n'
        msg += f'Host: {uri}\r\n'
        msg += 'Content-Type: text/html\r\n'
        msg += f'Content-Length: {len(post_text)}\r\n'
        msg += '\r\n'
        msg += post_text + '\r\n'
        msg += '\r\n'

    client.send(msg.encode()) # Encode with default utf-8

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
    """Store image response from server in the local images folder

    Args:
        img (bytes): image response from server
        path (string): path of the image that needs to be stored
    """

    file = open('images/' + path.split('/')[-1], 'wb')
    file.write(img)
    file.close()

def get_external_image(website, path):
    """Open new socket to website, send GET for external image and return server response with image

    Args:
        website (string): name of the website
        path (string): relative path of the external image

    Returns:
        bytes: requested image
    """
    cl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sv = socket.gethostbyname(website)
    cl.connect((sv, 80))
    cl.send(create_get_message(path).encode())
    resp = handle_response()
    cl.close()
    return resp

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
        msg = create_get_message(url)
        client.send(msg.encode())
        resp = handle_response()
        store_img(resp, url)

    ## External images (open other socket to external server)
    else:
        # E.g. https://ssl.gstatic.com/gb/images/b_8d5afc09.png
        split_url = url.split('/')
        website = split_url[2]
        img_path = '/' + '/'.join(split_url[3:])
        store_img(get_external_image(website, img_path), img_path)

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
        # Change src to local images folder (e.g. images/yeet.png)
        image_name = img['src'].split('/')[-1] # Grab image name from path
        img['src'] = 'images/' + image_name
    
    # Save HTML in which we changed the src of the images to our local images folder
    store_html(html)

def get_content_length(head):
    """Return Content-Length of response

    Args:
        head (bytes): headers of HTTP response

    Returns:
        int: length of the body of the HTTP response
    """
    keyword = b'Content-Length:'
    _, keyword, after_keyword = head.partition(keyword)

    # after_keyword now contains something like 1562\r\n..., so we only need the part before \r\n
    ind = after_keyword.index(b'\r')
    return int(after_keyword[:ind])

def get_next_chunk():
    """Read the size of the chunk and receive body of chunk

    Returns:
        bytes: body of the chunk
    """
    # Get bytes of chunk (first bytes sent in chunk), ends with '\r\n'
    chunk_bytes = b''
    while not (chunk_bytes.endswith(b'\r\n')):
        chunk_bytes += client.recv(1)

    chunk_bytes = chunk_bytes[:-2] # Cut off '\r\n'
    chunk_bytes = int(chunk_bytes, 16) # From hexadecimal to decimal

    # If chunk_bytes == 0, we reached the last chunk
    body = b''
    if chunk_bytes != 0:
        # Receive body of chunk
        # NOTE: To make the next call of this function more easy: already read in last '\r\n', otherwise the while loop above will end if '\r\n' is read
        actual_length = chunk_bytes + len(b'\r\n')
        while len(body) != actual_length:
            body += client.recv(actual_length - len(body)) # We can still receive the difference between the actual length of the response and the current length
    
    return body

def get_headers():
    """Extract the headers from the HTTP server response

    Returns:
        bytes: headers from response
    """
    headers = b''

    # The headers always end with b'\r\n\r\n'
    while not headers.endswith(b'\r\n\r\n'):
        response = client.recv(1)
        headers += response
    
    return headers

def handle_response():
    """Receive HTTP response from server and return response body

    Returns:
        bytes: HTTP response body
    """
    
    # First get headers: read byte per byte until we have the headers
    headers = get_headers()
    
    # See if we need to use content-length or transfer-encoding
    if b'Content-Length' in headers:
        body = b''
        content_length = get_content_length(headers)
        # NOTE: we can't just do client.recv(content_length), because the buffersize in recv(bufsize) is a maximum
        #   so client.recv() can return less bytes than the given buffer size
        buff_size = 1024
        # Loop as long as the received body is not the same length as given by Content-Length
        while len(body) != content_length:
            body += client.recv(buff_size)
    else:
        body = b''
        chunk = get_next_chunk()
        while len(chunk) != 0:
            body += chunk
            chunk = get_next_chunk()
    
    return body

def main():
    # Get HTTP command
    command = input('HTTP command: ')

    do_command(command)


    # Store HTML body in file
    if command == 'GET' or command == 'POST' or command == 'PUT':
        # Get HTML body
        body = handle_response()

        # Prettify body
        soup = BeautifulSoup(body, 'html.parser')

        # Fix html with images
        fix_html(soup)
    
    # Print headers
    elif command == 'HEAD':
        # Get response from server
        response = get_headers()

        print(response.decode('utf-8')) # Decoding for readability in terminal

    # Close connection
    # TODO (optional): send 'Connection: close' header to server
    client.close()

main()