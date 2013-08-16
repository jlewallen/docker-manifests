import sys
import json
import random
import time
import subprocess
import os
import string
import iptools
import netifaces
import re
import pickle
import docker.client
import logging

from urlparse import urlparse

def new_id(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

class Context:
	def __init__(self, docker, cfg, state):
		self.docker = docker
		self.cfg = cfg
		self.state = state
		formatting = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
		logging.basicConfig(format = formatting, stream = sys.stdout, level = logging.INFO)
		self.log = logging.getLogger('dock')

	def info(self, m):
		self.log.info(m)

class HostMachine:
	def kill_all(self, ctx):
		for container in ctx.docker.containers():
			ctx.info("killing " + container['Id'])
			ctx.docker.kill(container['Id'])

	def delete_exited(self, ctx):
		for container in ctx.docker.containers(all = True):
			details = ctx.docker.inspect_container(container['Id'])
			if not details['State']['Running']:
				ctx.info("removing " + container['Id'])
				ctx.docker.remove_container(container['Id'])

	def delete_images(self, ctx):
		for image in ctx.docker.images():
			ctx.info("removing " + image['Id'])
			ctx.docker.remove_image(image['Id'])

	def to_json(self):
		return {
			"update_url" : "/host-machine/update",
			"kill_all_url" : "/host-machine/kill-all",
			"delete_exited" : "/host-machine/delete-exited",
			"delete_images" : "/host-machine/delete-images"
		}

class State:
	def __init__(self):
		self.containers = {}

	@staticmethod
	def load(path):
		if os.path.isfile(path):
			return pickle.load(open(path))
		return State()

	def update(self, long_id, instance):
		self.containers[long_id] = instance

	def get(self, long_id):
		return self.containers.get(long_id)

	def save(self, path):
		pickle.dump(self, open(path, "wb"))

class Configuration:
	def __init__(self):
		None

	@staticmethod
	def get_docker():
		docker_url = urlparse("http://127.0.0.1:4243")
		return docker.Client(base_url = docker_url.geturl())

	@staticmethod
	def get_local_ip():
		ips = []
		for interface in netifaces.interfaces():
			addresses = netifaces.ifaddresses(interface)
			if netifaces.AF_INET in addresses:
				for link in addresses[netifaces.AF_INET]:
					ips.append(link['addr'])
		for ip in ips:
			if re.match(r"^192.168", ip): return ip
		raise "Unable to infer IP"

	@staticmethod
	def get_offset_ip(offset):
		return iptools.ipv4.long2ip(iptools.ipv4.ip2long(Configuration.get_local_ip()) + offset)

class Instance:
	def __init__(self, name, cfg):
		self.name = name
		self.cfg = cfg
		self.short_id = self.cfg.get('container')
		self.long_id = None
		self.ip = None
		self.running = False
		self.created = False

	def exists(self, docker):
		if self.short_id is None:
			return False
		try:
			details = docker.inspect_container(self.short_id)
			return True
		except:
			return False
		
	def is_running(self, docker):
		if self.short_id is None:
			return False
		try:
			details = docker.inspect_container(self.short_id)
			return details["State"]["Running"]
		except:
			return False

	def make_params(self):
 		params = { 'image':        self.cfg['image'],
			   'ports':        self.cfg.get('ports'),
			   'environment':  self.cfg.get('env'),
			   'command':      self.cfg.get('command'),
			   'detach':       True,
			   'hostname':     self.name,
		          }
		return params

	def needs_ip(self):
		return self.cfg.get('ip') is not None

	def provision(self, ctx):
		docker = ctx.docker
		if self.exists(docker):
			if self.is_running(docker):
				ctx.info("%s: skipping, %s is running" % (self.name, self.short_id))
				return self.short_id
			else:
				ctx.info("%s: %s exists, starting" % (self.name, self.short_id))
				docker.start(self.short_id)
		else:
			ctx.info("%s: creating instance" % (self.name))
			params = self.make_params()
			container = docker.create_container(**params)
			self.short_id = container['Id']
			docker.start(self.short_id)
			self.cfg['container'] = self.short_id
			ctx.info("%s: instance started %s" % (self.name, self.short_id))

		# this is all kinds of race condition prone, too bad we
		# can't do this before we start the container
		ctx.info("%s: configuring networking %s" % (self.name, self.short_id))
		self.update(ctx)
		if self.needs_ip():
			if self.has_host_mapping():
				raise Exception("Host port mappings and IP configurations are mutually exclusive.")
			self.configure_networking(ctx, self.short_id, self.long_id, "br0", self.calculate_ip())
		ctx.state.update(self.long_id, self)
		return self.short_id

	def has_host_mapping(self):
		if self.cfg.get("ports") is None:
			return False
		for port in self.cfg.get("ports"):
			if re.match(r"\d+:", port): return True
		return False

	def calculate_ip(self):
		configured = self.cfg["ip"]
		m = re.match(r"^\+(\d+)", configured)
		if m:
			return Configuration.get_offset_ip(int(m.group(0)))
		return configured

	def configure_networking(self, ctx, short_id, long_id, bridge, ip):
		iface_suffix = new_id()
		iface_local_name = "pvnetl%s" % iface_suffix
		iface_remote_name = "pvnetr%s" % iface_suffix

		# poll for the file, it'll be created when the container starts
		# up and we should spend very little time waiting
		while True:
			try:
				npsid = open("/sys/fs/cgroup/devices/lxc/" + long_id + "/tasks", "r").readline().strip()
				break
			except IOError:
				ctx.info("%s: waiting for container %s cgroup" % (self.name, short_id))
				time.sleep(0.1)

		ctx.info("%s: configuring %s networking, assigning %s" % (self.name, short_id, ip))

		# strategy from unionize.sh
		commands = [
			"mkdir -p /var/run/netns",
			"rm -f /var/run/netns/%s" % long_id,
      "ln -s /proc/%s/ns/net /var/run/netns/%s" % (npsid, long_id),
      "ip link add name %s type veth peer name %s" % (iface_local_name, iface_remote_name),
      "brctl addif %s %s" % (bridge, iface_local_name),
      "ifconfig %s up" % (iface_local_name),
      "ip link set %s netns %s" % (iface_remote_name, npsid),
      "ip netns exec %s ip link set %s name eth1" % (long_id, iface_remote_name),
      "ip netns exec %s ifconfig eth1 %s" % (long_id, ip)
		]

		for command in commands:
			if os.system(command) != 0:
				raise Exception("Error configuring networking: '%s' failed!" % command)

		self.ip = ip

	def stop(self, ctx):
		docker = ctx.docker
		if self.is_running(docker):
			ctx.info("%s: stopping %s" % (self.name, self.short_id))
			docker.stop(self.short_id)
			return self.short_id

	def kill(self, ctx):
		docker = ctx.docker
		if self.is_running(docker):
			ctx.info("%s: killing %s" % (self.name, self.short_id))
			docker.kill(self.short_id)
			return self.short_id

	def destroy(self, ctx):
		docker = ctx.docker
		if self.created:
			ctx.info("%s: destroying %s" % (self.name, self.short_id))
			docker.remove_container(self.short_id)
			return self.short_id

	def update(self, ctx):
		self.created = self.exists(ctx.docker)
		if self.created:
			details = ctx.docker.inspect_container(self.short_id)
			self.long_id = details['ID']
			self.running = self.is_running(ctx.docker)
			self.started_at = details['State']['StartedAt']
			self.created_at = details['Created']
			self.pid = details['State']['Pid']
			if ctx.state.get(self.long_id):
				self.ip = ctx.state.get(self.long_id).ip
		else:
			self.cfg["container"] = None
			self.long_id = None
			self.short_id = None
			self.running = False
			self.started_at = None
			self.created_at = None
			self.pid = None
			self.ip = None

	def to_json(self):
		return {
			"name" : self.name,
			"short_id" : self.short_id,
			"long_id" : self.long_id,
			"ip" : self.ip,
			"running" : self.running,
			"created" : self.created,
			"created_at" : self.created_at,
			"started_at" : self.started_at,
			"pid" : self.pid,
			"start_url" : "/instances/%s/start" % self.name,
			"stop_url" : "/instances/%s/stop" % self.name,
			"destroy_url" : "/instances/%s/destroy" % self.name,
			"kill_url" : "/instances/%s/kill" % self.name
		}

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

class Manifest:
	def __init__(self, path):
		self.path = path
		self.cfg = json.load(open(self.path))
		self.groups = self.make_groups()

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

