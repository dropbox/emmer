.PHONY: test clean

test:
	python tests/__init__.py

clean:
	rm *.pyc emmer/*.pyc tests/*.pyc
