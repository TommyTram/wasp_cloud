from optparse import OptionParser
from vmanager import Manager
from urllib2 import Request, urlopen, URLError
import urlparse


def request(ip, port, uri):
    # requst = "http://ip/uri"
    # urlparse.urljoin(ip, uri))
    request = urlparse.urljoin("http://" + ip + ":" + port, uri)

    print("Getting: " + request)

    try:
        response = urlopen(request)
        data = response.read()
        return data

    except URLError, e:
        print 'URLError:', e

        return None


def get_client_ips(name, network):

    manager = Manager()
    clients = manager.list_search({"name": options.backendname})

    ips = list()
    for c in clients:
        assert network in c.networks, "No such network %s" % network

        c_net = c.networks[options.network]
        if len(c_net) > 0:
            c_ip = c_net[0]
            ips.append(c_ip)

    return ips


def request_from_ips(ips, port, req):

    responses = list()
    for ip in ips:
        print(ip)
        responses.append(request(ip, port, req))

    return responses


if __name__ == "__main__":

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

    (options, args) = parser.parse_args()

    ips = get_client_ips(options.backendname, options.network)

    responses = request_from_ips(ips, options.port, '/isBusy')

    print(responses)

    pass
