                GLOBAL str
                GLOBAL ?@my_func
                GLOBAL ?@main
                SECTION .text
?@my_func:      push    ebp
                mov     ebp,esp
                sub     esp,0
                sub     esp,4
.while0:        pop     eax
                cmp     eax,0
                jz      .endwhile0
.if0:           pop     eax
                cmp     eax,0
                jz      .ifelse0
                jmp     .while0
.ifelse0:       jmp     .endwhile0
                jmp     .while0
.endwhile0:     add     esp,4
                jmp     .return
                add     esp,0
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
                sub     esp,0
                jmp     .return
                add     esp,0
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
.if1:
.if2:
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
test_array:     dw      1,2,3,4,53
useless:        dw      ??sl0,??sl1
str:            db      'abc'
foo:            dw      8
a:              db      'foobar'
b:              dw      1
??sl0:          db      'HELLO, WORLD!\n'
??sl1:          db      '\r\n\t \\\\\\'
