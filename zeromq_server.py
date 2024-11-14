import time
from datetime import datetime
import zmq
import json
import signal
import sys
from task_category_db import TaskCategoryDatabase

class CategoryServer:
    def __init__(self, host="localhost", port=8888):
        self._database = TaskCategoryDatabase()
        self._context = zmq.Context()
        # for connection with client program
        # self._socket = self._context.socket(zmq.REP)
        # self._socket.bind(f"tcp://{host}:{port}")
        self._frontend = self._context.socket(zmq.ROUTER)
        self._frontend.bind(f"tcp://{host}:{port}")

        # for communicating with workers
        # self._rep_socket = self._context.socket(zmq.PUSH)
        # self._rep_socket.bind(f"tcp://{host}:{port+1}")  # 8889
        self._backend = self._context.socket(zmq.DEALER)
        self._backend.bind(f"tcp://{host}:{port + 1}")  # 8889

        # self._rep_socket = self._context.socket(zmq.REP)
        # self._rep_socket.bind(f"tcp://{host}:{port+2}")  # 8890
        # self._pull_socket = self._context.socket(zmq.PULL)
        # self._pull_socket.bind(f"tcp://{host}:{port+2}")  # 8890
        signal.signal(signal.SIGINT, self.close)
        signal.signal(signal.SIGTERM, self.close)

        self._poller = zmq.Poller()
        self._poller.register(self._frontend, zmq.POLLIN)
        self._poller.register(self._backend, zmq.POLLIN)

    def process_requests(self):
        while True:
            sockets = dict(self._poller.poll())

            if sockets.get(self._frontend) == zmq.POLLIN:
                message = self._frontend.recv_multipart()
                print(f"sending message: {message}")
                client_id, message, request = self.partition_message(message)

                if request:
                    num_tasks = len(message["tasks"])
                    self.distribute_tasks(client_id, message)
                    response = self.get_responses(num_tasks)
                    print(response)
                    multipart_msg = [client_id, b'', json.dumps(response).encode()]
                    print(f"sending response: {multipart_msg} ")
                    self._frontend.send_multipart(multipart_msg)
                else:
                    response = self.process_feedback(message)
                    if response:
                        multipart_msg = [client_id, b'', json.dumps(response).encode()]
                        self._frontend.send_multipart(multipart_msg)


            # try:
            #     # receives request from client program
            #     multipart_message = self._frontend.recv_multipart()
            #     print(multipart_message)
            #     message = multipart_message[2]
            #     client_id = multipart_message[0]   # 1 is empty byte string
            #     # message = self._socket.recv_json()
            #
            #     try:
            #         message_str = message.decode("utf-8")
            #         print(f"Received request: {message}")
            #         message_dict = json.loads(message)
            #     except json.JSONDecodeError as e:
            #         print(f"Error decoding JSON: {e}")
            #         continue
            #     try:
            #         if request:
                        # send tasks to be categorized
                        # response = {
                        #     "message type": "response",
                        #     "tasks": []
                        # }
                        # num_tasks = len(message["tasks"])
                        # # sends tasks to workers
                        # for task in message["tasks"]:
                        #     try:
                        #         print(f"Sending: {task}")
                        #         serialized_task = json.dumps(task).encode('utf-8')
                        #         multipart_message = [client_id, serialized_task]
                        #         print(f"message to send: {multipart_message}")
                        #         self._backend.send_multipart(multipart_message)  # {task_id: , task: }
                        #     except Exception as e:
                        #         print(f"Error sending task: {e}")


                        # collects responses from workers
                        # for _ in range(num_tasks+1):
                        #     print("Collecting worker responses")
                        #     try:
                        #         if self._rep_socket in sockets:
                        #             new_task = self._rep_socket.recv_json()
                        #             print(f"Received response from worker:{new_task}")
                        #             response["tasks"].append(new_task)
                        #         else:
                        #             print("No response from worker within timeout")
                        #     except Exception as e:
                        #         print(f"Error receiving task: {e}")

                        # print(f"Sending: {response}")
                        # self._frontend.send_multipart([client_id, json.dumps(response).encode("utf-8")])

                #     else:
                #         # process feedback
                #         task = message['feedback']['task']
                #         orig_category = message['feedback']['category_provided']
                #         new_category = message['feedback']['category_feedback']
                #
                #         response = {"message type": "response",
                #                     "message": f"Received feedback for task: {task}.  Category should be {new_category} "
                #                                f"instead of {orig_category}."
                #                     }
                #
                #         self._frontend.send_json(response)
                # except zmq.Again as e:
                #     time.sleep(0.1)
                # except zmq.ZMQError as error:
                #     print(f"Error while receiving message: {error}")
                #     print(f"ZMQ Error Code: {error.errno}")
                #     print(f"ZMQ Error Message: {zmq.strerror(error.errno)}")
                #     break

    def partition_message(self, message):
        message_text = message[2].decode("utf-8")
        client_id = message[0]  # 1 is empty byte string

        print(f"Received request: {message}")
        message_dict = json.loads(message_text)

        request = message_dict.get("message type") == "request"

        return client_id, message_dict, request

    def distribute_tasks(self, client_id, message):
        del message["message type"]  # removes the message type
        tasks = message["tasks"]    # flattens remaining

        task_no = 0

        while task_no < len(tasks):
            json_task = json.dumps(tasks[task_no]).encode('utf-8')
            print(f"sending task {tasks[task_no]} to worker {datetime.now()}")
            self._backend.send_multipart([client_id, json_task])
            task_no += 1

    def get_responses(self, total):
        sockets = dict(self._poller.poll())
        response = {
            "message type": "response",
            "tasks": []
        }
        responses = 0

        while responses < total:
            if sockets.get(self._backend) == zmq.POLLIN:
                message = self._backend.recv_multipart()
                client_id = message[0]
                new_task = json.loads(message[1])
                print(f"Received response from worker: {new_task} {datetime.now()}")
                response["tasks"].append(new_task)
                responses += 1
        print(f"all responses received {datetime.now()}")
        return response


    def process_feedback(self, message):
        task = message['feedback']['task']
        orig_category = message['feedback']['category_provided']
        new_category = message['feedback']['category_feedback']

        response = {"message type": "response",
                        "message": f"Received feedback for task: {task}.  Category should be {new_category} "
                                   f"instead of {orig_category}."
                        }

        result = self._database.add_keyword_category(new_category, task)
        if result:
            return response
        return

    def close(self, signalnum, frame):
        self._frontend.close()
        self._backend.close()
        # self._rep_socket.close()
        self._context.term()
        print("Server Closed")


if __name__ == "__main__":
    server = CategoryServer()
    server.process_requests()