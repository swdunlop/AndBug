# defense against platforms where python == python3 

PYTHON ?= python
PYREXC ?= pyrexc 
PYLINT ?= pylint

test: lib/andbug/jdwp.so
	PYTHONPATH=lib python2 setup.py test

lib/andbug/jdwp.so: lib/jdwp/jdwp.c
	$(PYTHON) setup.py build_ext -i

lib/jdwp/jdwp.c: lib/jdwp/jdwp.pyx
	$(PYREXC) lib/jdwp/jdwp.pyx

clean:
	rm -rf build */*/*.o */*/*.so */*/*.pyc

lint:
	for x in `find lib -name '*.py'`; do echo :: $$x; PYTHONPATH=lib $(PYLINT) --rcfile=pylint.rc $$x; done
