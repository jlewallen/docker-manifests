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

	def get_long_id(self, docker):
		if self.long_id: return self.long_id
		details = docker.inspect_container(self.short_id)
		self.long_id = details['ID']
		return self.long_id
	
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
			docker.start(short_id)
			self.cfg['container'] = short_id
			print "%s: instance started %s" % (self.name, short_id)

		# this is all kinds of race condition prone, too bad we
		# can't do this before we start the container
		print "%s: configuring networking %s" % (self.name, self.short_id)
		long_id = self.get_long_id(docker)
		self.configure_networking(self.short_id, long_id, "br0", self.calculate_ip())
		ctx.state.update(long_id, self)
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

class Group:
	def __init__(self, name, cfg):
		self.name = name
		self.cfg = cfg

	def apply(self, ctx, callback):
		for index, instance in enumerate(self.cfg):
			instance_name = "%s-%d" % (self.name, index)
			callback(Instance(instance_name, instance), ctx)
	
	def provision(self, ctx):
		self.apply(ctx, lambda instance, ctx: instance.provision(ctx))

	def stop(self, ctx):
		self.apply(ctx, lambda instance, ctx: instance.stop(ctx))
	
	def kill(self, ctx):
		self.apply(ctx, lambda instance, ctx: instance.kill(ctx))

class Manifest:
	def __init__(self, path):
		self.path = path
		self.cfg = json.load(open(self.path))

	def apply(self, ctx, callback):
		for name in self.cfg:
			callback(Group(name, self.cfg[name]), ctx)
	
	def provision(self, ctx):
		self.apply(ctx, lambda group, ctx: group.provision(ctx))

	def stop(self, ctx):
		self.apply(ctx, lambda group, ctx: group.stop(ctx))
	
	def kill(self, ctx):
		self.apply(ctx, lambda group, ctx: group.kill(ctx))
	
	def save(self):
		json.dump(self.cfg, open(self.path, "w"), sort_keys=True, indent=4, separators=(',', ': '))

