import time
import zmq
import json



class CategoryServer:
    def __init__(self, host="localhost", port=8888):
        self._context = zmq.Context()
        # for connection with client program
        self._socket = self._context.socket(zmq.REP)
        self._socket.bind(f"tcp://{host}:{port}")

        # for communicating with workers
        self._push_socket = self._context.socket(zmq.PUSH)
        self._push_socket.bind(f"tcp://{host}:{port+1}")  # 8889

        self._pull_socket = self._context.socket(zmq.PULL)
        self._pull_socket.bind(f"tcp://{host}:{port+2}")  # 8890

    def process_requests(self):
        while True:
            # receives request from client program
            message = self._socket.recv_json()
            print(f"Received request: {message}")

            if "message type" == "request":
                # send tasks to be categorized
                response = {
                    "message type": "response",
                    "tasks": []
                }
                # sends tasks to workers
                for task in message["tasks"]:
                    self._push_socket.send_json(task)

                # collects responses from workers
                for _ in message["tasks"]:
                    new_task = self._pull_socket.recv_json()
                    response["tasks"].append(new_task)
                pass

            if "message type" == "feedback":
                # process feedback
                task = message['feedback']['task']
                orig_category = message['feedback']['category_provided']
                new_category = message['feedback']['category_feedback']

                response = {"message type": "response",
                            "message": f"Received feedback for task: {task}.  Category should be {new_category} "
                                       f"instead of {orig_category}."
                            }

                self._socket.send_json(response)

    def close(self):
        self._socket.close()
        self._push_socket.close()
        self._pull_socket.close()
        self._context.term()