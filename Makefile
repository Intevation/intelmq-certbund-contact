.PHONY: tests lint

tests:
	PYTHONPATH=. pytest tests/

lint:
	# Python syntax errors or undefined names
	flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	# exit-zero treats all errors as warnings
	flake8 . --count --exit-zero --max-complexity=10 --statistics
	git ls-files '*.py' | xargs pylint
