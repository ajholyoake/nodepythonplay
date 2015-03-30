import zmq

import sys
import zmq
import json

import threading


class RTAPClient:

  def __init__(self,server='localhost',port='2377'):
    # Socket to talk to server
    self.server = server
    self.port = port

  def subscribe(self,type=['FOM']):

      self.context = zmq.Context()
      self.socket = self.context.socket(zmq.SUB)

      self.socket.connect("tcp://localhost:{port}".format(port=self.port))
      self.socket.setsockopt(zmq.SUBSCRIBE,' '.join(type))

  def onMessage(self,cb):
      threading.Thread(target=self._onMessage,args=[cb]).start()

  def _onMessage(self,cb):
      while True:
          string = self.socket.recv()
          msgtype, obj = string.split(' ',1)
          obj = json.loads(obj)
          print str(obj)
          sys.stdout.flush()
          cb(obj)
          if "finished" in obj.keys():
              break;
