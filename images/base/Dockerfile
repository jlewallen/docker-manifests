from ubuntu

maintainer Jacob Lewallen

run apt-get install -y python-software-properties
run echo "deb http://archive.ubuntu.com/ubuntu precise main universe" > /etc/apt/sources.list
run add-apt-repository -y ppa:webupd8team/java
run apt-get update
run apt-get install -y vim wget curl tmux git 

run echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections && echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections
run apt-get install -y oracle-java7-installer

# https://gist.github.com/henrik-muehe/6155333
# RUN apt-get install libfuse2
# RUN cd /tmp ; apt-get download fuse
# RUN cd /tmp ; dpkg-deb -x fuse_* .
# RUN cd /tmp ; dpkg-deb -e fuse_*
# RUN cd /tmp ; rm fuse_*.deb
# RUN cd /tmp ; echo -en '#!/bin/bash\nexit 0\n' > DEBIAN/postinst
# RUN cd /tmp ; dpkg-deb -b . /fuse.deb
# RUN cd /tmp ; dpkg -i /fuse.deb
# RUN apt-get install -y openjdk-7-jdk nginx

run mkdir -p /opt
run cd /opt && wget http://apache.spinellicreations.com/tomcat/tomcat-7/v7.0.42/bin/apache-tomcat-7.0.42.tar.gz
run cd /opt && tar zxf apache-tomcat-*.tar.gz
run rm /opt/*.tar.gz
run mv /opt/apache-tomcat-* /opt/tomcat

