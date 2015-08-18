; wrapper for linking with libc
; you might need to remove the underscore if you're not
; on mac
GLOBAL _main
EXTERN ?@main
_main:
    jmp ?@main
