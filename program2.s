                GLOBAL str
                GLOBAL ?@my_func
                GLOBAL ?@main
                SECTION .text
?@my_func:      push    ebp
                mov     ebp,esp
                sub     esp,4
.while0:        mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,5
                pop     eax
                cmp     eax,ebx
                setl    al
                movzx   eax,al
                cmp     eax,0
                jz      .endwhile0
                mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,1
                pop     eax
                add     eax,ebx
                push    eax
                pop     eax
                mov     dword[ebp+12],eax
                push    eax
                pop     eax
                mov     dword[ebp+8],eax
.if0:           mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,3
                pop     eax
                cmp     eax,ebx
                setl    al
                movzx   eax,al
                push    eax
                mov     eax,dword[ebp+8]
                push    eax
                mov     eax,8
                pop     ebx
                cmp     ebx,eax
                setle   bl
                movzx   ebx,bl
                pop     eax
                and     eax,ebx
                cmp     eax,0
                jz      .ifelse0
                jmp     .while0
.ifelse0:       jmp     .endwhile0
                mov     eax,dword[ebp+8]
                push    eax
                mov     ebx,dword[ebp+12]
                pop     eax
                cdq
                div     ebx
                mov     eax,eax
                push    eax
                pop     eax
                mov     dword[ebp-4],eax
                jmp     .while0
.endwhile0:     add     esp,4
                mov     eax,dword[ebp+8]
                push    eax
                jmp     .return
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                push    eax
                jmp     ebx
?@square:       push    ebp
                mov     ebp,esp
                mov     eax,dword[ebp+8]
                mov     al,byte[eax]
                movsx   eax,al
                push    eax
                mov     ebx,dword[ebp+8]
                mov     bl,byte[ebx]
                movsx   ebx,bl
                pop     eax
                imul    eax,ebx
                push    eax
                mov     ebx,dword[ebp+8]
                pop     eax
                movsx   eax,al
                mov     byte[ebx],al
                jmp     .return
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,4
                jmp     ebx
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,4
                push    8
                pop     eax
                mov     dword[ebp-4],eax
                lea     eax,[ebp-4]
                push    eax
                call    ?@square
                lea     eax,[test_array+3]
                push    eax
                call    ?@square
.if1:           mov     eax,1
                cmp     eax,0
                jz      .ifelse1
.if2:           mov     eax,1
                cmp     eax,0
                jz      .ifelse2
.ifelse2:
.ifelse1:       add     esp,4
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
test_array:     dd      1,2,3,4,53
useless:        dd      ??sl0,??sl1
str:            db      `abc`
foo:            dd      8
a:              db      `foobar`
b:              dd      1
??sl0:          db      `HELLO, WORLD!\n`
??sl1:          db      `\r\n\t \\\\\\`
