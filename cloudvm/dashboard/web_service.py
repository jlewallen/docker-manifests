#
#
#

from cloudvm.models import *

class WebService:
	def __init__(self, options):
		self.docker = Context.get_docker()
		self.state = State.load(options.state_file_path)
		self.ctx = Context(self.docker, None, self.state)
		self.manifests = [Manifest.load(path, self.ctx, id) for id, path in enumerate(options.manifests)]
		self.machine = HostMachine()
		map(lambda manifest: manifest.update(self.ctx), self.manifests)
		self.ctx.state.purge(self.ctx)

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
