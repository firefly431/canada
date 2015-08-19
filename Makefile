SOURCES := $(wildcard *.ca)
DOTS := $(SOURCES:.ca=.dot)
DOTPNGS := $(SOURCES:.ca=.dot.png)
ASSEMBLIES := $(SOURCES:.ca=.s)
OBJECTS := $(SOURCES:.ca=.o)
BINARIES := bin/factorial bin/parse_test bin/extern_test

ifeq ($(shell uname -s),Linux)
	OUTPUT_FORMAT := elf
endif
ifeq ($(shell uname -s),FreeBSD)
	OUTPUT_FORMAT := elf
endif
ifeq ($(shell uname -s),Darwin)
	OUTPUT_FORMAT := macho
	LDFLAGS := -macosx_version_min 10.6
endif
ifndef OUTPUT_FORMAT
	$(error Unknown uname, define OUTPUT_FORMAT in Makefile)
endif

all: $(BINARIES) $(DOTPNGS) $(ASSEMBLIES)

bin/factorial: print.o

bin/extern_test: print.o canada_c.o extern_test.o extern_c.c
	$(CC) -arch i386 $^ -o $@

bin/%: %.o canada.o
	ld $(LDFLAGS) -e _start $^ -o $@

%.o: %.s
	nasm -o $@ -f $(OUTPUT_FORMAT) $<

%.s: %.ca canadacodegen.py
	python3 canadacodegen.py $<

%.dot: %.ca canadaparse.py
	python3 canadaparse.py $<

%.dot.png: %.dot
	dot -Tpng -o $@ $<

clean:
	rm -f $(OBJECTS) $(ASSEMBLIES) $(BINARIES) $(DOTS) $(DOTPNGS)

.PHONY: clean
