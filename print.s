                GLOBAL ?@print_int
                SECTION .text
?@print_int:    push    ebp
                mov     ebp,esp
                sub     esp,16
                push    0
                pop     eax
                mov     dword[ebp-16],eax
.if0:           mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,-2147483648
                pop     eax
                cmp     eax,ebx
                jne     .ifelse0
                push    12
                push    ??sl0
                push    1
                push    dword 0
                mov     eax,4
                int     80h
                add     esp,16
                push    eax
                jmp     .return
.ifelse0:
.if1:           mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,0
                pop     eax
                cmp     eax,ebx
                jge     .ifelse1
                push    45
                pop     eax
                movsx   eax,al
                mov     byte[ebp-3],al
                push    1
                lea     eax,[ebp-3]
                push    eax
                push    1
                push    dword 0
                mov     eax,4
                int     80h
                add     esp,16
                push    0
                mov     ebx,dword[ebp+8]
                pop     eax
                sub     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp+8],eax
.ifelse1:
.while0:        mov     eax,dword[ebp-16]
                push    eax
                mov     ebx,10
                pop     eax
                cmp     eax,ebx
                jge     .endwhile0
                push    0
                mov     ebx,dword[ebp-16]
                pop     eax
                movsx   eax,al
                mov     byte[ebp-12+ebx],al
                mov     eax,dword[ebp-16]
                push    eax
                mov     ebx,1
                pop     eax
                add     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp-16],eax
                jmp     .while0
.endwhile0:     push    9
                pop     eax
                mov     dword[ebp-16],eax
.while1:        mov     eax,dword[ebp-16]
                push    eax
                mov     ebx,0
                pop     eax
                cmp     eax,ebx
                jl      .endwhile1
                mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,10
                pop     eax
                cdq
                idiv    ebx
                mov     eax,edx
                push    eax
                mov     ebx,48
                pop     eax
                add     eax,ebx
                push    eax
                mov     ebx,dword[ebp-16]
                pop     eax
                movsx   eax,al
                mov     byte[ebp-12+ebx],al
                mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,10
                pop     eax
                cdq
                idiv    ebx
                mov     eax,eax
                push    eax
                pop     eax
                mov     dword[ebp+8],eax
                mov     eax,dword[ebp-16]
                push    eax
                mov     ebx,1
                pop     eax
                sub     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp-16],eax
.if2:           mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,0
                pop     eax
                cmp     eax,ebx
                jne     .ifelse2
                jmp     .endwhile1
.ifelse2:       jmp     .while1
.endwhile1:     push    9
                mov     ebx,dword[ebp-16]
                pop     eax
                sub     eax,ebx
                push    eax
                mov     eax,dword[ebp-16]
                push    eax
                mov     ebx,1
                pop     eax
                add     eax,ebx
                lea     eax,[ebp-12+eax]
                push    eax
                push    1
                push    dword 0
                mov     eax,4
                int     80h
                add     esp,16
                push    10
                pop     eax
                movsx   eax,al
                mov     byte[ebp-3],al
                push    1
                lea     eax,[ebp-3]
                push    eax
                push    1
                push    dword 0
                mov     eax,4
                int     80h
                add     esp,16
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,4
                jmp     ebx
                SECTION .data
??sl0:          db      `-2147483648\n`
