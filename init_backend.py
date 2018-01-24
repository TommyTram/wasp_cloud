
from optparse import OptionParser
from vmanager import Manager
import re

from paramiko import SSHClient
from scp import SCPClient  # pip install scp


def push_credentials(name, local_file='client_credentials.txt', remote_file='credentials.txt'):
    ssh = SSHClient()
    ssh.load_system_host_keys()

    clients = manager.list_search({"name": name})

    for c in clients:
        assert name in c.networks, "No such network %s" % options.network

        c_net = c.networks[options.network]
        if len(c_net) > 0:
            c_ip = c_net[0]

            print("pushing to " + name + ": " + c_ip)

            ssh.connect(c_ip)
            scp = SCPClient(ssh.get_transport())

            scp.put(local_file, remote_file)
            ssh.close()


if __name__ == "__main__":

    parser = OptionParser()

    # parser.add_option('-c', '--initfile', dest='initFile',
    #                   help='Path to INITFILE', metavar='INITFILE', default="vm-init.sh")
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

    manager = Manager()

    rabbits = manager.list_search({"name": options.rabbitname})

    assert len(rabbits) == 1, "%d rabbits running" % len(rabbits)

    rabbit = rabbits[0]

    assert options.network in rabbit.networks, "No such network %s" % options.network

    rabbit_network = rabbit.networks[options.network]

    if len(rabbit_network) > 0:
        rabbit_ip = rabbit_network[0]
    else:
        print("no ip found...")
        rabbit_ip = "error"

    print("rabbit ip: " + rabbit_ip)

    with open('client_credentials.txt.template', 'r') as f:
        config = ''.join(f.readlines())
        config = re.sub(r'\bserver\b', r"server=" + rabbit_ip, config)

    with open('client_credentials.txt', 'w') as f:
        f.write(config)

    push_credentials(backend)
    push_credentials(frontend)

    # ssh = SSHClient()
    # ssh.load_system_host_keys()

    # backends = manager.list_search({"name": options.backendname})

    # for b in backends:
    #     assert options.network in b.networks, "No such network %s" % options.network

    #     b_net = b.networks[options.network]
    #     if len(b_net) > 0:
    #         b_ip = b_net[0]

    #         print("backend ip:" + b_ip)

    #         ssh.connect(b_ip)
    #         scp = SCPClient(ssh.get_transport())

    #         scp.put('client_credentials.txt', 'credentials.txt')
    #         ssh.close()

    # rabbit_ip = manager.get_IP(vm=options.rabbitname)[0]

    # # print(args)
    # if options.action:
    #     manager = Manager(start_script=options.initFile)
    #     # manager.list()
    #     if options.action == "list":
    #         manager.list()
    #     if options.action == "list-ips":
    #         manager.get_IPs()
    #     if options.action == "terminate":
    #         manager.terminate(vm=args[0])
    #     if options.action == "create":
    #         manager.start_script = options.initFile
    #         manager.create(name=args[0])
    #         # time.sleep(1)
    #         # print(manager.get_IP(vm=args[0]))
    #     if options.action == "describe":
    #         manager.describe(vm=args[0])
    #     if options.action == "show-ip":
    #         manager.get_IP(vm=args[0])
    #     if options.action == "assign-fip":
    #         manager.assign_floating_IP(vm=args[0])
    # else:
    #     print("Syntax: 'python vmanager.py -h' | '--help' for help")
