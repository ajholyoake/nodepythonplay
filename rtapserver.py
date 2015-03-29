"""Fake rtap server using zeromq"""
import socket
import random
from operator import itemgetter
from collections import deque
from itertools import ifilter
import threading
import time
import signal
import sys
import json
port = "2377"

import zmq
zmqcontext = zmq.Context()
socket = zmqcontext.socket(zmq.PUB)
connstring = "tcp://*:{port}".format(port=port)
print connstring
socket.bind(connstring)


input_params = {
        'base_lap_time':100,
        'n_cars':20,
        'variation_cars':10,
        'fuel_variation':0.03,
        'n_laps':50,
        'offset_start':1,
        'random_effect':0.05}

class DataGenerator():
    def __init__(self,params,socket,n_laps_start=10,speed_up=10):
        self.p = params
        self.speed_up = speed_up
        self.n_laps_start = n_laps_start
        self.generate_laptimes()
        self.order()
        self.notify = []
        self.history = []
        self.listeners = []
        self.socket = socket

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
               time.sleep((offset - virtual_session_time)/self.speed_up)

            self.history.append(next_lap)
            self.broadcast(next_lap)
        self.broadcast('{"finished":true}')

    def broadcast(self,obj):
        print json.dumps(obj)
        sys.stdout.flush()
        self.socket.send("FOM " + json.dumps(obj))


dg = DataGenerator(input_params,socket)
dg.run()
