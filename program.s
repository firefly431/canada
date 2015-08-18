                GLOBAL ?@print_int
                GLOBAL ?@main
                GLOBAL num
                GLOBAL ?@main
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
                ne      .ifelse0
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
                ge      .ifelse1
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
                ge      .endwhile0
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
                l       .endwhile1
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
                ne      .ifelse2
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
                add     esp,16
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,4
                jmp     ebx
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,8
                push    1
                pop     eax
                mov     dword[ebp-8],eax
                push    1
                pop     eax
                mov     dword[ebp-4],eax
.while2:        mov     eax,dword[ebp-4]
                push    eax
                mov     ebx,dword[num+0]
                pop     eax
                cmp     eax,ebx
                g       .endwhile2
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
                jmp     .while2
.endwhile2:     mov     eax,dword[ebp-8]
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
                add     esp,8
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
num:            dd      5
??sl0:          db      `-2147483648\n`
