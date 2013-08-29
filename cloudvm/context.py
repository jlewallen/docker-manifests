#
#
#

import sys
import os
import re
import pickle
import docker.client
import logging

from interfaces import *
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
		self.networking = Networking(self.log, self.state)

	def update(self, group_name, name, instance):
		self.state.update(group_name, name, instance)

	def info(self, m):
		self.log.info(m)

	def save(self):
		if self.state: self.state.save()

	@staticmethod
	def get_docker():
		docker_url = urlparse("http://127.0.0.1:4243")
		return docker.Client(base_url = docker_url.geturl())

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
					group = self.groups.get(group_name)
					if group and name in group: group.remove(name)

	def group(self, group_name):
		return len(self.groups[group_name])

	def update(self, group_name, name, instance):
		self.groups[group_name].add(name)
		self.containers[name] = instance

	def get(self, long_id):
		return self.containers.get(long_id)

	def save(self):
		pickle.dump(self, open(self.path, "wb"))
