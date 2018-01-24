import ConfigParser
from optparse import OptionParser
from vmanager import Manager
import re

from paramiko import SSHClient
import paramiko
from scp import SCPClient  # pip install scp

import json
import urllib2
import urlparse


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


def get_token(username, password, os_auth_url='https://xerces.ericsson.net:5000/v3', os_user_domain_name='xerces'):

    # curl -v -s -X POST $OS_AUTH_URL/auth/tokens   -H "Content-Type: application/json"   -d '{ "auth": { "identity": { "methods": ["password"],"password": {"user": {"domain": {"name": "'"$OS_USER_DOMAIN_NAME"'"},"name": "'"$OS_USERNAME"'", "password": "'"$OS_PASSWORD"'"} } } } }

    data = {"auth": {"identity": {"methods": ["password"], "password": {
        "user": {"domain": {"name": os_user_domain_name},
                 "name": username,
                 "password": password}
    }}}}

    url = urlparse.urljoin(os_auth_url + "/", 'auth/tokens')
    print(json.dumps(data))
    print(url)

    req = urllib2.Request(url, json.dumps(
        data), {'Content-Type': 'application/json'})

    try:
        response = urllib2.urlopen(req)
        headers = dict(response.info())

        print(headers)

        print(response.read())

    except urllib2.HTTPError as e:
        error_message = e.read()
        print error_message


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

    get_token(connection["username"], connection["password"],
              connection["auth_url"], connection["user_domain_name"])

    rabbit_ip = get_rabbit_ip(options.rabbitname)

    print("rabbit ip: " + rabbit_ip)

    with open('client_credentials.txt.template', 'r') as f:
        config = ''.join(f.readlines())
        config = re.sub(r'\bserver\b', r"server=" + rabbit_ip, config)

    with open('client_credentials.txt', 'w') as f:
        f.write(config)

    push_credentials('backend', options.network)
    push_credentials('frontend', options.network)
