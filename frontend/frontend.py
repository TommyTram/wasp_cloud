from flask import Flask
import pika
import uuid
import ConfigParser
from optparse import OptionParser
from flask import request


class Connection:
    def __init__(self, connection_info=None):
        self.connection_info = connection_info
        self.credentials = pika.PlainCredentials(
            self.connection_info["username"], self.connection_info["password"])
        self.qname = self.connection_info["queue"]
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(self.connection_info["server"],
                                                                            self.connection_info["port"], '/',
                                                                            self.credentials))
        self.channel = self.connection.channel()

        #self.channel.queue_declare(queue=qname, durable=True)
        result = self.channel.queue_declare(queue='waspReply', durable=True)
        self.callback_queue = result.method.queue

    def __del__(self):
        self.connection.close()

    def send_to_queue(self, message="Hello!", corr_id='0000'):

        self.channel.basic_publish(exchange='',
                                   routing_key=self.qname,
                                   body=message,
                                   properties=pika.BasicProperties(

                                       delivery_mode=2,
                                       reply_to=self.callback_queue,
                                       correlation_id=corr_id))

        print(" [x] Sent %s" % message)


app = Flask(__name__)


@app.route("/convertMovie")
def send():
    global connection
    messenger = Connection(connection_info=connection)
    movieId = request.args.get('movieName')
    corrId = request.args.get('corrId')
    messenger.send_to_queue(movieId, corrId)
    return "Sent '%s'\n" % movieId


if __name__ == "__main__":
    global connection
    parser = OptionParser()
    parser.add_option('-c', '--credential', dest='credentialFile',
                      help='Path to CREDENTIAL file', metavar='CREDENTIALFILE')
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

        # start application
        app.run(host="0.0.0.0")

    else:
        # e.g. python frontend.py -c credentials.txt
        print("Syntax: 'python frontend.py -h' | '--help' for help")
