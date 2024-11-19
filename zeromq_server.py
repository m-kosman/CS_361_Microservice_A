from datetime import datetime
from typing import Union
import zmq
import json
import signal
from task_category_db import TaskCategoryDatabase


class CategoryServer:
    def __init__(self, host="localhost", port=8888):
        self._database = TaskCategoryDatabase()
        self._context = zmq.Context()

        # for connection with client program
        self._frontend = self._context.socket(zmq.ROUTER)
        self._frontend.bind(f"tcp://{host}:{port}")
        print(f"Server listening on {host}:{port}....")

        # for communicating with worker
        self._backend = self._context.socket(zmq.DEALER)
        self._backend.bind(f"tcp://{host}:{port + 1}")  # 8889
        print(f"Server listening on {host}:{port+1}....")

        # for closing sockets
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGTERM, self.close)

        # for checking for messages
        self._poller = zmq.Poller()
        self._poller.register(self._frontend, zmq.POLLIN)
        self._poller.register(self._backend, zmq.POLLIN)

    def process_requests(self):
        """
        Method handles the main event loop of the server.  It receives messages from
        the client and checks the type and handles the forwarding of the message depending
        on message t ype.
        """
        while True:
            # checks ot see if there is a message from the client
            sockets = dict(self._poller.poll())

            if sockets.get(self._frontend) == zmq.POLLIN:
                message = self._frontend.recv_multipart()
                print(f"Received message: {message}")
                client_id, message, request = self.partition_message(message)

                # if the message is a request type it sends them to the worker and once
                # it receives all responses it sends it to the client
                if request:
                    num_tasks = len(message["tasks"])
                    self.distribute_tasks(client_id, message)
                    response = self.get_responses(num_tasks)
                    multipart_msg = [client_id, b'', json.dumps(response).encode()]
                    print(f"Sending response: {multipart_msg} ")
                    self._frontend.send_multipart(multipart_msg)
                # if the message is a feedback type it adds it to the database and sends
                # response to client
                else:
                    response = self.process_feedback(message)
                    if response:
                        multipart_msg = [client_id, b'', json.dumps(response).encode()]
                        self._frontend.send_multipart(multipart_msg)

    def partition_message(self, message) -> tuple[bytes, dict, bool]:
        """
        Method receives a multipart message and breaks it into its component segments
        and also determines the message type.

        :param message: a multipart message consisting of byte strings
        :return: Tuple containing the client id, the decoded message and a boolean val for
        message type
        """
        # get component parts
        message_text = message[2].decode("utf-8")
        client_id = message[0]  # 1 is empty byte string

        # loads message
        message_dict = json.loads(message_text)

        # checks if its a request message
        request = message_dict.get("message type") == "request"

        return client_id, message_dict, request

    def distribute_tasks(self, client_id: bytes, message:dict):
        """
        Method receives a client id and message dictionary.  The dictionary has a list
        of tasks.  Method distributes each task to the worker one by one.

        :param client_id: A byte string of the client id
        :param message: A dictionary version of the client's message
        :return: None
        """
        del message["message type"]  # removes the message type
        tasks = message["tasks"]    # flattens remaining tasks

        task_no = 0

        # sends each task to the worker so 1 task == 1 message
        while task_no < len(tasks):
            json_task = json.dumps(tasks[task_no]).encode('utf-8')
            print(f"sending task {tasks[task_no]} to worker {datetime.now()}")
            self._backend.send_multipart([client_id, json_task])
            task_no += 1

    def get_responses(self, total: int) -> dict:
        """
        Gathers all the responses from the worker and adds it to the client response.

        :param total: the number of tasks that were sent
        :return: A dictionary containing the response to the client
        """
        # checks if responses are ready
        sockets = dict(self._poller.poll())
        response = {
            "message type": "response",
            "tasks": []
        }
        responses = 0

        # loops until it receives all responses
        while responses < total:
            # if a worker response is ready it gets it and adds it to the client response
            if sockets.get(self._backend) == zmq.POLLIN:
                message = self._backend.recv_multipart()
                new_task = json.loads(message[1])
                print(f"Received response from worker: {new_task} {datetime.now()}")
                response["tasks"].append(new_task)
                responses += 1
        print(f"all responses received {datetime.now()}")
        return response

    def process_feedback(self, message) -> Union[dict, None]:
        """
        Method receives a client message and adds the task to the correct category database
        to improve future performance and creates the response.

        :param message: the multipart message from client
        :return: A response in dictionary format or None if error adding to the database
        """
        task = message['feedback']['task']
        orig_category = message['feedback']['category_provided']
        new_category = message['feedback']['category_feedback']

        response = {"message type": "response",
                    "message": f"Received feedback for task: {task}.  Category should be {new_category} "
                               f"instead of {orig_category}."
                    }

        # calls database to add the keyword/category link
        result = self._database.add_keyword_category(new_category, task)
        if result:
            print(f"Sending response: {response}")
            return response
        return

    def close(self, signalnum, frame):
        """Handles closing of the socket """
        self._frontend.close()
        self._backend.close()
        self._context.term()
        print("Server Closed")


if __name__ == "__main__":
    server = CategoryServer()
    server.process_requests()