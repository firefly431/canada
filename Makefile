all: program program2

%: %.o canada.o
	ld -e _start $+ -o $@

%.o: %.s
	nasm -o $@ -f macho $<

%.s: %.samp canadacodegen.py
	python3 canadacodegen.py $<
