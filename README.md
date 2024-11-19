# Task Categorizer Microservice. 
This repository implements a Task Catetgorizer microservice using ZeroMQ as the communication pipe.  The microservice analyzes a task and compares it to a 
database of keywords and assigns it to one of 7 categories: Home, Work, School, Finance, Shopping, Health/Fitness, and Personal.  The personal category 
operates as a catch-all if no other category is a good fit.  The program also receives user feedback and adds the task and corrected category to the database to 
improve future requests.  

## Requirements
- ZeroMQ
- SQLAlchemy
- SQLite/PySQLite
- ContextLib library
- enum Library
- JSON library
- Signal library
- String library
- NLTK
- NLTK downloads for stopword, punkt, punkt_tab and wordnet

## Setup 
### 1. Database Initialization
The microservice uses a local persistent SQL database and comes with a JSON file (starter_tasks.json) to pre-populate the database.  The database must be initialized before use.  To create the database, run task_category_db.py on its own to set up the database.  
### 2.  Running the Server
The microservice has a server and a worker.  The server's DEALER socket hands out individual tasks to the worker who handles categorization.  To run the microservice, both zeromq_server.py and category_worker.py must be running.   
### 3.  Making Requests
The microservice uses a request-reply broker model for communication.  Clients should use a REQ socket to connect to the server's ROUTER socket.  The ROUTER is listening at Host: Local Host, Port: 8888.  

The server's ROUTER socket will receive a multipart message; however, clients should use send_json() to communicate with the server.  

## Sample Requests
To request data the client must: 
```
1. Connect to the server
2. Send either a feedback or request message to the server in JSON format
```
To receive data the client must: 
```
1. Receive the JSON message from the server
2. For requests, parse the JSON to get the task's category 
```
### Categorization Request
Categorization requests should be made in the following format: 
```
import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:8888")
message = {"message type": "request",
           "tasks": [
               {"task_id": "1", "task": "Clean the living room"},
               {"task_id": "2", "task": "Write a report for work"}
           ]
           }
socket.send_json(message)
while True:
    try:
        response = socket.recv_json(flags=zmq.NOBLOCK)
        break
    except zmq.Again:
        time.sleep(.1)
    except zmq.ZMQError as e:
        print(f"Error receiving message: {e}")
```
### Feedback Request 
Feedback requests should be made in the following format: 
```
import zmq
import time

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:8888")
message = {"message type": "feedback",
           "feedback":
               {'task_id': '43',
                'task': 'Update social media profiles',
                'category_provided': 'school',
                "category_feedback": "personal"
               }
           }
socket.send_json(message)
while True:
    try:
        response = socket.recv_json(flags=zmq.NOBLOCK)
        break
    except zmq.Again:
        time.sleep(.1)
    except zmq.ZMQError as e:
        print(f"Error receiving message: {e}")
```
Tasks may be in mixed case, but the categories should be lowercase.  
 
## Sample Response
### Request
```
{"message type": "response",
                 "tasks": [
                          {"task_id": "1", "task": "Clean the living room", "category": "home"},
                          {"task_id": "2", "task": "Write a report for work", "category": "work"}
                         ]
           }
```
### Feedback 
```
{"message type": "response",
"message": f"Received feedback for task: {task}.  Category should be {new_category} "
           f"instead of {original_category}."
}
```
# Notes
- To prevent blocking, the recv_json method should have its flags set to zmq.NOBLOCK. 
- Task IDs should be strings
- If you want to add more keywords, you can either use a SQL query or send a feedback request.

# UML Diagram
![UML diagram.png](https://github.com/m-kosman/CS_361_Microservice_A/blob/master/UML%20diagram.png))
