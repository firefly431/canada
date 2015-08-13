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
3. Allocate local variables by subtracting from `esp`

Example:

    push ebp
    mov ebp, esp
    sub esp, 12 ; 3 4-byte local variables
    ; we can access the nth argument with
    ; word [ebp + 4 + 4 * n]

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
    add 12, esp
    push eax
    jmp ebx
