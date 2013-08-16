from instance import *

class Group:
	def __init__(self, name, cfg):
		self.name = name
		self.cfg = cfg
		self.instances = self.make_instances()

	def make_instances(self):
		instances = []
		for index, instance in enumerate(self.cfg):
			instances.append(Instance("%s-%d" % (self.name, index), instance))
		return instances
		
	def provision(self, ctx):
		map(lambda i: i.provision(ctx), self.instances)

	def stop(self, ctx):
		map(lambda i: i.stop(ctx), self.instances)
	
	def kill(self, ctx):
		map(lambda i: i.kill(ctx), self.instances)
	
	def destroy(self, ctx):
		map(lambda i: i.destroy(ctx), self.instances)
	
	def update(self, ctx):
		map(lambda i: i.update(ctx), self.instances)

	def are_all_created(self):
		for instance in self.instances:
			if not instance.created: return False
		return True

	def are_any_created(self):
		for instance in self.instances:
			if instance.created: return True
		return False

	def are_all_running(self):
		for instance in self.instances:
			if not instance.running: return False
		return True

	def are_any_running(self):
		for instance in self.instances:
			if instance.running: return True
		return False

	def resize(self, ctx, newSize):
		if newSize == 0: raise Exception("Can't remove all instances, just stop the group.")
		currentSize = len(self.instances)
		ctx.info("resizing group %s oldSize=%d newSize=%d" % (self.name, currentSize, newSize))
		while currentSize != newSize:
			if currentSize < newSize:
				ctx.info("adding to group %s" % self.name)
				self.instances.append(self.instances[0])
			else:
				ctx.info("removing from group %s" % self.name)
				self.instances.remove(self.instances[currentSize - 1])
			currentSize = len(self.instances)
		print self.instances

	def to_json(self):
		return {
			"name" : self.name,
			"resize_url" : "/groups/%s/resize" % self.name,
			"start_url" : "/groups/%s/start" % self.name,
			"stop_url" : "/groups/%s/stop" % self.name,
			"kill_url" : "/groups/%s/kill" % self.name,
			"destroy_url" : "/groups/%s/destroy" % self.name,
      "all_running" : self.are_all_running(),
      "any_running" : self.are_any_running(),
      "all_created" : self.are_all_created(),
      "any_created" : self.are_any_created(),
			"can_kill" : self.are_any_running(),
			"can_destroy" : self.are_any_created() and not self.are_any_running(),
			"instances" : map(lambda i: i.to_json(), self.instances)
		}

