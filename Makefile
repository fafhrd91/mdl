# Some simple testing tasks (sorry, UNIX only).

.install-deps: requirements-dev.txt
	@pip install -U -r requirements-dev.txt
	@touch .install-deps

flake: .flake

.flake: .install-deps $(shell find mdl -type f) \
                      $(shell find tests -type f)
	@flake8 mdl
	@if python -c "import sys; sys.exit(sys.version_info < (3,5))"; then \
	    flake8 tests && \
            python setup.py check -rms; \
	fi
	@touch .flake

.develop: .install-deps $(shell find mdl -type f) .flake
	@pip install -e .
	@touch .develop

test: .develop
	@pytest tests

vtest: .develop
	@pytest -v tests

cov cover coverage:
	tox

cov-dev: .develop
	@pytest --cov=mdl --cov-report=html --cov-report=term tests
	@echo "open file://`pwd`/coverage/index.html"

clean:
	@rm -rf `find . -name __pycache__`
	@rm -f `find . -type f -name '*.py[co]' `
	@rm -f `find . -type f -name '*~' `
	@rm -f `find . -type f -name '.*~' `
	@rm -f `find . -type f -name '@*' `
	@rm -f `find . -type f -name '#*#' `
	@rm -f `find . -type f -name '*.orig' `
	@rm -f `find . -type f -name '*.rej' `
	@rm -f .coverage
	@rm -rf coverage
	@rm -rf build
	@rm -rf cover
	@python setup.py clean
	@rm -rf .tox

install:
	@pip install -U pip
	@pip install -Ur requirements-dev.txt

.PHONY: all build flake test vtest cov clean doc
