import sys
import time
import zmq
import json
from task_categorizer import TaskCategorization
import signal
from datetime import datetime


class CategoryWorker:
    def __init__(self, host="localhost", port=8889):
        self._context = zmq.Context()
        # self._pull_socket = self._context.socket(zmq.PULL)
        # self._pull_socket.connect(f"tcp:{host}:{port}")
        #
        # self._rep_socket = self._context.socket(zmq.PUSH)
        # self._rep_socket.connect(f"tcp:{host}:{port+1}")  # 8890
        self._deal_socket = self._context.socket(zmq.DEALER)
        self._deal_socket.connect(f"tcp://{host}:{port}")
        print(f"Worker created and connected to dealersocket {self._deal_socket}")

        self._poller = zmq.Poller()
        self._poller.register(self._deal_socket, zmq.POLLIN)

        # self._rep_socket = self._context.socket(zmq.REP)
        # self._rep_socket.connect(f"tcp://{host}:{port + 1}")  # 8890
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGTERM, self.close)

    def process_tasks(self):
        while True:
            sockets = dict(self._poller.poll())

            if sockets.get(self._deal_socket) == zmq.POLLIN:
                message = self._deal_socket.recv_multipart()  # {task_id:, task:}
                print(f"Worker {self} received message: {message} {datetime.now()}")
                client_id = message[0]
                tasks = message[1]
                task = json.loads(tasks.decode('utf-8'))

                response = self.get_category(task)

                print(f"about to send:{response} {datetime.now()}")
                json_response = json.dumps(response).encode()
                # sends message to main server
                self._deal_socket.send_multipart([client_id, json_response])
                # print(f"received message: {task}")
                #
                # # add categorization
                # categorizer = TaskCategorization(task["task_id"], task["task"])
                # category = categorizer.get_category()
                #
                # # creates message
                # result = {
                #     "task_id": task['task_id'],
                #     "task": task['task'],
                #     "category": category
                # }
                # print(f"about to send:{result}")
                #
                # # sends message to main server
                # self._rep_socket.send_json(result)

    def get_category(self, task):
        # add categorization
        categorizer = TaskCategorization(task["task_id"], task["task"])
        category = categorizer.get_category()

        # creates message
        result = {
            "task_id": task['task_id'],
            "task": task['task'],
            "category": category
        }
        return result


    def close(self, signalnum, frame):
        self._rep_socket.close()
        self._deal_socket.close()
        self._context.term()
        print("Workers closed")


