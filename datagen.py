
import asyncore
import socket
import random
from operator import itemgetter
from collections import deque
from itertools import ifilter
import threading
import time
import signal

input_params = {
        'base_lap_time':100,
        'n_cars':20,
        'variation_cars':10,
        'fuel_variation':0.03,
        'n_laps':50,
        'offset_start':1,
        'random_effect':0.05}

class DataGenerator(threading.Thread):
    def __init__(self,params,n_laps_start=10,speed_up=100):
        threading.Thread.__init__(self)
        self.p = params
        self.speed_up = speed_up
        self.n_laps_start = n_laps_start
        self.generate_laptimes()
        self.order()
        self.notify = []
        self.history = []
        self.listeners = []

    def generate_laptimes(self):
        car_numbers = range(self.p['n_cars'])

        car_base_lap_times = {x:self.p['variation_cars']*random.random()+self.p['base_lap_time'] for x in car_numbers}
        shuffled_cars = range(self.p['n_cars'])
        random.shuffle(shuffled_cars)
        car_offset_times =  {x:k*self.p['offset_start'] for x,k in zip(car_numbers,shuffled_cars)}
        lap_times = {i:[(car_offset_times[i],car_offset_times[i],0)] for i in car_numbers}

        for k in car_numbers:
            for i in range(self.p['n_laps']):
                new_lap_time =  car_base_lap_times[k] + random.normalvariate(0,self.p['random_effect']) + (self.p['n_laps']-i)*self.p['fuel_variation']
                lap_times[k].append((new_lap_time, new_lap_time + lap_times[k][-1][1],i))

        self.lap_times = lap_times

    def order(self):
        flat_times = [{'session_time':cumulative_lap_time, 'car': car, 'lap_time': lap_time, 'lap_number':lap_number} for car in self.lap_times for lap_time,cumulative_lap_time,lap_number in self.lap_times[car] ]
        flat_times = sorted(flat_times,key=itemgetter('session_time'))

        for index,lap in enumerate(flat_times):
            lap['index'] = index


        self.time_offset = next(ifilter(lambda x: x['lap_number'] == self.n_laps_start,flat_times))['session_time']
        self.times = deque(flat_times)


    def run(self):
        startedat = time.time()
        while self.times:
            next_lap = self.times.popleft()
            offset = next_lap['session_time']
            virtual_session_time = (time.time() - startedat)*self.speed_up + self.time_offset
            if offset > virtual_session_time:
               time.sleep(offset - virtual_session_time)

            self.history.append(next_lap)
            self.broadcast(next_lap)
        print 'Race Finished'

    def register(self,obj):
        self.listeners.append(obj)
        for i in self.history:
            obj.send(str(i)+'\n')

    def broadcast(self,obj):
        for l in self.listeners:
            l.send(str(obj)+'\n')

class Handler(asyncore.dispatcher_with_send):

    def __init__(self,sock,dg):
        asyncore.dispatcher_with_send.__init__(self,sock)
        dg.register(self) 
    #def handle_read(self):

        #First we send history


        #if data:
            #self.send(data)



class DataServer(asyncore.dispatcher):

    def __init__(self, host, port,dg):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.dg = dg
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            handler = Handler(sock,self.dg)

dg = DataGenerator(input_params)
dg.daemon = True
dg.start()



server = DataServer('localhost', 8080,dg)
asyncore.loop()

dg.join()
