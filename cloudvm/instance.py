#
#
#

import random
import time
import string
import os
import re
import copy

from context import *

log = logging.getLogger('dock')

class Instance:
	def __init__(self, group_name, index, name):
		self.group_name = group_name
		self.index = index
		self.name = name
		self.image = None
		self.ports = None
		self.env = {}
		self.command = None
		self.short_id = None
		self.long_id = None
		self.assigned_ip = None
		self.configured_ip = None
		self.interface = None
		self.running = False
		self.created = False
		self.details = None

	@staticmethod
	def new_id(size=6, chars=string.ascii_uppercase + string.digits):
		return ''.join(random.choice(chars) for x in range(size))

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

	def make_params(self, group_type):
		env = dict((self.env.items() if self.env else []) + group_type.environment(self).items())
		log.info("%s: env %s" % (self.name, env))
		hostname = self.assigned_ip
		if not self.assigned_ip:
			hostname = Networking.get_offset_ip(0)
		params = {
			'image':        self.image,
			'ports':        self.ports,
			'environment':  list({ k + "=" + str(v) for k, v in env.items() }),
			'command':      self.command,
			'detach':       True,
			'hostname':     hostname
		}
		return params

	def needs_ip(self):
		return self.configured_ip is not None

	def configure(self, group_type, ctx):
		if self.needs_ip():
			self.interface = self.get_interface(ctx)
			self.assigned_ip = self.interface.ip
		else:
			self.interface = None
			self.assigned_ip = None
		ctx.update(self.group_name, self.name, self)

	def provision(self, group_type, ctx):
		docker = ctx.docker
		if self.exists(docker):
			if self.is_running(docker):
				log.info("%s: skipping, %s is running" % (self.name, self.short_id))
				return self.short_id
			else:
				log.info("%s: %s exists, starting" % (self.name, self.short_id))
				docker.start(self.short_id)
		else:
			log.info("%s: creating instance" % (self.name))
			params = self.make_params(group_type)
			container = docker.create_container(**params)
			self.short_id = container['Id']
			docker.start(self.short_id)
			log.info("%s: instance started %s" % (self.name, self.short_id))

		# this is all kinds of race condition prone, too bad we
		# can't do this before we start the container
		log.info("%s: configuring networking %s" % (self.name, self.short_id))
		self.update(ctx)
		if self.needs_ip():
			self.configure_networking(ctx)
		return self.short_id

	def has_host_mapping(self):
		if self.ports is None:
			return False
		for port in self.ports:
			if re.match(r"\d+:", port): return True
		return False

	def get_interface(self, ctx):
		if self.interface:
			return self.interface
		return ctx.networking.get_interface()

	def calculate_ip(self):
		configured = self.configured_ip
		m = re.match(r"^\+(\d+)", configured)
		if m:
			return Configuration.get_offset_ip(int(m.group(0)))
		return configured

	def configure_networking(self, ctx):
		if self.has_host_mapping():
			raise Exception("Host port mappings and IP configurations are mutually exclusive.")
		if self.interface:
			log.info("%s: assigning interface %s %s" % (self.name, self.interface.name, self.interface.ip))
			self.nspid = self.get_nspid(ctx)
			self.interface.assign(self, ctx)

	# poll for the file, it'll be created when the container starts
	# up and we should spend very little time waiting
	def get_nspid(self, ctx):
		while True:
			path = "/sys/fs/cgroup/devices/lxc/" + self.long_id + "/tasks"
			try:
				nspid = open(path, "r").readline().strip()
				if nspid: return nspid
			except IOError:
				log.info("%s: waiting for container %s cgroup" % (self.name, self.long_id))
				time.sleep(0.2)
				if not self.is_running(ctx.docker):
					log.info("%s: stopped, aborting" % (self.name))
					return None
		raise "Unable to get namespace PID"

	def stop(self, ctx):
		docker = ctx.docker
		if self.is_running(docker):
			log.info("%s: stopping %s" % (self.name, self.short_id))
			docker.stop(self.short_id)
			return self.short_id

	def kill(self, ctx):
		docker = ctx.docker
		if self.is_running(docker):
			log.info("%s: killing %s" % (self.name, self.short_id))
			docker.kill(self.short_id)
			return self.short_id

	def destroy(self, ctx):
		docker = ctx.docker
		if self.created:
			log.info("%s: destroying %s" % (self.name, self.short_id))
			docker.remove_container(self.short_id)
			return self.short_id

	def update(self, ctx):
		self.created = self.exists(ctx.docker)
		if self.created:
			details = ctx.docker.inspect_container(self.short_id)
			self.running = self.is_running(ctx.docker)
			self.details = details
			self.long_id = details['ID']
			self.started_at = details['State']['StartedAt']
			self.created_at = details['Created']
			self.docker_ip = details['NetworkSettings']['IPAddress']
			self.pid = details['State']['Pid']
		else:
			self.running = False
			self.details = None
			self.long_id = None
			self.short_id = None
			self.started_at = None
			self.created_at = None
			self.docker_ip = None
			self.pid = None
			self.assigned_ip = None

	def stop_url(self):
		return "/instances/%s/stop" % self.name

	def kill_url(self):
		return "/instances/%s/kill" % self.name

	def destroy_url(self):
		return "/instances/%s/destroy" % self.name

	def start_url(self):
		return "/instances/%s/start" % self.name

	def to_json(self):
		return {
			"name" : self.name,
			"short_id" : self.short_id,
			"long_id" : self.long_id,
			"ip" : self.assigned_ip,
			"docker_ip" : self.docker_ip,
			"running" : self.running,
			"created" : self.created,
			"created_at" : self.created_at,
			"started_at" : self.started_at,
			"pid" : self.pid,
			"details" : self.details,
			"start_url" : self.start_url(),
			"stop_url" : self.stop_url(),
			"destroy_url" : self.destroy_url(),
			"kill_url" : self.kill_url()
		}
