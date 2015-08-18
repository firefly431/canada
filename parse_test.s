                GLOBAL ?@main
                SECTION .text
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,4
                mov     eax,-5
                cmp     eax,0
                setne   al
                movzx   eax,al
                push    eax
                mov     ebx,-5
                pop     eax
                sub     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp-4],eax
                add     esp,4
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
