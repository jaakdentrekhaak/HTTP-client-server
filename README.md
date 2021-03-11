This is the first assignment for the course Computer Networks 2020-2021 about HTTP.

# Run code
Activate the virtual environment: `source venv/bin/activate`
## Send requests to websites with client
1. Start program: `python3 client.py`
2. Fill in URI (or fill in a number for the default options)  
3. Fill in the port (or press enter to use default port 80)  
4. Choose the HTTP command
5.  - For HEAD: response will be printed to the terminal
    - For GET: response will be placed inside 'received.html', which can be viewed in a browser
    - For PUT: the current content of 'received.html' will be sent to the server at /new.html, 
    response will be stored in 'received.html'
    - For POST: type in terminal the info you want to send to the server (will be sent to root /),
    response will be stored in 'received.html'