#
#
#

import json

from group import *

log = logging.getLogger('dock')

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
			type = group_cfg.get("type")
			number = group_cfg.get("number")
			if not number: number = 1
			group = Group(group_name, type, template)
			group.resize(ctx, number)
			manifest.groups.append(group)
		return manifest

	def to_json(self):
		return {
			'name' : self.name,
			'groups' : map(lambda g: g.to_json(), self.groups),
      "all_running" : self.are_all_running(),
      "any_running" : self.are_any_running(),
      "all_created" : self.are_all_created(),
      "any_created" : self.are_any_created(),
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
		group = self.group(name)
		if group: group.provision(ctx)
		self.update(ctx)

	def killGroup(self, ctx, name):
		group = self.group(name)
		if group: group.kill(ctx)
		self.update(ctx)

	def destroyGroup(self, ctx, name):
		group = self.group(name)
		if group: group.destroy(ctx)
		self.update(ctx)

	def resizeGroup(self, ctx, name, size):
		group = self.group(name)
		if group: group.resize(ctx, size)
		self.update(ctx)

	def update(self, ctx):
		map(lambda group: group.update(ctx), self.groups)

	def are_all_running(self):
		return reduce(lambda memo, group: memo and group.are_all_running(), self.groups, True)

	def are_all_stopped(self):
		return reduce(lambda memo, group: memo and group.are_all_stopped(), self.groups, True)

	def are_all_created(self):
		return reduce(lambda memo, group: memo and group.are_all_created(), self.groups, True)

	def are_any_created(self):
		return reduce(lambda memo, group: memo or group.are_any_created(), self.groups, False)

	def are_any_running(self):
		return reduce(lambda memo, group: memo or group.are_any_running(), self.groups, False)

	def find_instance(self, name):
		for group in self.groups:
			for instance in group.instances:
				if instance.name == name: return instance
		return None

