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

idHolder = dict()
logFileName = time.strftime("%Y%m%d-%H%M%S") + ".csv"
def callback(ch, method, properties, body):
    global idHolder
    global logFileName
    # Get id of finished job and assign current time
    idX = properties.correlation_id
    idHolder[idX][1] = time.time()

    config = ConfigParser.RawConfigParser()
    config.read('../credentials.txt')
    connection = {}
    connection["server"] = config.get('rabbit', 'server')
    connection["port"] = int(config.get('rabbit', 'port'))
    connection["queue"] = config.get('rabbit', 'queue')
    connection["username"] = config.get('rabbit', 'username')
    connection["password"] = config.get('rabbit', 'password')

    qname = connection["queue"]
    credentials = pika.PlainCredentials(
        connection["username"], connection["password"])
    connection = pika.BlockingConnection(pika.ConnectionParameters(connection["server"],
                                                                   connection["port"], '/',
                                                                   credentials))
    channel = connection.channel()
    res = channel.queue_declare(queue=qname, durable=True)

    # Find out queue size
    queueSize = res.method.message_count
    #Compute time taken for the job from frontend -> backend
    timeTaken = idHolder[idX][1] - idHolder[idX][0]
    print("Job id : ",idX, "took ", timeTaken, "[s] to complete. Queue size ",queueSize)
    del(idHolder[idX])

    log = open(logFileName, "a")
    log.write(str(timeTaken) + "," + str(queueSize) + "\n")
    log.close()

def receive(connection_info=None):
    global channel
    qname = "waspReply"
    credentials = pika.PlainCredentials(
        connection_info["username"], connection_info["password"])
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        connection_info["server"], connection_info["port"], '/', credentials))
    channel = connection.channel()

    channel.queue_declare(queue=qname, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback, queue=qname, no_ack=True)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

def workloadGeneration():
    global idHolder
    url = 'http://172.16.0.10:5000/convertMovie'
    fileName = 'jellyfish-3-mbps-hd-h264.mkv'
    for i in range(0,2):
        corrId = str(uuid.uuid4())
        print(fileName)
        print(corrId)
        idHolder[corrId] = [time.time(),0]
        payload = {'movieName' : fileName, 'corrId' : corrId}
        r = requests.get(url,params=payload)

if __name__ == "__main__":

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
    for j in jobs:
        j.start()
 # Ensure all of the threads have finished
    for j in jobs:
        j.join()





