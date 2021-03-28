This is the first assignment for the course Computer Networks 2020-2021 about HTTP.

# Run code
## Start client
`python3 client.py {HTTP command} {URI} {Port}`  
HTTP command: HEAD, GET, PUT or POST; URI: url or ipv4 address; Port: default 80, own server 5050  
The response can be viewed in 'received.html'

## Start server on own ipv4 adress
`python3 server.py`  
The content of POST and PUT requests will be placed inside the 'server_text_files'-folder