from jlewallen/base

maintainer Jacob Lewallen

run apt-get install -y nginx
add nginx-default /etc/nginx/sites-available/default

expose 80

entrypoint ["/usr/sbin/nginx"]
cmd ["-g", "daemon off;"]
