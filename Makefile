SOURCES := $(wildcard *.ca)
DOTS := $(SOURCES:.ca=.dot)
DOTPNGS := $(SOURCES:.ca=.dot.png)
ASSEMBLIES := $(SOURCES:.ca=.s)
OBJECTS := $(SOURCES:.ca=.o)
BINARIES :=  $(SOURCES:%.ca=bin/%)

all: $(BINARIES) $(DOTPNGS) $(DOTS) $(ASSEMBLIES)

bin/%: %.o canada.o
	ld -e _start $+ -o $@

%.o: %.s
	nasm -o $@ -f macho $<

%.s: %.ca canadacodegen.py
	python3 canadacodegen.py $<

%.dot: %.ca canadaparse.py
	python3 canadaparse.py $<

%.dot.png: %.dot
	dot -Tpng -o $@ $<
