.PHONY: build-CrawlerFunction

build-CrawlerFunction:
	python -m pip install -r requirements-lambda.txt -t "$(ARTIFACTS_DIR)"
	mkdir -p "$(ARTIFACTS_DIR)/src" "$(ARTIFACTS_DIR)/utils" "$(ARTIFACTS_DIR)/certs"
	cp src/crawler.py "$(ARTIFACTS_DIR)/src/crawler.py"
	cp utils/*.py "$(ARTIFACTS_DIR)/utils/"
	cp certs/db-cacert.pem "$(ARTIFACTS_DIR)/certs/db-cacert.pem"
