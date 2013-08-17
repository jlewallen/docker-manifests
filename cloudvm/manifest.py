#
#
#

import json

from group import *

class Manifest:
	def __init__(self, name):
		self.name = name
		self.groups = []

	@staticmethod
	def load(path, ctx):
		manifest_cfg = json.load(open(path))
		manifest = Manifest(path)
		for group_name in manifest_cfg:
			group_cfg = manifest_cfg[group_name]
			template = group_cfg["template"]
			group = Group(group_name, template)
			group.resize(ctx, 1)
			manifest.groups.append(group)
		return manifest

	def to_json(self):
		return {
			'name' : self.name,
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
	
	def find_instance(self, name):
		for group in self.groups:
			for instance in group.instances:
				if instance.name == name: return instance
		return None

