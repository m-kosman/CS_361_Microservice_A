import time
import zmq
import json
from task_categorizer import *


class CategoryWorker:
    def __init__(self, host="localhost", port=8889):
        self._context = zmq.Context()
        self._pull_socket = self._context.socket(zmq.PULL)
        self._pull_socket.connect(f"tcp:{host}:{port}")

        self._push_socket = self._context.socket(zmq.PUSH)
        self._push_socket.connect(f"tcp:{host}:{port+1}")  # 8890

    def process_tasks(self):
        while True:
            tasks = self._pull_socket.recv_json()

            # add categorization
            category = 'home'  # placeholder for category

            # creates message
            result = {
                "task_id": tasks['task_id'],
                "task": tasks['task'],
                "category": category
            }

            # sends message to main server
            self._push_socket.send_json(result)

    def close(self):
        self._push_socket.close()
        self._pull_socket.close()
        self._context.term()