test: andbug/jdwp.so
	python setup.py test

andbug/jdwp.so: jdwp/jdwp.c
	python setup.py build_ext -i

jdwp/jdwp.c: jdwp/jdwp.pyx
	pyrexc jdwp/jdwp.pyx

clean:
	rm -rf build */*.o */*.so */*.pyc