from flask import Flask
import pika
import ConfigParser
from optparse import OptionParser


class Connection:
    def __init__(self, connection_info=None):
        self.connection_info = connection_info
        self.credentials = pika.PlainCredentials(
            self.connection_info["username"], self.connection_info["password"])

    def send_to_queue(self, message="Hello!"):
        qname = self.connection_info["queue"]

        connection = pika.BlockingConnection(pika.ConnectionParameters(self.connection_info["server"],
                                                                       self.connection_info["port"], '/',
                                                                       self.credentials))
        channel = connection.channel()

        channel.queue_declare(queue=qname, durable=True)

        channel.basic_publish(exchange='',
                              routing_key=qname,
                              body=message,
                              properties=pika.BasicProperties(
                                  delivery_mode=2))

        print(" [x] Sent %s" % message)
        connection.close()


app = Flask(__name__)


@app.route("/convertMovie/<message>")
def send(message):
    movieId = message.replace("+", " ")
    messenger.send_to_queue(movieId)
    return "Sent '%s'\n" % movieId


if __name__ == "__main__":
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

        messenger = Connection(connection_info=connection)

        # start application
        app.run(host="0.0.0.0")

    else:
        # e.g. python frontend.py -c credentials.txt
        print("Syntax: 'python frontend.py -h' | '--help' for help")
