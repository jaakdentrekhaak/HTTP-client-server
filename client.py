import socket
from bs4 import BeautifulSoup
import sys

# Example websites
# 
# www.example.com
# www.google.com
# www.tcpipguide.com
# www.jmarshall.com
# www.tldp.org
# www.tinyos.net
# www.linux-ip.net

# IF_MODIFIED_SINCE = 'If-Modified-Since: Sun, 04 Apr 2021 17:10:27 GMT\r\n' # Date in the future -> not modified
IF_MODIFIED_SINCE = ''

def create_get_message(url, path):
    """Generate GET message with given path

    Args:
        url (string): url of server
        path (string): path to request

    Returns:
        string: GET message
    """
    msg = f'GET {path} HTTP/1.1\r\n'
    msg += f'Host: {url}\r\n'
    msg += IF_MODIFIED_SINCE
    msg += '\r\n'

    return msg

def do_command(client, cmd, url, path):
    """Send HTTP request to the server depending on the type of command

    Args:
        client (object): socket
        cmd (string): One of the possible HTTP commands
        url (string): url of server
        path (string): path to requested file
    """
    # Possible HTTP commands for this implementation
    if cmd not in ('HEAD', 'GET', 'PUT', 'POST'):
        print('[ERROR] Command not recognized')
        exit()

    if cmd == 'HEAD':
        msg = f'HEAD {path} HTTP/1.1\r\n'
        msg += f'Host: {url}\r\n'
        msg += IF_MODIFIED_SINCE
        msg += '\r\n'
    elif cmd == 'GET':
        msg = create_get_message(url, path)
    elif cmd == 'PUT' or cmd == 'POST':
        text = input('Enter text you want to send to the server: ')
        msg = f'{cmd} {path} HTTP/1.1\r\n'
        msg += f'Host: {url}\r\n'
        msg += 'Content-Type: text/html\r\n'
        length = len(text) + len(b'\r\n\r\n')
        msg += f'Content-Length: {length}\r\n'
        msg += '\r\n'
        msg += text + '\r\n'
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
        website (string): name of external server
        path (string): relative path of the external image

    Returns:
        bytes: requested image
    """
    cl = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sv = socket.gethostbyname(website)
    cl.connect((sv, 80))
    cl.send(create_get_message(website, path).encode())
    headers = get_headers(cl)
    resp = handle_response(cl, headers)
    cl.close()
    return resp

def request_img(client, uri, url):
    """Request the image from the server and store it locally in the same relative path.
    External urls should just be downloaded in a folder, but are not used.

    Args:
        client (object): socket
        uri (string): url/path of the image
        url (string): url of server connected to
    """
    ## Local images (GET to current server)
    if not uri.startswith('http'):
        if not uri.startswith('/'):
            uri = '/' + uri 
        print('[IMG REQUEST]', uri)
        msg = create_get_message(url, uri)
        client.send(msg.encode())
        headers = get_headers(client)
        resp = handle_response(client, headers)
        store_img(resp, uri)

    ## External images (open other socket to external server)
    else:
        print('[EXT IMG REQUEST]', url, uri)
        # E.g. http://www.tinyos.net/tos-jwall.jpg
        split_uri = uri.split('/')
        website = split_uri[2]
        img_path = '/' + '/'.join(split_uri[3:])
        store_img(get_external_image(website, img_path), img_path)

def fix_html(client, html, url):
    """Find missing images in the given html, request them from the server and
    store them locally.

    Images can be stored locally:
        e.g. /images/nav_logo229.png
    or loaded from external website:
        e.g. https://ssl.gstatic.com/gb/images/b_8d5afc09.png
    
    Images will be stored in <img ... src="">

    Args:
        client (object): socket
        html (BeautifulSoup): HTML body
        url (string): url of connected server
    """

    imgs = html.findAll('img')

    for img in imgs:
        request_img(client, img['src'], url)
        # Change src to local images folder (e.g. images/yeet.png)
        image_name = img['src'].split('/')[-1] # Grab image name from path
        img['src'] = 'images/' + image_name
    
    # Save HTML in which we changed the src of the images to our local images folder
    store_html(html)

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

def get_next_chunk(client):
    """Read the size of the chunk and receive body of chunk

    Args:
        client (object): socket

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

def get_headers(client):
    """Extract the headers from the HTTP server response

    Args:
        client (object): socket

    Returns:
        bytes: headers from response
    """
    headers = b''

    # The headers always end with b'\r\n\r\n'
    while not headers.endswith(b'\r\n\r\n'):
        response = client.recv(1)
        headers += response
    
    return headers

def handle_response(client, headers):
    """Receive HTTP response from server and return response body

    Args:
        client (object): socket
        headers (bytes): headers of the HTTP response

    Returns:
        bytes: HTTP response body
    """
    
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
        chunk = get_next_chunk(client)
        while len(chunk) != 0:
            body += chunk
            chunk = get_next_chunk(client)

    return body

def main(command, uri, port):
    """Run the code

    Args:
        command (string): HTTP command
        uri (string): path to file on server
        port (string): port to connect to
    """

    # Parse URI (e.g. www.google.com)
    if uri.startswith('http://'):
        uri = uri[len('http://'):]

    # Get url of given uri and the path of the file
    url = uri.split('/')[0]
    path = '/'.join(uri.split('/')[1:]) or '/' # Default is /

    port = int(port)

    # Create TCP socket with ipv4
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to server
    if url == 'localhost':
        print('[ERROR] Connect to your own server with your ipv4 address.')
        exit()
    elif url.startswith('192'): # possible that user wants to connect to given ipv4 adress
            server = url
    else:
        try:
            server = socket.gethostbyname(url)
        except socket.gaierror:  
            # this means could not resolve the host  
            print ('[ERROR] There was an error resolving the host') 
            exit()
    client.connect((server, port))

    # Execute command
    do_command(client, command, url, path)

    # Get header from response
    headers = get_headers(client)

    # If not 200 OK in headers -> show headers in terminal
    if b'200 OK' not in headers:
        print(headers.decode('utf-8'))

    # If 304 Not Modified in response: don't receive the body

    # Store HTML body in file
    if b'304 Not Modified' not in headers and (command == 'GET' or command == 'POST' or command == 'PUT'):
        # If you are requesting an image, this image gets saved inside the images-folder
        if command == 'GET' and (path.endswith('.jpg') or path.endswith('.png')):
            request_img(client, path, url)
            print('[SUCCESS] The requested image can be found in the images-folder')
        else:
            # Get HTML body
            body = handle_response(client, headers)

            # Prettify body
            soup = BeautifulSoup(body, 'lxml')

            # Fix html with images
            fix_html(client, soup, url)

            print('[SUCCESS] Request succeeded, the response can be viewed in received.html')
    
    # Print headers
    elif b'304 Not Modified' not in headers and command == 'HEAD':
        print(headers.decode('utf-8')) # Decoding for readability in terminal

    # Close connection
    client.send(f'HEAD / HTTP/1.1\r\nHost: {url}\r\nConnection: close\r\n\r\n'.encode())
    headers = get_headers(client)
    if b'Connection: close' in headers:
        print('[CLOSE] Client successfully closed.')
        client.close()
    else:
        print('[FORCE CLOSE] Client closed because no \'Connection: close\'-header was received from the server.')
        client.close()

if __name__ == '__main__':
    # Check input arguments
    if len(sys.argv) != 4:
        print('[ERROR] Input arguments must be: client.py; HTTP command; URI; Port')
        exit()
    command, uri, port = sys.argv[1:]
    main(command, uri, port)
