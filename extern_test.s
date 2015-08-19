                GLOBAL ?@main
                EXTERN ?@print_int
                EXTERN _my_int
                EXTERN _puts
                EXTERN _printf
                SECTION .text
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,4
                mov     eax,dword[ebp+8]
                push    eax
                pop     eax
                mov     dword[ebp-4],eax
                mov     eax,dword[_my_int+0]
                push    eax
                call    ?@print_int
                mov     eax,esp
                and     esp,0fffffff0h
                sub     esp,8
                push    eax
                push    ??sl0
                call    _puts
                mov     esp,[esp+4]
.if0:           mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,2
                pop     eax
                cmp     eax,ebx
                jne     .ifelse0
                mov     eax,esp
                and     esp,0fffffff0h
                sub     esp,8
                push    eax
                push    ??sl1
                call    _puts
                mov     esp,[esp+4]
                jmp     .ifend0
.ifelse0:       mov     eax,esp
                and     esp,0fffffff0h
                sub     esp,4
                push    eax
                mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,1
                pop     eax
                sub     eax,ebx
                push    eax
                push    ??sl2
                call    _printf
                mov     esp,[esp+8]
.ifend0:
.while0:        mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,0
                pop     eax
                cmp     eax,ebx
                jle     .endwhile0
                mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,1
                pop     eax
                sub     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp+8],eax
                mov     eax,esp
                and     esp,0fffffff0h
                sub     esp,8
                push    eax
                mov     eax,dword[ebp+12]
                push    eax
                mov     eax,dword[ebp+8]
                push    eax
                mov     eax,4
                pop     ebx
                imul    ebx,eax
                pop     eax
                add     eax,ebx
                mov     eax,dword[eax]
                push    eax
                call    _puts
                mov     esp,[esp+4]
                jmp     .while0
.endwhile0:     mov     eax,dword[ebp-4]
                push    eax
                mov     ebx,1
                pop     eax
                sub     eax,ebx
                push    eax
                jmp     .return
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
??sl0:          db      `hello, world!\0`
??sl1:          db      `We have 1 argument.\0`
??sl2:          db      `We have %d arguments.\n\0`
