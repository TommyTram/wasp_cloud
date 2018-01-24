#!/usr/bin/env python
import pika
from optparse import OptionParser
import ConfigParser
import time

def callback(ch, method, properties, body):
	print(" [x] Processing %r" % body)

	ch.basic_ack(delivery_tag = method.delivery_tag)
	print(" [x] Process done ---")
	
def receive(connection_info=None):
	qname = "wasp"
	credentials = pika.PlainCredentials(connection_info["username"], connection_info["password"])
	connection = pika.BlockingConnection(pika.ConnectionParameters(connection_info["server"],connection_info["port"],'/',credentials))
	channel = connection.channel()

	channel.queue_declare(queue=qname, durable=True)
	channel.basic_qos(prefetch_count=1)
	channel.basic_consume(callback, queue=qname)
	print(' [*] Waiting for messages. To exit press CTRL+C')
	channel.start_consuming()


if __name__=="__main__":
	parser = OptionParser()
	parser.add_option('-c', '--credential', dest='credentialFile', help='Path to CREDENTIAL file', metavar='CREDENTIALFILE')
	(options, args) = parser.parse_args()
	
	if options.credentialFile:
		config = ConfigParser.RawConfigParser()
		config.read(options.credentialFile)
		connection = {}
		connection["server"] = config.get('rabbit', 'server')
		connection["port"] = int(config.get('rabbit', 'port'))
		connection["queue"] = config.get('rabbit', 'queue')
		connection["username"] = config.get('rabbit', 'username')
		connection["password"] = config.get('rabbit', 'password')
		receive(connection_info=connection)
	else:
		#e.g. python backend.py -c credentials.txt
		print("Syntax: 'python backend.py -h' | '--help' for help")

