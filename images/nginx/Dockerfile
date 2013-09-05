FROM jlewallen/base

MAINTAINER Jacob Lewallen

RUN apt-get install -y nginx
ADD nginx-default /etc/nginx/sites-available/default

EXPOSE 80

CMD ["/usr/sbin/nginx", "-g", "daemon off;"]
