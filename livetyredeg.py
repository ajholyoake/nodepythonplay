"""General layout:
    we have an rtap server working in another process which must be started manually
    we have an rtap client lib which has a thread with loops the socket recv thing, and calls a callback (on that thread). The callback should just append the timing data to a datastructure.

    The datastructure should be processing on another thread, i.e. doing the deg calculations etc. This should happen with a minimum time interval, and on events such as sending valid laps information back from the browser (which should alter immediately) or on new laps (i.e. every 10 seconds)

We then emit this data out on websockets to the browser for display using d3
"""

from flask import Flask
from flask.ext.socketio import SocketIO,emit

app = Flask(__name__,static_url_path='',static_folder='front_end')
app.config['SECRET_KEY']='staplesandhorsesandthat'
app.config['Debug'] = True
app.debug = True
socketio=SocketIO(app)


"""Processing Section"""

from rtapclientlib import RTAPClient as client
from threading import Thread
from Queue import Queue
from collections import defaultdict

"""Processing Queue"""
q = Queue() 
num_worker_threads = 3

data = defaultdict(lambda:[])

class Lap:
    def __init__(self,**kwargs):
        self.car = kwargs['car']
        self.lap_time = kwargs['lap_time']
        self.session_time = kwargs['session_time']
        self.lap_number = kwargs['lap_number']
        self.index = kwargs['index']
        self.included = True
        self.tyre_age = self.lap_number
        self.degradation = 0

def process_degradation(item):
    ccar = data[item['car']]
    ccar.append(Lap(**item))
    """Exclude slow laps in here and calc deg"""
    mintime = min([l.lap_time for l in ccar])
    for lap in ccar:
        lap.degradation = lap.lap_time - mintime


def worker():
    while True:
        item = q.get()
        #process_degradation(item)
        emit('my response',item)
        q.task_done()



def callback(data):
    q.put(data)
    socketio.emit('my response',data)

"""Block until tasks are done"""
#q.join()

c = client()
c.subscribe()
c.onMessage(callback)

"""Web Server Section"""



@app.route('/')
def index():
    return app.send_static_file('index.html')

@socketio.on('my event')
def test_message(message):
    emit('my response',{'data':message['data']})

@socketio.on('my broadcast event')
def test_message(message):
    emit('my response', {'data': message['data']}, broadcast=True)

@socketio.on('connect')
def test_connect():
    emit('my response', {'data': 'Connected'})

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')


if __name__ == '__main__':
    socketio.run(app)



