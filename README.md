This is the first assignment for the course Computer Networks 2020-2021 about HTTP.

# Run code
Activate the virtual environment: `source venv/bin/activate`
## Start client
1. Start program: `python3 client.py {HTTP command} {URI} {Port}`  
    HTTP command: HEAD, GET, PUT or POST; URI: url or ipv4 address; Port: default 80, own server 5050
2.  - For HEAD: enter the path of the file you want to request (default: /),
    response will be printed to the terminal
    - For GET: enter the path of the file you want to request (default: /),
    response will be placed inside 'received.html', which can be viewed in a browser
    - For PUT: enter the path where you want your input to be stored (default: /) and enter the input itself, 
    response will be stored in 'received.html'
    - For POST: enter the path where you want your input to be stored (default: /) and enter the input itself,
    response will be stored in 'received.html'

## Start server on own ipv4 adress
`python3 server.py`  
The content of POST and PUT requests will be placed inside the 'server_text_files'-folder