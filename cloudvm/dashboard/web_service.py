#
#
#

from cloudvm.models import *

class WebService:
	def __init__(self):
		self.docker = Configuration.get_docker()
		self.ctx = Context(self.docker, None, State.load("dock.state"))
		self.manifest = Manifest.load("manifest-test.json")
		self.manifest.update(self.ctx)
		self.machine = HostMachine()

	def startManifest(self):
		self.manifest.provision(self.ctx)
		self.save()
		return self.to_status_json()

	def killManifest(self):
		self.manifest.kill(self.ctx)
		self.save()
		return self.to_status_json()

	def destroyManifest(self):
		self.manifest.destroy(self.ctx)
		self.save()
		return self.to_status_json()

	def startGroup(self, name):
		self.manifest.provisionGroup(self.ctx, name)
		self.save()
		return self.to_status_json()

	def killGroup(self, name):
		self.manifest.killGroup(self.ctx, name)
		self.save()
		return self.to_status_json()

	def destroyGroup(self, name):
		self.manifest.destroyGroup(self.ctx, name)
		self.save()
		return self.to_status_json()

	def resizeGroup(self, name, newSize):
		self.manifest.resizeGroup(self.ctx, name, newSize)
		self.save()
		return self.to_status_json()

	def save(self):
		self.manifest.save()
		self.ctx.state.save("dock.state")

	def to_status_json(self):
		return {
      'machine' : self.machine.to_json(),
      'manifest' : self.manifest.to_json()
		}
