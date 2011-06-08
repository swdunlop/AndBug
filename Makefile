test: lib/andbug/jdwp.so
	PYTHONPATH=lib python setup.py test

lib/andbug/jdwp.so: lib/jdwp/jdwp.c
	python setup.py build_ext -i

lib/jdwp/jdwp.c: lib/jdwp/jdwp.pyx
	pyrexc lib/jdwp/jdwp.pyx

clean:
	rm -rf build */*/*.o */*/*.so */*/*.pyc

lint:
	for x in `find lib -name '*.py'`; do echo :: $$x; PYTHONPATH=lib pylint --rcfile=pylint.rc $$x; done
