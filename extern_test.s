                GLOBAL ?@main
                EXTERN ?@print_int
                EXTERN my_int
                SECTION .text
?@main:         push    ebp
                mov     ebp,esp
                mov     eax,dword[my_int+0]
                push    eax
                call    ?@print_int
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
