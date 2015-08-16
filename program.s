                GLOBAL ?@print_int
                GLOBAL ?@main
                GLOBAL num
                GLOBAL ?@main
                SECTION .text
?@print_int:    push    ebp
                mov     ebp,esp
                sub     esp,16
                sub     esp,0
.while0:        pop     eax
                cmp     eax,0
                jz      .endwhile0
                jmp     .while0
.endwhile0:     add     esp,0
.if0:           pop     eax
                cmp     eax,0
                jz      .ifelse0
.ifelse0:       sub     esp,0
.while1:        pop     eax
                cmp     eax,0
                jz      .endwhile1
.if1:           pop     eax
                cmp     eax,0
                jz      .ifelse1
                jmp     .endwhile1
.ifelse1:       jmp     .while1
.endwhile1:     add     esp,0
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
                sub     esp,0
.while2:        pop     eax
                cmp     eax,0
                jz      .endwhile2
                jmp     .while2
.endwhile2:     add     esp,0
                add     esp,8
                push    0
.return:        pop     eax
                mov     esp,ebp
                pop     ebp
                pop     ebx
                add     esp,8
                jmp     ebx
                SECTION .data
num:            dw      5
