#!/bin/bash
apt-get update
apt-get -y install ansible
cp -f /vagrant/vagrant/ansible_hosts /etc/ansible/hosts
chmod 644 /etc/ansible/hosts
ansible-playbook -v --connection=local /vagrant/vagrant/basic.yml
