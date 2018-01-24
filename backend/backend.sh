#!/bin/sh

# set hostname 
sudo echo waspmq-backend > /etc/hostname
sudo sed -i "s/127.0.0.1 localhost/127.0.0.1 waspmq-backend/g" /etc/hosts

# install some dependencies
sudo apt-get -y update
sudo apt-get install -y python-dev
sudo apt-get install -y python-pip
sudo apt-get install -y python-pika

# prepare directory 
mkdir /usr/local/
cd /usr/local/

# echo "Cloning repo with WASP"
git clone https://github.com/TommyTram/wasp_cloud.git
