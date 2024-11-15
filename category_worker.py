import zmq
import json
from task_categorizer import TaskCategorization
import signal
from datetime import datetime


class CategoryWorker:
    """Represents a worker who categorizes tasks"""
    def __init__(self, host="localhost", port=8889):
        self._context = zmq.Context()

        self._deal_socket = self._context.socket(zmq.DEALER)
        self._deal_socket.connect(f"tcp://{host}:{port}")
        print(f"Worker created and connected to dealersocket {self._deal_socket}")

        self._poller = zmq.Poller()
        self._poller.register(self._deal_socket, zmq.POLLIN)

        # for handling socket close
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGTERM, self.close)

    def process_tasks(self):
        """
        Handles the main event loop for listening for tasks calling the task categorizer and
        returning a category.
        """
        while True:
            sockets = dict(self._poller.poll())

            # checks for a message, processes it and returns the category
            if sockets.get(self._deal_socket) == zmq.POLLIN:
                # receives and unpacks the message
                message = self._deal_socket.recv_multipart()  # {task_id:, task:}
                print(f"Worker {self} received message: {message} {datetime.now()}")
                client_id = message[0]
                tasks = message[1]
                task = json.loads(tasks.decode('utf-8'))

                # gets the response to send
                response = self.get_category(task)

                # sends message to main server
                print(f"about to send:{response} {datetime.now()}")
                json_response = json.dumps(response).encode()
                self._deal_socket.send_multipart([client_id, json_response])

    def get_category(self, task:dict) -> dict:
        """
        Calls the task categorizer and creates the response message to
        send to server.
        :param task: a dictionary of the task w/ id and task
        :return: A dictionary with the task and category
        """
        # gets the categorization
        categorizer = TaskCategorization(task["task_id"], task["task"])
        category = categorizer.get_category()

        # creates message w/ new c ategory
        result = {
            "task_id": task['task_id'],
            "task": task['task'],
            "category": category
        }
        return result

    def close(self, signalnum, frame):
        """Handles closing a socket"""
        self._deal_socket.close()
        self._context.term()
        print("Workers closed")


if __name__ == "__main__":
    worker = CategoryWorker(host="localhost", port=8889)
    worker.process_tasks()