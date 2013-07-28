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

Running
=======
