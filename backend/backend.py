#!/usr/bin/env python
import pika
from optparse import OptionParser
import ConfigParser
import time
from flask import Flask
import threading
import psutil
import urllib2
import urlparse
import os
from tempfile import mkstemp


app = Flask(__name__)
isBusyState = "0"


@app.route("/isBusy")
def isBusy():
    return isBusyState


@app.route("/cpuLoad")
def cpuLoad():
    return str(psutil.cpu_percent())


def callback(ch, method, properties, body):
    global isBusyState
    isBusyState = "1"
    print(" [x] Processing %r" % body)

    # Read download url

    auth_path = "https://xerces.ericsson.net:5000/v3/"
    container = "CloudStoring"

    with open('~ubuntu/os_token') as f:
        os_token = myfile.read().replace('\n', '')

    #downloadPath = "https://xerces.ericsson.net:7480/swift/v1/CloudStoring/"

    # Extract file name
    filename = body

    filebody, ext = os.path.splitext(filename)

    #url_in = urlparse.urljoin(downloadPath, filename)

    #fileLocation = "/tmp/"

    fd_in, file_in = mkstemp()
    fd_out, file_out = mkstemp()

    # Open url

    try:
        cmd = "sudo swift -A {1} --os-auth-token {2} download {3} {4}".format(
            auth_path, os_token, container, filename)

        os.system(cmd)
        #rsp = urllib2.urlopen(url_in)

        # with open(file_in, 'w') as f:
        #    f.write(rsp.read())
    except:
        print("Couldn't download")

    try:
        cmd = """sudo mencoder %s -ovc lavc -lavcopts vcodec=mpeg4:vbitrate=3000 -oac copy -o %s""" % (
            file_in, file_out)
        os.system(cmd)
    except:
        print("Couldn't convert")

    ch.basic_ack(delivery_tag=method.delivery_tag)
    # time.sleep(3)

    try:
        os.remove(file_in)
    except:
        print("Couldn't remove file")

    os.close(fd_in)
    os.close(fd_out)

    print(" [x] Process done ---")
    isBusyState = "0"


def receive(connection_info=None):
    qname = "wasp"
    credentials = pika.PlainCredentials(
        connection_info["username"], connection_info["password"])
    connection = pika.BlockingConnection(pika.ConnectionParameters(
        connection_info["server"], connection_info["port"], '/', credentials))
    channel = connection.channel()

    channel.queue_declare(queue=qname, durable=True)
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(callback, queue=qname)
    print(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-c', '--credential', dest='credentialFile',
                      help='Path to CREDENTIAL file', metavar='CREDENTIALFILE')
    (options, args) = parser.parse_args()

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
        print("Starting flask also")
        thread = threading.Thread(target=app.run, args=("0.0.0.0",))
        jobs.append(thread)
    else:
        # e.g. python backend.py -c credentials.txt
        print("Syntax: 'python backend.py -h' | '--help' for help")
    for j in jobs:
        j.start()
 # Ensure all of the threads have finished
    for j in jobs:
        j.join()
