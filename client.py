import socket


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


def do_command(cmd):
    if cmd not in HTTP_COMMANDS:
        print('[INVALID COMMAND] Command not recognized')
        exit()

    if cmd == 'HEAD':
        msg = 'HEAD / HTTP/1.1\r\n'
        msg += f'Host:{uri}\r\n'
        msg += '\r\n'
    elif cmd == 'GET':
        msg = 'GET / HTTP/1.1\r\n'
        msg += f'Host:{uri}\r\n'
        msg += '\r\n'
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

    client.send(msg.encode())


while True:
    # Get HTTP command
    command = input('HTTP command: ')
    
    do_command(command)

    # Get response from server
    response = b''
    while True:
        received = client.recv(1024)
        response += received
        if received.endswith('\r\n\r\n'.encode('utf-8')):
            break
    
    response = response.decode('ISO-8859-1') # TODO: get encoding with 'charset' in content-length header

    # Store HTML body in file
    # TODO: download images in html file
    if command == 'GET':
        # Get HTML body
        start = response.index('<!doctype html>')
        end = response.index('</html>') + len('</html>')
        body = response[start:end]
        
        # Store HTML body
        file = open('received.html', 'w').close() # Remove contents of html file
        file = open('received.html', 'w')
        file.write(body)
        file.close()

