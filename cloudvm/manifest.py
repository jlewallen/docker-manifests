#
#
#

import json

from group import *

class Manifest:
	def __init__(self, path):
		self.path = path
		self.cfg = json.load(open(self.path))
		self.groups = self.make_groups()

	@staticmethod
	def load(path):
		return Manifest(path)

	def make_groups(self):
		return map(lambda name: Group(name, self.cfg[name]), self.cfg)

	def to_json(self):
		return {
			'path' : self.path,
			'groups' : map(lambda g: g.to_json(), self.groups),
			"start_url" : "/manifests/0/start",
			"kill_url" : "/manifests/0/kill",
			"destroy_url" : "/manifests/0/destroy"
		}

	def provision(self, ctx):
		self.update(ctx)
		map(lambda group: group.provision(ctx), self.groups)

	def stop(self, ctx):
		self.update(ctx)
		map(lambda group: group.stop(ctx), self.groups)
		self.update(ctx)
	
	def kill(self, ctx):
		self.update(ctx)
		map(lambda group: group.kill(ctx), self.groups)
		self.update(ctx)
	
	def destroy(self, ctx):
		self.update(ctx)
		map(lambda group: group.destroy(ctx), self.groups)
		self.update(ctx)

	def group(self, name):
		for group in self.groups:
			if group.name == name: return group
		return None
	
	def provisionGroup(self, ctx, name):
		self.group(name).provision(ctx)
		self.update(ctx)

	def killGroup(self, ctx, name):
		self.group(name).kill(ctx)
		self.update(ctx)

	def destroyGroup(self, ctx, name):
		self.group(name).destroy(ctx)
		self.update(ctx)

	def resizeGroup(self, ctx, name, size):
		self.group(name).resize(ctx, size)
		self.update(ctx)

	def update(self, ctx):
		map(lambda group: group.update(ctx), self.groups)
	
	def save(self):
		json.dump(self.cfg, open(self.path, "w"), sort_keys=True, indent=4, separators=(',', ': '))

	def find_instance(self, name):
		for group in self.groups:
			for instance in group.instances:
				if instance.name == name: return instance
		return None

