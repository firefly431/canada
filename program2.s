                SECTION .text
                SECTION .data
test_array:     dw      1,2,3,4,53
useless:        dw      sl0,sl1
str:            db      'abc'
foo:            dw      8
a:              db      'foobar'
b:              dw      1
sl0:            db      'HELLO, WORLD!\n'
sl1:            db      '\r\n\t \\\\\\'
