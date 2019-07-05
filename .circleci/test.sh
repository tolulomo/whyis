#!/bin/bash
mkdir -p test-results/python

docker run whyis bash -c "source venv/bin/activate && python manage.py test --ci &>/dev/null && cat test-results/python/results.xml" >test-results/python/results.xml

cat test-results/python/results.xml

if [ "$(grep -c "failure " schemas.txt)" -ge 3 ]; then
    exit 1
else
    exit 0
fi
