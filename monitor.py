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
from init_backend import push_credentials

from paramiko import SSHClient
from scp import SCPClient  # pip install scp


def push_to_ip(ip, local_files=['client_credentials.txt'], remote_files=['credentials.txt']):

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    print("pushing to: " + ip)

    try:
        ssh.connect(ip, timeout=1)
        scp = SCPClient(ssh.get_transport())
        for n, f in enumerate(local_files):
            scp.put(f, remote_files[n])
        ssh.close()
    except Exception, e:
        print(e)


def start_vm(name, start_script, image=None):

    manager = Manager(start_script=start_script)
    manager.create(name=name, image=image)


def stop_vm(ip):
    manager = Manager()
    manager.terminate_ip(ip)


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
        # assert network in c.networks, "No such network %s" % network

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


def get_working_nodes(responses):

    free = list()
    busy = list()
    na = list()
    for key in responses:
        if responses[key] == '0':
            free.append(key)
        elif responses[key] == '1':
            busy.append(key)
        else:
            na.append(key)

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

    free_nodes, busy_nodes, na_nodes = get_working_nodes(busy_resp)

    cpu_loads = request_from_ips(ips, port, '/cpuLoad')

    # cpu = get_cpu_stats(cpu_resp)
    # cpu = sum_cpu_load(cpu_loads)

    cpu = dict((k, v) for k, v in cpu_loads.iteritems() if v is not None)

    return nodes, free_nodes, busy_nodes, na_nodes, cpu


def regulate(nodes, queue, setpoint=5):
    print('setpoint ', setpoint)
    p = .2
    free, busy, na = nodes
    d = queue - setpoint
    r = p * d

    return r


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
    last_credentials = datetime.datetime(1970, 1, 1)

    log = open(time.strftime("logs/mon_%Y%m%d-%H%M%S") + ".csv", "w+")

    try:
        while (True):

            nodes, free_nodes, busy_nodes, na_nodes, cpu = get_stats(
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

            node_diff = regulate(nodes, queue, setpoint=5 * (free + busy))
            print('node diff: ', node_diff)

            # for n in range(int(ceil(node_diff))):
            if last_update + datetime.timedelta(seconds=60) < datetime.datetime.now():
                if node_diff > 0 and na == 0:
                    print('starting wm')
                    start_vm('backend', 'backend/backend.sh')
                    last_update = datetime.datetime.now()
                if node_diff < 0:
                    if free + busy > 1:
                        if na > 0:
                            kill_ip = na_nodes[0]
                            print('killing na node')
                        if free > 0:
                            print('killing free node')
                            kill_ip = free_nodes[0]
                        else:
                            print('killing working node')
                            kill_ip = busy_nodes[0]

                        print('killing', kill_ip)
                        stop_vm(kill_ip)

            if na > 0:
                if last_credentials + datetime.timedelta(seconds=30) < datetime.datetime.now():
                    print('pushing credentials')

                    #push_credentials('backend', options.network)
                    # push_credentials('backend', options.network,
                    #                 local_file='os_token', remote_file='os_token')

                    for ip in na_nodes:
                        push_to_ip(ip, ['client_credentials.txt',
                                        'os_token'],
                                   remote_files=['credentials.txt',
                                                 'os_token'])
                    last_credentials = datetime.datetime.now()

            time.sleep(1)
    except KeyboardInterrupt:
        log.close()

    pass
