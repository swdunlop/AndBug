PYTHON_VER ?= 2
PYTHON_CONFIG ?= python$(PYTHON_VER)-config
PYTHON_CFLAGS ?= $(shell $(PYTHON_CONFIG) --cflags) 
PYTHON_LIBS ?= $(shell $(PYTHON_CONFIG) --libs)
CFLAGS += -fPIC

all: pyjdwp.so

clean:
	rm -f *.o *.so

pyjdwp.c: pyjdwp.pyx
	pyrexc $<

pyjdwp.so: pyjdwp.o jdwp_wire.o
	$(CC) -shared -o $@ $(PYTHON_LIBS) $(LIBS) pyjdwp.o jdwp_wire.o
		
%.o: %.c
	$(CC) $(CPPFLAGS) $(CFLAGS) $(PYTHON_CFLAGS) -c $< 
