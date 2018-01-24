
from optparse import OptionParser
from vmanager import Manager
import re

from paramiko import SSHClient
import paramiko
from scp import SCPClient  # pip install scp


def push_credentials(name, network, local_file='client_credentials.txt', remote_file='credentials.txt'):
    manager = Manager()
    clients = manager.list_search({"name": name})

    ssh = SSHClient()
    # ssh.load_system_host_keys()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for c in clients:
        assert network in c.networks, "No such network %s" % network

        c_net = c.networks[options.network]
        if len(c_net) > 0:
            c_ip = c_net[0]

            print("pushing to " + name + ": " + c_ip)

            ssh.connect(c_ip)
            scp = SCPClient(ssh.get_transport())

            scp.put(local_file, remote_file)
            ssh.close()


def get_rabbit_ip(name):
    manager = Manager()
    rabbits = manager.list_search({"name": name})

    assert len(rabbits) == 1, "%d rabbits running" % len(rabbits)

    rabbit = rabbits[0]

    assert options.network in rabbit.networks, "No such network %s" % options.network

    rabbit_network = rabbit.networks[options.network]

    assert len(rabbit_network) > 0, "No ips found"

    rabbit_ip = rabbit_network[0]

    return rabbit_ip


if __name__ == "__main__":

    parser = OptionParser()

    parser.add_option('-r', '--rabbitname', dest='rabbitname',
                      help='rabbitmq id',
                      default="rabbitmq", metavar='RABBITMQ')
    parser.add_option('-b', '--backendname', dest='backendname',
                      help='backend id',
                      default="backend", metavar='BACKEND')
    parser.add_option('-n', '--network', dest='network',
                      help='network id',
                      default="tutorial_net", metavar='NETWORK')

    (options, args) = parser.parse_args()

    rabbit_ip = get_rabbit_ip(options.rabbitname)

    print("rabbit ip: " + rabbit_ip)

    with open('client_credentials.txt.template', 'r') as f:
        config = ''.join(f.readlines())
        config = re.sub(r'\bserver\b', r"server=" + rabbit_ip, config)

    with open('client_credentials.txt', 'w') as f:
        f.write(config)

    push_credentials('backend', options.network)
    push_credentials('frontend', options.network)
