Stack Frame Description
=======================

Function Stack Frame
--------------------
Before:

    ... <- ebp
    arg3
    arg2
    arg1 <- esp

During:

    ...
    arg3
    arg2
    arg1
    eip
    ebp <- ebp
    var1
    var2
    var3 <- esp

After:

    ... <- ebp
    ret <- esp

Function Calling Convention
---------------------------

###To call a function `myfunc`:

1. Push the arguments in reverse order
2. `call ?@myfunc`

The return value is pushed onto the stack,
and the arguments are popped
(this is like a function in RPN).

Example:

    push 3
    push 2
    push 1
    call ?@myfunc ; return value is on the stack

###In `myfunc`:

1. Push `ebp`
2. Set `ebp` to `esp` (which points to the `ebp` pushed above)

Example:

    push ebp
    mov ebp, esp
    ; we can access the nth (1-based) argument with
    ; dword [ebp + 4 + 4 * n]

###To return from `myfunc`:

1. Store the return value in some temporary register (we use `eax`)
2. Restore `esp` by setting it to `ebp`
3. Pop into `ebp`
4. Pop the return address into a temporary register (we use `ebx`)
5. Deallocate the parameters by adding to `esp`
6. Push the return value (`eax`)
7. Jump (`ebx`)

Example:

    pop eax
    mov esp, ebp
    pop ebp
    pop ebx
    add esp, 12
    push eax ; omit if function does not return
    jmp ebx

Blocks
------

Local variables are allocated at the start of a block
by subtracting the size of the variables in bytes to `esp`.
At the end of a block, the variables are deallocated
by adding to `esp` (at the end of a function block,
all variables are deallocated by simply setting
`esp` to `ebp`).

Example (while loop):

    .while1: sub esp, 12 ; 3 4-byte local variables
    ...
    ; continue
    jmp .while1
    ...
    ; break
    jmp .endwhile1
    ...
    .endwhile1: add esp, 12
