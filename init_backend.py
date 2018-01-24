
from optparse import OptionParser
from vmanager import Manager
import re


if __name__ == "__main__":

    parser = OptionParser()

    # parser.add_option('-c', '--initfile', dest='initFile',
    #                   help='Path to INITFILE', metavar='INITFILE', default="vm-init.sh")
    parser.add_option('-r', '--rabbitname', dest='rabbitname',
                      help='rabbitmq id',
                      default="rabbitmq", metavar='RABBITMQ')
    parser.add_option('-n', '--network', dest='network',
                      help='network id',
                      default="tutorial_net", metavar='NETWORK')

    (options, args) = parser.parse_args()

    manager = Manager()

    rabbits = manager.list_search({"name": options.rabbitname})

    print(rabbits)
    print(len(rabbits))
    print(rabbits[0])
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

    with f = open('client_credentials.txt', 'w'):
        config = ''.join(f.readlines())
        re.sub(r'\bserver\b', r"server=" + rabbit_ip, config)
        f.write(yourTxt)

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
