import zmq

import sys
import zmq
import json

port = "2377"

# Socket to talk to server
context = zmq.Context()
socket = context.socket(zmq.SUB)

socket.connect("tcp://localhost:{port}".format(port=port))
socket.setsockopt(zmq.SUBSCRIBE,"FOM")

while True:
    string = socket.recv()
    msgtype, obj = string.split(' ',1)
    obj = json.loads(obj)
    print str(obj)
    sys.stdout.flush()
    if "finished" in obj.keys():
        break;
