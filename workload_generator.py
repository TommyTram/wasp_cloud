#!/usr/bin/env python
import pika
from optparse import OptionParser
import ConfigParser
import time
from flask import Flask
import threading
import psutil
import urllib2
import urlparse
import os

if __name__ == "__main__":

	url = 'http://172.16.0.10:5000/convertMovie/'
	fileName = 'jellyfish-3-mbps-hd-h264.mkv'
    corrId = str(uuid.uuid4())

	payload = {'movieName' : filenName, 'corrId' : corrId}
	r = requests.get(url,params=payload)

