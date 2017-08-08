version := $(shell python -c 'from azurectl.version import __VERSION__; print(__VERSION__)')

all:
	python setup.py build
	${MAKE} -C doc/man all

flake8:
	flake8

install:
	python setup.py install
	tools/completion_generator > /etc/bash_completion.d/azurectl.sh
	${MAKE} -C doc/man install

.PHONY: test
test:
	cd test/unit && py.test --no-cov-on-fail --cov=azurectl --cov-report=term-missing --cov-fail-under=100

list_tests:
	@for i in test/unit/*_test.py; do basename $$i;done | sort

%.py:
	cd test/unit && py.test -s $@

.PHONY: completion
completion:
	mkdir -p completion && tools/completion_generator > completion/azurectl.sh

.PHONY: doc
doc:
	${MAKE} -C doc/man all

build: flake8 test completion doc
	rm -f dist/*
	# delete version information from setup.py for rpm package
	# we don't want to have this in the egg info because the rpm
	# package should handle package/version requirements
	cat setup.py | sed -e 's@>=[0-9.]*@@g' > setup.build.py
	python setup.build.py sdist
	mv dist/azurectl-${version}.tar.gz dist/python3-azurectl-${version}.tar.gz
	rm setup.build.py
	git log | tools/changelog_generator |\
		tools/changelog_descending > dist/python3-azurectl.changes
	cat package/spec-template | sed -e s'@%%VERSION@${version}@' \
		> dist/python3-azurectl.spec
	rm -rf dist/azurectl-${version}

pypi: clean test
	python setup.py sdist upload

clean:
	${MAKE} -C doc/man clean
	find -name *.pyc | xargs rm -f
	rm -rf azurectl.egg-info
	rm -rf build
	rm -rf dist

tar:
	# An easy way to generate a tarball that can be used for a local
	# package build. Builds targetd for release should always be created
	# with the build target
	rm -f dist/*
	cat setup.py | sed -e 's@>=[0-9.]*@@g' > setup.build.py
	python setup.build.py sdist
	mv dist/azurectl-${version}.tar.gz dist/python3-azurectl-${version}.tar.gz
	rm setup.build.py
