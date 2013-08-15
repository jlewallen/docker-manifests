all:
	docker pull ubuntu
	for a in base tomcat eureka nginx cassandra; do \
		(echo $$a && cd images/$$a && docker build -t jlewallen/$$a . ) ; \
	done
