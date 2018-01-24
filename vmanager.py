from __future__ import print_function
from keystoneauth1.identity import v3
from keystoneauth1 import session
from novaclient.client import Client as NovaClient
import datetime
import sys
import time
from ConfigParser import SafeConfigParser
from optparse import OptionParser


class Manager:
    DEFAULT_IMAGE = "ubuntu 16.04"
    DEFAULT_FLAVOUR = "c1m05"

    def __init__(self, start_script=None):
        self.start_script = start_script

        parser = SafeConfigParser()
        try:
            parser.read("credentials.txt")
        except IOError:
            print("Credential file missing")
            sys.exit()

        self.username = parser.get("auth", "username")
        self.password = parser.get("auth", "password")
        self.tenant_name = parser.get("auth", "tenant_name")
        self.user_domain = parser.get("auth", "user_domain_name")
        self.project_domain = parser.get("auth", "project_domain_name")
        self.project_domain_id = parser.get("auth", "project_domain_id")
        self.auth_url = parser.get("auth", "auth_url")
        self.net_id = parser.get("auth", "net_id")
        self.pkey_id = parser.get("auth", "pkey_id")
        auth = v3.Password(username=self.username, password=self.password, project_name=self.tenant_name, auth_url=self.auth_url,
                           user_domain_name=self.user_domain, project_domain_name=self.project_domain, project_id=self.project_domain_id)
        sess = session.Session(auth=auth)
        self.nova = NovaClient("2", session=sess)

    def create(self, name=""):
        image = self.nova.images.find(name=Manager.DEFAULT_IMAGE)
        flavor = self.nova.flavors.find(name=Manager.DEFAULT_FLAVOUR)
        net = self.nova.networks.find(label=self.net_id)
        nics = [{'net-id': net.id}]
        vm = self.nova.servers.create(name=name, image=image, flavor=flavor, key_name=self.pkey_id,
                                      nics=nics, userdata=open(self.start_script))
        print("VM %s created" % name.upper())
        return

    def assign_floating_IP(self, vm):
        self.nova.floating_ip_pools.list()
        floating_ip = self.nova.floating_ips.create(
            self.nova.floating_ip_pools.list()[0].name)
        instance = self.nova.servers.find(name=vm)
        instance.add_floating_ip(floating_ip)
        print("floating IP %s is assigned to %s VM", floating_ip.ip, vm)
        # return floating_ip

    def list(self):
        for idx, server in enumerate(self.nova.servers.list()):
            print ("%d\t%s" % (idx, server.name),
                   "\t", server.networks, sep="")
        return

    def terminate(self, vm=""):
        server_exists = False
        for s in self.nova.servers.list():
            if s.name == vm:
                print("server %s exists" % vm)
                server_exists = True
                break
        if server_exists:
            print("deleting server..........")
            self.nova.servers.delete(s)
            print("server '%s' successfully deleted" % vm)
        else:
            print ("server '%s' does not exist" % vm)
        return

    def get_IPs(self):
        ip_list = self.nova.floating_ips.list()
        for ip in ip_list:
          # if ip.instance_id
            print("fixed_ip : %s\n" % ip.fixed_ip)
            print("ip : %s" % ip.ip)
            print("instance_id : %s" % ip.instance_id)
        # return {"Floating":ip.ip, "Fixed":ip.fixed_ip}

    def get_IP(self, vm):
        instance = self.nova.servers.find(name=vm)
        # print(instance.networks)
        # ip=instance.networks['CloudCourse'][0]
        print (instance.networks[self.net_id])  # ("ipaddress:"+ip);

    def describe(self, vm):
        instance = self.nova.servers.find(name=vm)
        print("server id: %s\n" % instance.id)
        print("server name: %s\n" % instance.name)
        print("server image: %s\n" % instance.image)
        print("server flavor: %s\n" % instance.flavor)
        print("server key name: %s\n" % instance.key_name)
        print("user_id: %s\n" % instance.user_id)

#    def shutdown(self, vm=""):
#        pass


if __name__ == "__main__":
    parser = OptionParser()

    parser.add_option('-c', '--initfile', dest='initFile',
                      help='Path to INITFILE', metavar='INITFILE', default="vm-init.sh")
    parser.add_option('-a', '--action', dest='action',
                      help='Action to perform: [list | terminate VM_NAME | create VM_NAME | describe VM_NAME | show-ip VM_NAME | assign-fip VM_NAME]',
                      default="list", metavar='ACTION')
    (options, args) = parser.parse_args()
    # print(args)
    if options.action:
        manager = Manager(start_script=options.initFile)
        # manager.list()
        if options.action == "list":
            manager.list()
        if options.action == "list-ips":
            manager.get_IPs()
        if options.action == "terminate":
            manager.terminate(vm=args[0])
        if options.action == "create":
            manager.start_script = options.initFile
            manager.create(name=args[0])
            # time.sleep(1)
            # print(manager.get_IP(vm=args[0]))
        if options.action == "describe":
            manager.describe(vm=args[0])
        if options.action == "show-ip":
            manager.get_IP(vm=args[0])
        if options.action == "assign-fip":
            manager.assign_floating_IP(vm=args[0])
    else:
        print("Syntax: 'python vmanager.py -h' | '--help' for help")
