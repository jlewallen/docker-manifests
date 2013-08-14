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

from urlparse import urlparse

def new_id(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

class Context:
	def __init__(self, docker, cfg, state):
		self.docker = docker
		self.cfg = cfg
		self.state = state

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
 		return { 'image':        self.cfg['image'],
			 'command':      self.cfg.get('command'),
			 'ports':        self.cfg.get('ports'),
			 'environment':  self.cfg.get('env'),
			 'detach':       True,
			 'hostname':     self.name,
		        }

	def provision(self, ctx):
		docker = ctx.docker
		if self.exists(docker):
			if self.is_running(docker):
				print "%s: skipping, %s is running" % (self.name, self.short_id)
				return self.short_id
			else:
				print "%s: %s exists, starting" % (self.name, self.short_id)
				docker.start(self.short_id)
		else:
			print "%s: creating instance" % (self.name)
			container = docker.create_container(**self.make_params())
			self.short_id = container['Id']
			docker.start(self.short_id)
			self.cfg['container'] = self.short_id
			print "%s: instance started %s" % (self.name, self.short_id)

		# this is all kinds of race condition prone, too bad we
		# can't do this before we start the container
		print "%s: configuring networking %s" % (self.name, self.short_id)
		self.update(ctx)
		self.configure_networking(self.short_id, self.long_id, "br0", self.calculate_ip())
		ctx.state.update(self.long_id, self)
		return self.short_id

	def calculate_ip(self):
		configured = self.cfg["ip"]
		m = re.match(r"^\+(\d+)", configured)
		if m:
			return Configuration.get_offset_ip(int(m.group(0)))
		return configured

	def configure_networking(self, short_id, long_id, bridge, ip):
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
				print "%s: waiting for container %s cgroup" % (self.name, short_id)
				time.sleep(0.1)

		print "%s: configuring %s networking, assigning %s" % (self.name, short_id, ip)

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

	def stop(self, ctx):
		docker = ctx.docker
		if self.is_running(docker):
			print "%s: stopping %s" % (self.name, self.short_id)
			docker.stop(self.short_id)
			return self.short_id

	def kill(self, ctx):
		docker = ctx.docker
		if self.is_running(docker):
			print "%s: killing %s" % (self.name, self.short_id)
			docker.kill(self.short_id)
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
		else:
			self.cfg["container"] = None
			self.long_id = None
			self.short_id = None
			self.running = False

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
			"pid" : self.pid
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
	
	def update(self, ctx):
		map(lambda i: i.update(ctx), self.instances)

	def to_json(self):
		return {
			"name" : self.name,
			"resize_url" : "",
			"stop_url" : "",
			"start_url" : "",
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
		return { 'groups' : map(lambda g: g.to_json(), self.groups) }

	def provision(self, ctx):
		self.update(ctx)
		map(lambda group: group.provision(ctx), self.groups)

	def stop(self, ctx):
		self.update(ctx)
		map(lambda group: group.stop(ctx), self.groups)
	
	def kill(self, ctx):
		self.update(ctx)
		map(lambda group: group.kill(ctx), self.groups)
	
	def update(self, ctx):
		map(lambda group: group.update(ctx), self.groups)
	
	def save(self):
		json.dump(self.cfg, open(self.path, "w"), sort_keys=True, indent=4, separators=(',', ': '))

	def find_instance(self, name):
		for group in self.groups:
			for instance in group.instances:
				if instance.name == name: return instance
		return None

