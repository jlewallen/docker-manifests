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

from collections import defaultdict
from urlparse import urlparse

class Context:
	def __init__(self, docker, cfg, state):
		formatting = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		logging.basicConfig(format = formatting, stream = sys.stdout, level = logging.INFO)

		self.docker = docker
		self.cfg = cfg
		self.state = state
		self.log = logging.getLogger('dock')
		self.log.info("local ip: %s" % Configuration.get_local_ip())

	def info(self, m):
		self.log.info(m)

	def save(self):
		if self.state: self.state.save()

	def allocate_ip(self):
		return self.state.allocate_ip()

class State:
	def __init__(self, path):
		self.path = path
		self.groups = defaultdict(set)
		self.containers = {}

	@staticmethod
	def load(path):
		if os.path.isfile(path):
			return pickle.load(open(path))
		return State(path)

	def purge(self, ctx):
		for name, instance in self.containers.items():
			if not instance.exists(ctx.docker):
				ctx.info("purging %s" % name)
				del self.containers[name]
				for group_name in self.groups:
					self.groups[group_name].remove(name)

	def group(self, group_name):
		return len(self.groups[group_name])

	def update(self, group_name, name, instance):
		self.groups[group_name].add(name)
		self.containers[name] = instance

	def assigned_ips(self):
		ips = []
		for name in self.containers:
			instance = self.containers[name]
			if instance.assigned_ip:
				ips.append(instance.assigned_ip)
		return ips

	def allocate_ip(self):
		assigned = self.assigned_ips()
		for i in range(11, 255):
			ip = Configuration.get_offset_ip(i)
			if ip not in assigned:
				return ip
		raise "No more IPs available"

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

