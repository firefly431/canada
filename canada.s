; extremely simple wrapper that defines _start

; let nasm know we need the main function
EXTERN ?@main

SECTION .text
GLOBAL _start
_start:
        ; arguments to main: argc, argv
        ; so we should push argv then argc
        ; but argc is already on stack so pop it first
        pop eax ; into a temp register
        push esp ; then push the address of the first variable
        ; luckily the arguments are backwards so it's consistent
        ; with positive pointer offsets
        push eax ; push argc again
        ; then we're ready to call main
        call ?@main
        ; now exit if we returned without exiting
        ; the code below works for both linux and bsd
        ; bsd requires parameters on stack
        push 0 ; 0 exit code
        push 0 ; emulate call/ret
        mov eax, 1 ; both
        mov ebx, 0 ; linux 0 exit code
        int 80h
