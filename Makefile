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
endif
ifndef OUTPUT_FORMAT
	$(error Unknown uname, define OUTPUT_FORMAT in Makefile)
endif

all: $(BINARIES) $(DOTPNGS) $(DOTS) $(ASSEMBLIES)

bin/factorial: print.o

bin/extern_test: print.o canada_c.o extern_test.o
	$(CC) -arch i386 $^ -o $@

bin/%: %.o canada.o
	ld -e _start $^ -o $@

%.o: %.s
	nasm -o $@ -f $(OUTPUT_FORMAT) $<

%.s: %.ca canadacodegen.py
	python3 canadacodegen.py $<

%.dot: %.ca canadaparse.py
	python3 canadaparse.py $<

%.dot.png: %.dot
	dot -Tpng -o $@ $<
