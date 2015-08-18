                GLOBAL ?@main
                EXTERN ?@print_int
                EXTERN my_int
                EXTERN _puts
                SECTION .text
?@main:         push    ebp
                mov     ebp,esp
                mov     eax,dword[my_int+0]
                push    eax
                call    ?@print_int
                mov     eax,esp
                and     esp,0fffffff0h
                sub     esp,8
                push    eax
                push    ??sl0
                call    _puts
                mov     esp,[esp+4]
                mov     eax,dword[ebp+8]
                push    eax
                call    ?@print_int
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
                mov     eax,dword[ebp+8]
                mov     eax,dword[ebp+12+eax]
                push    eax
                call    _puts
                mov     esp,[esp+4]
                jmp     .while0
.endwhile0:     push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
??sl0:          db      `hello, world!`
