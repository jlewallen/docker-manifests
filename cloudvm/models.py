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

def new_id(size=6, chars=string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for x in range(size))

class Configuration:
	def __init__(self):
		self.cfg = json.load(open('settings.json'))

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

	def short_id(self):
		return self.cfg.get('container')

	def exists(self, docker):
		if self.short_id() is None:
			return False
		try:
			details = docker.inspect_container(self.short_id())
			return True
		except:
			return False
		
	def is_running(self, docker):
		if self.short_id() is None:
			return False
		try:
			details = docker.inspect_container(self.short_id())
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

	def long_id(self, docker):
		details = docker.inspect_container(self.short_id())
		return details['ID']
	
	def provision(self, docker):
		if self.exists(docker):
			if self.is_running(docker):
				print "%s: skipping, %s is running" % (self.name, self.short_id())
				return self.short_id()
			else:
				print "%s: %s exists, starting" % (self.name, self.short_id())
				docker.start(self.short_id())
		else:
			print "%s: creating instance" % (self.name)
			container = docker.create_container(**self.make_params())
			short_id = container['Id']
			docker.start(short_id)
			self.cfg['container'] = short_id
			print "%s: instance started %s" % (self.name, short_id)

		# this is all kinds of race condition prone, too bad we
		# can't do this before we start the container
		print "%s: configuring networking %s" % (self.name, self.short_id())
		self.configure_networking(self.short_id(), self.long_id(docker), "br0", self.calculate_ip())
		return self.short_id()

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

	def stop(self, docker):
		if self.is_running(docker):
			print "%s: stopping %s" % (self.name, self.short_id())
			docker.stop(self.short_id())
			return self.short_id()

	def kill(self, docker):
		if self.is_running(docker):
			print "%s: killing %s" % (self.name, self.short_id())
			docker.kill(self.short_id())
			return self.short_id()

class Manifest:
	def __init__(self, path):
		self.path = path
		self.cfg = json.load(open(self.path))

	def apply(self, docker, callback):
		for name in self.cfg:
			for index, instance in enumerate(self.cfg[name]):
				instance_name = "%s-%d" % (name, index)
				callback(Instance(instance_name, instance), docker)
	
	def provision(self, docker):
		self.apply(docker, lambda instance, docker: instance.provision(docker))

	def stop(self, docker):
		self.apply(docker, lambda instance, docker: instance.stop(docker))
	
	def kill(self, docker):
		self.apply(docker, lambda instance, docker: instance.kill(docker))
	
	def save(self):
		json.dump(self.cfg, open(self.path, "w"), sort_keys=True, indent=4, separators=(',', ': '))

