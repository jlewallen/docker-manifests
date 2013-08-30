#
#
#

import re
import os
import sys
import time
import iptools
import netifaces
import logging

from collections import deque

log = logging.getLogger('dock')

class Interface:
	def __init__(self, name, ip):
		self.name = name
		self.local_name = "l%s" % self.name
		self.remote_name = "r%s" % self.name
		self.ip = ip

	def _destroy(self):
		if self.local_name in netifaces.interfaces():
			log.info("%s: deleting" % self.name)
			self._execute("ip link delete %s" % (self.local_name))

	def _create(self):
		bridge = "br0"
		if not bridge in netifaces.interfaces(): raise "No bridge: " + bridge
		commands = [
			"ip link add name %s type veth peer name %s" % (self.local_name, self.remote_name),
			"brctl addif %s %s" % (bridge, self.local_name),
			"ifconfig %s up" % (self.local_name),
		]
		log.info("%s: creating" % self.name)
		map(lambda command: os.system(command), commands)

	def assign(self, instance, ctx):
		self._destroy()
		self._create()
		netns = instance.long_id
		nspid = instance.nspid
		commands = [
			"mkdir -p /var/run/netns",
			"rm -f /var/run/netns/%s" % netns,
      "ln -s /proc/%s/ns/net /var/run/netns/%s" % (nspid, netns),
      "ip link set %s netns %s" % (self.remote_name, nspid),
      "ip netns exec %s ip link set %s name eth1" % (netns, self.remote_name),
      "ip netns exec %s ifconfig eth1 %s" % (netns, self.ip)
		]
		map(lambda command: self._execute(command), commands)

	def _execute(self, command):
		for i in range(0, 5):
			if os.system(command) != 0:
				time.sleep(1)
			else:
				return True
		raise Exception("Error configuring networking: '%s' failed!" % command)

class InterfacePool:
	def __init__(self, size):
		self.ifaces = deque([])

	def _new_interface(self):
		return Interface("dock%d" % len(self.ifaces), Networking.get_offset_ip(len(self.ifaces) + 1))

	def get_by_ip(self, ip):
		for iface in self.ifaces:
			if iface.ip == ip:
				return iface
		None

	def get(self):
		interface = self._new_interface()
		self.ifaces.append(interface)
		return interface

	def release(self, interface):
		None

class Networking:
	def __init__(self, state):
		self.state = state
		self.ifaces = InterfacePool(6)
		log.info("local ip: %s" % Networking.get_local_ip())

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
		return iptools.ipv4.long2ip(iptools.ipv4.ip2long(Networking.get_local_ip()) + offset)

	def assigned_ips(self):
		ips = []
		for name in self.state.containers:
			instance = self.state.containers[name]
			if instance.assigned_ip:
				ips.append(instance.assigned_ip)
		return ips

	def get_interface(self):
		interface = self.ifaces.get()
		return interface

def main():
	formatting = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
	logging.basicConfig(format = formatting, stream = sys.stdout, level = logging.INFO)
	pool = InterfacePool(logging.getLogger('dock'), 6)

if __name__ == "__main__":
	main()
