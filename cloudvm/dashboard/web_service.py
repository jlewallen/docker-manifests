#
#
#

import os

from jinja2 import Template
from cloudvm.models import *

class MetaFile:
	def __init__(self, path):
		self.path = path

	def generate(self, group, instance):
		template = Template(open(self.path).read())
		data = {
			"machine" : {
				"ip" : Networking.get_local_ip()
			}
		}
		rendered = "# " + self.path + "\n"
		rendered += template.render(data)
		return rendered

class MetaFiles:
	def serve(self, group, instance, path):
		files = []
		for full_path in self._paths_for(group.name, instance.name, path):
			if os.path.exists(full_path):
				files.append(MetaFile(full_path))
		merged = ""
		for file in files:
			merged += file.generate(group, instance)
		return merged

	def _paths_for(self, group_name, instance_name, path):
		return [
			"meta/%s" % (path),
			"meta/%s/%s" % (group_name, path),
			"meta/%s/%s/%s" % (group_name, instance_name, path)
		]

class Lookup:
	def __init__(self, manifests):
		self.manifests = manifests

	def instance(self, name_or_ip):
		for manifest in self.manifests:
			for group in manifest.groups:
				for instance in group.instances:
					if name_or_ip in [ instance.name, instance.docker_ip, instance.assigned_ip ]:
						return instance
		raise Exception("No instance found using '%s'" % name_or_ip)

	def group_for_instance(self, instance):
		for manifest in self.manifests:
			for group in manifest.groups:
				if instance in group.instances: return group
		raise Exception("No group found for %s" % instance.name)

	def group_for(self, name):
		for manifest in self.manifests:
			for group in manifest.groups:
				names = map(lambda i: i.name, group.instances)
				if name in names: return group
		raise "No group found for %s" % name

class WebService:
	def __init__(self, options):
		self.docker = Context.get_docker()
		self.state = State.load(options.state_file_path)
		self.ctx = Context(self.docker, None, self.state)
		self.manifests = [Manifest.fromFile(path, self.ctx, id) for id, path in enumerate(options.manifests)]
		self.machine = HostMachine()
		self.update()
		self.ctx.state.purge(self.ctx)

	def update(self):
		map(lambda manifest: manifest.update(self.ctx), self.manifests)

	def lookup(self):
		return Lookup(self.manifests)

	def instanceEnv(self, instance_name, path):
		instance = self.lookup().instance(instance_name)
		group = self.lookup().group_for_instance(instance)
		return MetaFiles().serve(group, instance, path)

	def manifest(self, id):
		return self.manifests[id]

	def recreateAll(self):
		steps = [manifest.kill_url() for manifest in self.manifests] + [manifest.destroy_url() for manifest in self.manifests] + [manifest.start_url() for manifest in self.manifests]
		return { "steps" : steps }

	def startManifests(self):
		map(lambda manifest: manifest.provision(self.ctx), self.manifests)
		self.save()
		return self.to_status_json()

	def killManifests(self):
		map(lambda manifest: manifest.kill(self.ctx), self.manifests)
		self.save()
		return self.to_status_json()

	def destroyManifests(self):
		map(lambda manifest: manifest.destroy(self.ctx), self.manifests)
		self.save()
		return self.to_status_json()

	def startManifest(self, id):
		self.manifest(id).provision(self.ctx)
		self.save()
		return self.to_status_json()

	def killManifest(self, id):
		self.manifest(id).kill(self.ctx)
		self.save()
		return self.to_status_json()

	def destroyManifest(self, id):
		self.manifest(id).destroy(self.ctx)
		self.save()
		return self.to_status_json()

	def startGroup(self, name):
		map(lambda manifest: manifest.provisionGroup(self.ctx, name), self.manifests)
		self.save()
		return self.to_status_json()

	def killGroup(self, name):
		map(lambda manifest: manifest.killGroup(self.ctx, name), self.manifests)
		self.save()
		return self.to_status_json()

	def destroyGroup(self, name):
		map(lambda manifest: manifest.destroyGroup(self.ctx, name), self.manifests)
		self.save()
		return self.to_status_json()

	def resizeGroup(self, name, newSize):
		map(lambda manifest: manifest.resizeGroup(self.ctx, name, newSize), self.manifests)
		self.save()
		return self.to_status_json()

	def start(self):
		self.ctx.reload()
		self.update()
		self.ctx.state.purge(self.ctx)

	def save(self):
		self.ctx.state.purge(self.ctx)
		self.ctx.save()

	def instanceLogs(self, name):
		for manifest in self.manifests:
			for group in manifest.groups:
				for instance in group.instances:
					if instance.name == name:
						return self.ctx.docker.logs(instance.short_id)
		raise "No such instance"

	def addManifest(self, name, json):
		self.manifests.append(Manifest.fromJson(name, json, self.ctx, len(self.manifests)))
		self.ctx.reload()
		self.update()
		self.save()
		return self.to_status_json()

	def clearManifests(self):
		self.manifests = []
		self.ctx.reload()
		self.update()
		self.save()
		return self.to_status_json()

	def are_all_stopped(self):
		return reduce(lambda value, manifest: value and manifest.are_all_stopped(), self.manifests, True)

	def are_any_created(self):
		return reduce(lambda value, manifest: value or manifest.are_any_created(), self.manifests, False)

	def are_any_running(self):
		return reduce(lambda value, manifest: value or manifest.are_any_running(), self.manifests, False)

	def to_status_json(self):
		return {
      'machine' : self.machine.to_json(),
      'manifests' : map(lambda manifest: manifest.to_json(), self.manifests),
			'can_kill' : self.are_any_running(),
			'can_destroy' :  self.are_all_stopped() and self.are_any_created(),
			"start_url" : "/manifests/start",
			"kill_url" : "/manifests/kill",
			"destroy_url" : "/manifests/destroy"
		}
