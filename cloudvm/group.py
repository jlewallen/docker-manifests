#
#
#

from instance import *

log = logging.getLogger('dock')

class GroupType:
	def __init__(self, group):
		self.group = group

	def environment(self, instance):
		return {}

	@staticmethod
	def get(name):
		if name is None:
			return GroupType
		return eval(name.title())

class Cassandra(GroupType):
	def __init__(self, group):
		self.group = group

	def environment(self, instance):
		number = self.group.size()
		tokens = [((2**64 / number) * i) - 2**63 for i in range(number)]
		return {
			"CASS_SEEDS" : self.group.instances[0].assigned_ip,
			"CASS_TOKEN" : tokens[instance.index],
			"CASS_LOCAL_IP" : instance.assigned_ip,
			"CASS_NAME" : self.group.name
		}

class Group:
	def __init__(self, name, type_name, template):
		self.name = name
		self.type_name = type_name
		self.template = template
		self.instances = []

	def make_type(self):
		klass = GroupType.get(self.type_name)
		return klass(self)

	def size(self):
		return len(self.instances)

	def provision(self, ctx):
		map(lambda i: i.configure(self.make_type(), ctx), self.instances)
		map(lambda i: i.provision(self.make_type(), ctx), self.instances)

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

	def are_all_stopped(self):
		return not self.are_any_running()

	def resize(self, ctx, newSize):
		if newSize == 0: raise Exception("Can't remove all instances, just stop the group.")
		currentSize = len(self.instances)
		removed = []
		added = []
		log.info("resizing group %s oldSize=%d newSize=%d" % (self.name, currentSize, newSize))
		while currentSize != newSize:
			if currentSize < newSize:
				log.info("adding to group %s" % self.name)
				instance = self.new_instance(ctx)
				added.append(instance)
				self.instances.append(instance)
				# instance.configure(self.make_type(), ctx)
				# instance.provision(self.make_type(), ctx)
			else:
				log.info("removing from group %s" % self.name)
				instance = self.instances[currentSize - 1]
				removed.append(instance)
				self.instances.remove(instance)
				instance.kill(ctx)
				instance.destroy(ctx)
			currentSize = len(self.instances)

	def new_instance(self, ctx):
			index = len(self.instances)
			name = "%s-%d" % (self.name, index)
			saved = ctx.state.get(name)
			instance = Instance(self.name, index, name)
			if saved:
				instance.short_id = saved.short_id
				instance.assigned_ip = saved.assigned_ip
			instance.configured_ip = self.template.get("ip")
			instance.image = self.template["image"]
			instance.ports = self.template.get("ports")
			instance.env = self.template.get("env")
			instance.command = self.template.get("command")
			return instance

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

