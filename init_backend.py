
from optparse import OptionParser
from vmanager import Manager

if __name__ == "__main__":

    parser = OptionParser()

    # parser.add_option('-c', '--initfile', dest='initFile',
    #                   help='Path to INITFILE', metavar='INITFILE', default="vm-init.sh")
    parser.add_option('-r', '--rabbitname', dest='rabbitmq',
                      help='rabbitmq id'
                      default="list", metavar='RABBITMQ')
    (options, args) = parser.parse_args()

    manager = Manager()

    manager.get_IP(vm=options.rabbitname)

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
