import ConfigParser
from optparse import OptionParser
from vmanager import Manager
import re

from paramiko import SSHClient
import paramiko
from scp import SCPClient  # pip install scp

import subprocess


def push_credentials(name, network, local_file='client_credentials.txt', remote_file='credentials.txt'):
    manager = Manager()
    clients = manager.list_search({"name": name})

    ssh = SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    for c in clients:
        if network in c.networks:
            c_net = c.networks[options.network]
            if len(c_net) > 0:
                c_ip = c_net[0]

                print("pushing to " + name + ": " + c_ip)

                try:
                    ssh.connect(c_ip, timeout=2)
                    scp = SCPClient(ssh.get_transport())

                    scp.put(local_file, remote_file)
                    ssh.close()
                except Exception, e:
                    print(e)
            else:
                print('network nog in ', c)


def get_rabbit_ip(name):
    manager = Manager()
    rabbits = manager.list_search({"name": name})

    assert len(rabbits) == 1, "%d rabbits running" % len(rabbits)

    rabbit = rabbits[0]

    if options.network in rabbit.networks:

        rabbit_network = rabbit.networks[options.network]

        assert len(rabbit_network) > 0, "No ips found"

        rabbit_ip = rabbit_network[0]

        return rabbit_ip
    else:
        print('no rabbit found')
        return None


def get_token(username, password, os_project_id, os_auth_url='https://xerces.ericsson.net:5000/v3', os_user_domain_name='xerces'):

    try:
        cmd = ['swift', '--os-auth-url', os_auth_url, '--os-user-domain-name', os_user_domain_name,
               '--os-username', username, '--os-password', password, '--os-project-id', os_project_id, 'auth']

        with open('os_token', 'w') as out:
            return_code = subprocess.call(cmd, stdout=out)
    except:
        print "Error getting swift token"


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
    parser.add_option('-c', '--credential', dest='credentialFile',
                      help='Path to CREDENTIAL file', default='credentials.txt', metavar='CREDENTIALFILE')

    (options, args) = parser.parse_args()

    config = ConfigParser.RawConfigParser()
    config.read(options.credentialFile)

    connection = {}

    connection["user_domain_name"] = config.get('auth', 'user_domain_name')
    connection["auth_url"] = config.get('auth', 'auth_url')
    connection["username"] = config.get('auth', 'username')
    connection["password"] = config.get('auth', 'password')
    connection["project_id"] = config.get('auth', 'project_domain_id')

    get_token(connection["username"], connection["password"], connection["project_id"],
              connection["auth_url"], connection["user_domain_name"])

    push_credentials('backend', options.network,
                     local_file='os_token', remote_file='os_token')

    rabbit_ip = get_rabbit_ip(options.rabbitname)

    print("rabbit ip: " + rabbit_ip)

    with open('client_credentials.txt.template', 'r') as f:
        config = ''.join(f.readlines())
        config = re.sub(r'\bserver\b', r"server=" + rabbit_ip, config)

    with open('client_credentials.txt', 'w') as f:
        f.write(config)

    push_credentials('backend', options.network)
    push_credentials('frontend', options.network)
