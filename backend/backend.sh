#!/bin/sh

# set hostname
sudo echo cloud-backend > /etc/hostname
sudo sed -i "s/127.0.0.1 localhost/127.0.0.1 cloud-backend/g" /etc/hosts

# install some dependencies
sudo apt-get -y update
sudo apt-get install -y python-dev
sudo apt-get install -y python-pip
sudo apt-get install -y python-pika
sudo pip install flask
sudo pip install psutil

# echo "Cloning repo with WASP"
git clone https://github.com/TommyTram/wasp_cloud.git ~ubuntu/wasp_cloud


while [ ! -f ~ubuntu/credentials.txt ] ;
do
      sleep 2
done

python ~ubuntu/wasp_cloud/backend/backend.py
