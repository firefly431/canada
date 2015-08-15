                SECTION .text
?@print_int:    push    ebp
                mov     ebp,esp
                sub     esp,16
                push    0
                pop     eax
                sub     esp,0
.while0:        push    0
                pop     eax
                cmp     eax,0
                jz      .endwhile0
                push    0
                pop     eax
                push    0
                pop     eax
                jmp     .while0
.endwhile0:     add     esp,0
.if0:           push    0
                pop     eax
                cmp     eax,0
                jz      .ifelse0
                push    0
                pop     eax
.ifelse0:       push    0
                pop     eax
                sub     esp,0
.while1:        push    0
                pop     eax
                cmp     eax,0
                jz      .endwhile1
                push    0
                pop     eax
                push    0
                pop     eax
                push    0
                pop     eax
.if1:           push    0
                pop     eax
                cmp     eax,0
                jz      .ifelse1
                jmp     .endwhile1
.ifelse1:       jmp     .while1
.endwhile1:     add     esp,0
                push    0
                pop     eax
                add     esp,16
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                add     esp,4
                jmp     ebx
?@main:         push    ebp
                mov     ebp,esp
                sub     esp,8
                push    0
                pop     eax
                push    0
                pop     eax
                sub     esp,0
.while2:        push    0
                pop     eax
                cmp     eax,0
                jz      .endwhile2
                push    0
                pop     eax
                push    0
                pop     eax
                jmp     .while2
.endwhile2:     add     esp,0
                push    0
                pop     eax
                add     esp,8
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                add     esp,8
                jmp     ebx
                SECTION .data
num:            dw      5
                GLOBAL ?@print_int
                GLOBAL ?@main
                GLOBAL num
                GLOBAL ?@main
