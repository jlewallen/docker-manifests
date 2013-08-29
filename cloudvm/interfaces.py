#
#
#

import re
import iptools
import netifaces

class Interface:
	None

class InterfacePool:
	def __init__(self, log):
		None

class Networking:
	def __init__(self, log, state):
		self.log = log
		self.state = state
		self.log.info("local ip: %s" % Networking.get_local_ip())

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

	def allocate_ip(self):
		assigned = self.assigned_ips()
		for i in range(11, 255):
			ip = Networking.get_offset_ip(i)
			if ip not in assigned:
				return ip
		raise "No more IPs available"

