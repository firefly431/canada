                GLOBAL num
                GLOBAL ?@main
                EXTERN ?@print_int
                SECTION .text
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,8
                push    1
                pop     eax
                mov     dword[ebp-8],eax
                push    1
                pop     eax
                mov     dword[ebp-4],eax
.while0:        mov     eax,dword[ebp-4]
                push    eax
                mov     ebx,dword[num+0]
                pop     eax
                cmp     eax,ebx
                jg      .endwhile0
                mov     eax,dword[ebp-8]
                push    eax
                mov     ebx,dword[ebp-4]
                pop     eax
                imul    eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp-8],eax
                mov     eax,dword[ebp-4]
                push    eax
                mov     ebx,1
                pop     eax
                add     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp-4],eax
                jmp     .while0
.endwhile0:     mov     eax,dword[ebp-8]
                push    eax
                call    ?@print_int
                push    -10
                call    ?@print_int
                push    0
                call    ?@print_int
                push    2147483647
                call    ?@print_int
                push    -2147483648
                call    ?@print_int
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
num:            dd      5
