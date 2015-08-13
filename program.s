                SECTION .text
?@print_int:    push    ebp
                mov     ebp,esp
                sub     esp,14
                add     esp,14
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                add     esp,4
                jmp     ebx
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,8
                add     esp,8
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                add     esp,0
                jmp     ebx
                SECTION .data
num:            dw      5
