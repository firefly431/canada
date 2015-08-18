all: program program2 program.dot.png program2.dot.png

program: program.o canada.o
	ld -e _start $+ -o $@

program2: program2.o canada.o
	ld -e _start $+ -o $@

%.o: %.s
	nasm -o $@ -f macho $<

%.s: %.samp canadacodegen.py
	python3 canadacodegen.py $<

%.dot: %.samp canadaparse.py
	python3 canadaparse.py $<

%.dot.png: %.dot
	dot -Tpng -o $@ $<
