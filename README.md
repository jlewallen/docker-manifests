The Idea
========

The basic idea is a development VM that emulates a collection of cloud machines
for development. A single VM hosts a collection of Docker containers for
various services, and exposes them as individual machines to the local
network/developer machine. Docker containers for the following are planned:

* Apache Cassandra (N sized cluster and single node)
* Apache Tomcat
* netflix/eureka
  
I'd also like to see a web UI for starting/stopping/updating various services
and providing easy access to configuration. This will be especially important
once developers need to spin up instances of their own services from artifacts
in Nexus or elsewhere.

Host Setup
==========

You'll need to setup a bridge network device so that we can expose containers
on the same network with their own individual IPs. You can use either DHCP for
the host's network or a static address. Static may be easier because it'll
chang eon you less.

/etc/network/interfaces

	# Comment out the following:
	# The primary network interface
	#allow-hotplug eth0
	#iface eth0 inet dhcp

	auto br0
	iface br0 inet dhcp
        	bridge_ports eth0
        	bridge_fd 0
        	bridge_maxwait 0

	# uncomment the below and comment the above for static ip setup on the host
	#iface br0 inet static
	#       bridge_ports eth0
	#       bridge_fd 0
	#       address <host IP here, e.g. 192.168.1.20>
	#       netmask 255.255.255.0
	#       network <network IP here, e.g. 192.168.1.0>
	#       broadcast <broadcast IP here, e.g. 192.168.1.255>
	#       gateway <gateway IP address here, e.g. 192.168.1.1>
	#       # dns-* options are implemented by the resolvconf package, if installed
	#       dns-nameservers <name server IP address here, e.g. 192.168.1.1>
	#       dns-search your.search.domain.here

Make sure that the network interface on your VM has promiscuous mode enabled.

Running
=======
