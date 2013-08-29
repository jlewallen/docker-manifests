#
#
#

from cloudvm.models import *

class WebService:
	def __init__(self, options):
		self.docker = Configuration.get_docker()
		self.state = State.load(options.state_file_path)
		self.ctx = Context(self.docker, None, self.state)
		self.manifests = map(lambda path: Manifest.load(path, self.ctx), options.manifests)
		self.machine = HostMachine()
		map(lambda manifest: manifest.update(self.ctx), self.manifests)
		self.ctx.state.purge(self.ctx)

	def startManifest(self):
		map(lambda manifest: manifest.provision(self.ctx), self.manifests)
		self.save()
		return self.to_status_json()

	def killManifest(self):
		map(lambda manifest: manifest.kill(self.ctx), self.manifests)
		self.save()
		return self.to_status_json()

	def destroyManifest(self):
		map(lambda manifest: manifest.destroy(self.ctx), self.manifests)
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

	def to_status_json(self):
		return {
      'machine' : self.machine.to_json(),
      'manifests' : map(lambda manifest: manifest.to_json(), self.manifests),
			'can_kill' : reduce(lambda value, manifest: value or manifest.are_any_running(), self.manifests, False),
			'can_destroy' : reduce(lambda value, manifest: value and manifest.are_all_stopped(), self.manifests, True),
			"start_url" : "/manifests/0/start",
			"kill_url" : "/manifests/0/kill",
			"destroy_url" : "/manifests/0/destroy"
		}
