import ply.lex

import re

from syscall import syscalls

reserved = (
    'if',
    'else',
    'while',
    'break',
    'continue',
    'return',
    'export',
)

types = (
    'int',
    'char',
)

tokens = [
    'INT_LIT',
    'CHAR_LIT',
    'STRING_LIT',
    'IDENT',
    'SYSCALL',
    'PRIM_TYPE',
    'VOID',
    'SHIFT',
    'RELOP',
    'EQ',
    'AND',
    'OR',
] + list(map(str.upper, reserved))

# @ is unsigned %
# \ is unsigned /
# # is unsigned * (mul)
# # is * for char (deref)
literals = "()[]+-!~*&|/^,%@#{};\\"

def t_INT_LIT(t):
    r'-?\d+'
    t.value = int(t.value)
    return t

def t_CHAR_LIT(t):
    r'\'.\''
    t.value = t.value[1]
    return t

def t_STRING_LIT(t):
    r'"(\\.|[^"])*"'
    t.value = t.value[1:-1]
    return t

def t_IDENT(t):
    r'[a-zA-Z_][a-zA-Z_0-9]*'
    if t.value in reserved:
        t.type = t.value.upper()
    elif t.value in types:
        t.type = 'PRIM_TYPE'
    elif t.value == 'void':
        t.type = 'VOID'
    return t

t_SYSCALL = '|'.join(map(re.escape, syscalls.keys()))
t_SHIFT = r'<<|>>>?' # >>> is unsigned
t_RELOP = r'[<>]\|?=?|[=!]=' # >|, <|, >|=, <|= is unsigned
t_EQ = r'='
t_AND = r'&&'
t_OR = r'\|\|'

t_ignore_LINE_COMMENT = r'//.*'
def t_BLOCK_COMMENT(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

t_ignore = ' \r\t'

def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)

lexer = ply.lex.lex()

if __name__ == '__main__':
    ply.lex.runmain(lexer=lexer)
