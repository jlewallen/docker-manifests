#
#
#

import sys
import os
import re
import pickle
import docker.client
import logging
import iptools
import netifaces

from urlparse import urlparse

class Context:
	def __init__(self, docker, cfg, state):
		self.docker = docker
		self.cfg = cfg
		self.state = state
		formatting = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		logging.basicConfig(format = formatting, stream = sys.stdout, level = logging.INFO)
		self.log = logging.getLogger('dock')

	def info(self, m):
		self.log.info(m)

	def save(self):
		if self.state: self.state.save()

class State:
	def __init__(self, path):
		self.path = path
		self.containers = {}

	@staticmethod
	def load(path):
		if os.path.isfile(path):
			return pickle.load(open(path))
		return State(path)

	def update(self, long_id, instance):
		self.containers[long_id] = instance

	def get(self, long_id):
		return self.containers.get(long_id)

	def save(self):
		pickle.dump(self, open(self.path, "wb"))

class Configuration:
	def __init__(self):
		None

	@staticmethod
	def get_docker():
		docker_url = urlparse("http://127.0.0.1:4243")
		return docker.Client(base_url = docker_url.geturl())

	@staticmethod
	def get_local_ip():
		ips = []
		for interface in netifaces.interfaces():
			addresses = netifaces.ifaddresses(interface)
			if netifaces.AF_INET in addresses:
				for link in addresses[netifaces.AF_INET]:
					ips.append(link['addr'])
		for ip in ips:
			if re.match(r"^192.168", ip): return ip
		raise "Unable to infer IP"

	@staticmethod
	def get_offset_ip(offset):
		return iptools.ipv4.long2ip(iptools.ipv4.ip2long(Configuration.get_local_ip()) + offset)

