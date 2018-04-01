.PHONY: test publish publish-test clean build

test: 
	bash tests/test.sh


README: README.md
	pandoc --from=markdown --to=rst --output=README README.md


build: test README
	python setup.py build sdist
	python setup.py test

publish: build README
	python setup.py sdist upload
	rm -fr build dist .egg roro_ioc.egg-info


publish-test: build README
	python setup.py sdist upload -r pypitest  
	rm -fr build dist .egg roro_ioc.egg-info 

clean:
	rm -fr build dist .egg roro_ioc.egg-info README

