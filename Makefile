all:
	for a in base tomcat eureka nginx cassandra; do \
		(echo $$a && cd $$a && docker build -t jlewallen/$$a . ) ; \
	done
