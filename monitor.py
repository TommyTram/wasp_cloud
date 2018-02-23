from optparse import OptionParser
import pika
import ConfigParser
from vmanager import Manager
from urllib2 import Request, urlopen, URLError
import urlparse
import os.path
import time
import datetime
from math import ceil


def start_vm(name, image, start_script):

    manager = Manager(start_script=start_script)
    manager.create(name=name, image=image)


def request(ip, port, uri):
    # requst = "http://ip/uri"
    # urlparse.urljoin(ip, uri))
    request = urlparse.urljoin("http://" + ip + ":" + port, uri)

    try:
        response = urlopen(request, timeout=1)
        data = response.read()
        return data

    except URLError, e:
        print "URLError (%s):" % request, e

        return None


def get_client_ips(name, network):

    manager = Manager()
    clients = manager.list_search({"name": name})

    ips = list()
    for c in clients:
        #assert network in c.networks, "No such network %s" % network

        if network in c.networks:

            c_net = c.networks[network]
            if len(c_net) > 0:
                c_ip = c_net[0]
                ips.append(c_ip)

    return ips


def get_busy_stats(responses):

    free = 0
    busy = 0
    na = 0
    for key in responses:
        r = responses[key]
        if r == '0':
            free += 1
        if r == '1':
            busy += 1
        if r is None:
            na += 1

    return free, busy, na


def sum_cpu_load(responses):

    sum = 0.0
    for key in responses:
        if responses[key] is not None:
            sum += float(responses[key])

    return sum


def request_from_ips(ips, port, req):

    responses = dict()
    for ip in ips:
        responses[ip] = request(ip, port, req)

    return responses


def get_queue_length(credential_file):

    config = ConfigParser.RawConfigParser()
    config.read(options.credentialFile)
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

    return res.method.message_count


def get_stats(backendname, network, port):

    ips = get_client_ips(backendname, network)
    busy_resp = request_from_ips(ips, port, '/isBusy')
    nodes = get_busy_stats(busy_resp)

    cpu_loads = request_from_ips(ips, port, '/cpuLoad')

    #cpu = get_cpu_stats(cpu_resp)
    #cpu = sum_cpu_load(cpu_loads)

    cpu = dict((k, v) for k, v in cpu_loads.iteritems() if v is not None)

    return nodes, cpu


def regulate(nodes, queue, setpoint=5):

    #global last_update
    p = .2

    free, busy, na = nodes

    d = queue - setpoint

    r = p * d

    return r

    # if last_update + datetime.timedelta(seconds=120) < datetime.datetime.now():

    #    print('update!')
    #    last_update = datetime.datetime.now()
    #    return r
    # else:
    #    print('waiting..')

    # return 0


if __name__ == "__main__":
    global last_update

    parser = OptionParser()

    parser.add_option('-b', '--backendname', dest='backendname',
                      help='backend id',
                      default="backend", metavar='BACKEND')
    parser.add_option('-n', '--network', dest='network',
                      help='network id',
                      default="tutorial_net", metavar='NETWORK')
    parser.add_option('-p', '--port', dest='port',
                      help='port',
                      default="5000", metavar='PORT')
    parser.add_option('-c', '--credential', dest='credentialFile',
                      help='Path to CREDENTIAL file', default='client_credentials.txt', metavar='CREDENTIALFILE')

    (options, args) = parser.parse_args()

    last_update = datetime.datetime(1970, 1, 1)

    log = open(time.strftime("logs/mon_%Y%m%d-%H%M%S") + ".csv", "w+")

    try:
        while (True):

            nodes, cpu = get_stats(
                options.backendname, options.network, options.port)

            queue = get_queue_length(options.credentialFile)

            cpu_str = ['{}: {}'.format(key, val)
                       for key, val in cpu.iteritems()]

            free, busy, na = nodes

            print(
                "Free: {0} Busy: {1} N/A: {2} Queue: {3} CPU: {4}".format(free, busy, na, queue, cpu_str))

            log.write("{0},{1},{2},{3},{4},{5}\n".format(
                datetime.datetime.now().isoformat(), free, busy, na, queue, ','.join(cpu.values())))
            log.flush()

            node_diff = regulate(nodes, queue)
            print('node diff: ', node_diff)

            if node_diff > 0:
                    # for n in range(int(ceil(node_diff))):
                if last_update + datetime.timedelta(seconds=120) < datetime.datetime.now():
                    print('starting wm')
                    start_vm('backend', 'backend', 'backend/backend_image.sh')
                    last_update = datetime.datetime.now()

            time.sleep(1)
    except KeyboardInterrupt:
        log.close()

    pass
