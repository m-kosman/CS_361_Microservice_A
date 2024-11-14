# Program requires ZeroMQ, SQLAlchemy, SQLite/PySQLite, NLTK

# Program comes with a json file full of starter keywords to use for categorization.  The 
# database is a local persistent SQL database. 

# Prior to running, you must first set up the database.  To do this, run task_category_db.py 
# and the database should be prefilled with the categories and keywords. 

# This program uses a request reply broker model for communication.  

# The client should use a REQ socket to connect to the server's ROUTER socket.  The server 
# also has a DEALER socket which connects to the worker's DEALER socket.  

# Client should use send/recv_json to send the messages, however, the recv_json should have 
# the zmq.NOBLOCK flag set to prevent blocking.  

# To communicate with the microservice both zeromq_server and category_worker must be
# running in separate terminals.  