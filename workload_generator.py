#!/usr/bin/env python
import pika
from optparse import OptionParser
import ConfigParser
import time
from flask import Flask
import threading
import uuid
import urllib2
import urlparse
import os
import requests
import datetime
import numpy as np

idHolder = dict()
logFileName = time.strftime("logs/wl_%Y%m%d-%H%M%S") + ".csv"

def callback(ch, method, properties, body):
    global idHolder
    global logFileName
    global connection
    # Get id of finished job and assign current time
    idX = properties.correlation_id

    # Find out queue size

    # Compute time taken for the job from frontend -> backend

    if idX in idHolder:

        idHolder[idX][1] = time.time()
        timeTaken = idHolder[idX][1] - idHolder[idX][0]
        print("Job id : " + idX + "took " + str(timeTaken) +
              "[s] to complete. Queue size " + str(idHolder[idX][2]))

        with open(logFileName, "a") as log:
            log.write(datetime.datetime.now().isoformat() + ',' + idX +
                      ',' + str(timeTaken) + "," + str(idHolder[idX][2]) + "\n")

        del(idHolder[idX])
    else:
        print('unknown job ' + idX)


def receive(connection_info=None):
    global channel
    qname = "waspReply"
    credentials = pika.PlainCredentials(
        connection_info["username"], connection_info["password"])
    c = pika.BlockingConnection(pika.ConnectionParameters(
        connection_info["server"], connection_info["port"], '/', credentials))
    channel = c.channel()

    channel.queue_declare(queue=qname, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback, queue=qname, no_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


def workloadGeneration():
    global idHolder
    global channel

    # Static movie and url at the moment
    url = 'http://172.16.0.10:5000/convertMovie'
    fileName = 'jellyfish-3-mbps-hd-h264.mkv'

    # Define length of simulated users
    tEnd = 3600 # time in seconds
   
    # Define time at which the extra users kick in
    tExtra = 1800
    
    # Avg time for each user between service calls
    avgTimeBetweenCallsOriginal = [20+20, 20+25, 20+30, 20+35, 20+40]

    # Independent users -> can generate random times they will call the service
    timeArray = np.array([])
    for idx in range(len(avgTimeBetweenCallsOriginal)):
        mu = avgTimeBetweenCallsOriginal[idx]
	t = np.random.uniform(0,mu)
	timeHolder = np.array([])
	while t <= tEnd:
	    t = t + np.random.normal(mu,10)
	    #timeArray.append(t)
	    timeHolder = np.append(timeHolder,t)
	#timeHolder -= timeHolder[0] - 0.5*idx
	timeArray = np.append(timeArray,timeHolder)

    # Add times for the extra appearing users
    avgTimeBetweenCallsExtra = [18+20, 19+20, 20+20, 21+20, 22+20]
    timeArrayExtra = np.array([])
    for idx in range(len(avgTimeBetweenCallsExtra)):
        mu = avgTimeBetweenCallsExtra[idx]
        t = np.random.uniform(tExtra,tExtra+mu)
	timeHolder = np.array([])
	while t <= tEnd:
            t = t + np.random.normal(mu,10)
	    timeHolder = np.append(timeHolder,t)

	if len(timeHolder) > 0:
	    #timeHolder -= timeHolder[0] - 0.5*idx - tExtra
	    timeArrayExtra = np.append(timeArrayExtra,timeHolder)
    
    for idx in range(len(avgTimeBetweenCallsOriginal)):
        mu = avgTimeBetweenCallsOriginal[idx]
        t = np.random.uniform(tEnd,tEnd+mu)
        timeHolder = np.array([])
        while t <= tEnd + 1800:
            t = t + np.random.normal(mu,10)
            #timeArray.append(t)
            timeHolder = np.append(timeHolder,t)
        #timeHolder -= timeHolder[0] - 0.5*idx
        timeArray = np.append(timeArray,timeHolder)

    # Sort the array so that we know at which times to send the requests
    sortedTimeArray = sorted(np.append(timeArray,timeArrayExtra))
    dt = np.ediff1d(sortedTimeArray)

    # Loop through the simulated service calls
    for sleepTime in dt:
        # Assign id
        corrId = str(uuid.uuid4())
        print(fileName)
        print(corrId)

        # Open the channel to see how many messages are already in the queue
        res = channel.queue_declare(queue='wasp', durable=True)
        queueSize = res.method.message_count
        print("queue size: " + str(queueSize))

        # Assign the idHolder which contains the job id, start time, and queue size. To be filled at callback with end time
        idHolder[corrId] = [time.time(), 0, queueSize]

        # Set up payload and send it to the front end
        payload = {'movieName': fileName, 'corrId': corrId}
        r = requests.get(url, params=payload)

        print('User sent message with id', corrId)

        # Sleep for the amount of time until next simulated call
        time.sleep(sleepTime) 
       
    print('Sent all requests')

if __name__ == "__main__":
    global channel
    global connection
    global res
    parser = OptionParser()
    parser.add_option('-c', '--credential', dest='credentialFile',
                      help='Path to CREDENTIAL file', metavar='CREDENTIALFILE')
    parser.add_option('-t', '--os_token', dest='osTokenFile',
                      default='~ubuntu/os_token', help='Path to OSTOKEN file', metavar='OSTOKEN')
    (options, args) = parser.parse_args()

    os_token_file = options.osTokenFile

    jobs = []
    if options.credentialFile:
        config = ConfigParser.RawConfigParser()
        config.read(options.credentialFile)
        connection = {}
        connection["server"] = config.get('rabbit', 'server')
        connection["port"] = int(config.get('rabbit', 'port'))
        connection["queue"] = config.get('rabbit', 'queue')
        connection["username"] = config.get('rabbit', 'username')
        connection["password"] = config.get('rabbit', 'password')

        thread = threading.Thread(target=receive, args=(connection,))
        jobs.append(thread)
        thread = threading.Thread(target=workloadGeneration)
        jobs.append(thread)
    else:
        # e.g. python backend.py -c credentials.txt
        print("Syntax: 'python backend.py -h' | '--help' for help")

    qname = connection["queue"]
    credentials = pika.PlainCredentials(
        connection["username"], connection["password"])
    connection = pika.BlockingConnection(pika.ConnectionParameters(connection["server"],
                                                                   connection["port"], '/',
                                                                   credentials))
    channel = connection.channel()
    res = channel.queue_declare(queue=qname, durable=True)

    for j in jobs:
        j.start()
 # Ensure all of the threads have finished
    for j in jobs:
        j.join()
