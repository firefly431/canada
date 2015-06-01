import ply.lex
import ply.yacc

import canadalex
from canadalex import tokens

start = 'program'

precedence = (
    ('left', 'IF'), # resolve dangling else
    ('left', 'ELSE'),
    ('right', 'EQ'),
    ('left', '&', '|', '^'),
    ('left', 'RELOP'),
    ('left', 'SHIFT'),
    ('left', '+', '-'),
    ('left', '*', '/', '~', '\\', '%', '@'),
)

# return ('program', [global_decl...])
def p_program(p):
    '''
    program : program global_decl
            |
    '''
    if len(p) == 1:
        p[0] = (p.slice[0].type, [])
    else:
        p[0] = (p.slice[0].type, p[1][1] + p[2:])

# forwards
def p_global_decl(p):
    '''
    global_decl : global_var
                | function
    '''
    p[0] = p[1]

# return ('global_var', [var_type, IDENT, *literal])
def p_global_var(p):
    '''
    global_var : var_decl EQ literal ';'
    '''
    p[0] = (p.slice[0].type, p[1][1] + [p[3]])

# return ('var_type', [array_decl or ('PRIM_TYPE', [PRIM_TYPE])])
def p_var_type(p):
    '''
    var_type : array_decl
             | PRIM_TYPE
    '''
    if p.slice[1].type == 'PRIM_TYPE':
        p[0] = (p.slice[0].type, [('PRIM_TYPE', [p[1]])])
    else:
        p[0] = (p.slice[0].type, p[1:])

# return ('array_decl', [PRIM_TYPE, INT_LIT])
def p_array_decl(p):
    '''
    array_decl : PRIM_TYPE '[' INT_LIT ']'
    '''
    p[0] = (p.slice[0].type, [p[1], p[3]])

# returns ('INT_LIT' or 'CHAR_LIT' or 'STRING_LIT', INT_LIT or CHAR_LIT or STRING_LIT)
def p_literal(p):
    '''
    literal : INT_LIT
            | CHAR_LIT
            | STRING_LIT
    '''
    p[0] = (p.slice[1].type, [p[1]])

# return ('function', [('VOID', [VOID]) or var_type, IDENT, par_list, statement])
def p_function(p):
    '''
    function : var_decl function_header_body
             | VOID IDENT function_header_body
    '''
    if len(p) == 3:
        p[0] = (p.slice[0].type, p[1][1] + p[2][1])
    else:
        p[0] = (p.slice[0].type, [('VOID', [p[1]]), p[2]] + p[3][1])

# return ('function_header_body', [par_list, statement])
def p_function_header_body(p):
    '''
    function_header_body : '(' par_list ')' statement
    '''
    p[0] = (p.slice[0].type, [p[2], p[4]])

# return ('par_list', [var_decl...])
def p_par_list(p):
    '''
    par_list : par_list ',' var_decl
             | var_decl
             |
    '''
    if len(p) <= 2:
        p[0] = (p.slice[0].type, p[1:])
    else:
        p[0] = (p.slice[0].type, p[1][1] + p[3:])

# return ('var_decl', [var_type, IDENT])
def p_var_decl(p):
    '''
    var_decl : var_type IDENT
    '''
    p[0] = (p.slice[0].type, p[1:])

# forwards
def p_statement(p):
    '''
    statement : simple_stmt
              | block
    '''
    p[0] = p[1]

# forwards
def p_simple_stmt(p):
    '''
    simple_stmt : if_stmt
                | while_loop
                | break_stmt
                | continue_stmt
                | return_stmt
                | expr_stmt
    '''
    p[0] = p[1]

# returns ('if_stmt', [*expr, *statement, else_clause])
def p_if_stmt(p):
    '''
    if_stmt : IF condition statement else_clause
    '''
    p[0] = (p.slice[0].type, p[2:])

# forwards or returns None
def p_else_clause(p):
    '''
    else_clause : ELSE statement
                |
    '''
    if len(p) == 3:
        return p[2]
    else:
        return None

# returns ('while_loop', [*expr, *statement])
def p_while_loop(p):
    '''
    while_loop : WHILE condition statement
    '''
    p[0] = (p.slice[0].type, p[2:])

# forwards expr
def p_condition(p):
    '''
    condition : '(' expr ')'
    '''
    p[0] = p[2]

# returns ('break_stmt', [])
def p_break_stmt(p):
    '''
    break_stmt : BREAK ';'
    '''
    p[0] = (p.slice[0].type, [])

# returns ('continue_stmt', [])
def p_continue_stmt(p):
    '''
    continue_stmt : CONTINUE ';'
    '''
    p[0] = (p.slice[0].type, [])

# returns ('return_stmt', [*expr] or [])
def p_return_stmt(p):
    '''
    return_stmt : RETURN expr ';'
                | RETURN ';'
    '''
    p[0] = (p.slice[0].type, p[2:-1])

# forwards
def p_expr_stmt(p):
    '''
    expr_stmt : expr ';'
    '''
    p[0] = p[1]

# forwards with name 'block'
def p_block(p):
    '''
    block : '{' block_stmt_list '}'
    '''
    p[0] = (p.slice[0].type, p[2][1])

# returns ('block_stmt_list', [block_stmt...])
def p_block_stmt_list(p):
    '''
    block_stmt_list : block_stmt_list block_stmt
                    |
    '''
    if len(p) == 1:
        p[0] = (p.slice[0].type, [])
    else:
        p[0] = (p.slice[0].type, p[1][1] + p[2:])

# forwards
def p_block_stmt(p):
    '''
    block_stmt : statement
               | var_decl ';'
    '''
    p[0] = p[1]

# returns ('bin_expr', [*operator, *expr, *expr])
def p_bin_expr(p):
    '''
    bin_expr : expr '*' expr
             | expr '/' expr
             | expr '\\\\' expr
             | expr '~' expr
             | expr '%' expr
             | expr '@' expr
             | expr '+' expr
             | expr '-' expr
             | expr SHIFT expr
             | expr RELOP expr
             | expr '&' expr
             | expr '|' expr
             | expr '^' expr
             | lvalue EQ expr
    '''
    p[0] = (p.slice[0].type, [p[2], p[1], p[3]])

# forwards something
def p_expr(p):
    '''
    expr : bin_expr
         | function_call
         | '(' expr ')'
         | lvalue
         | address
         | literal
    '''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

# returns ('function_call', [*function_name, arg_list])
def p_function_call(p):
    '''
    function_call : function_name '(' arg_list ')'
    '''
    p[0] = (p.slice[0].type, [p[1], p[3]])

# forwards
def p_function_name(p):
    '''
    function_name : IDENT
                  | SYSCALL
    '''
    p[0] = p[1]

# returns ('arg_list', [*expr...])
def p_arg_list(p):
    '''
    arg_list : arg_list ',' expr
             | expr
             |
    '''
    if len(p) <= 2:
        p[0] = (p.slice[0].type, p[1:])
    else:
        p[0] = (p.slice[0].type, p[1][1] + [p[3]])

# forwards or returns ('IDENT', [IDENT])
def p_lvalue(p):
    '''
    lvalue : deref
           | simple_lvalue
    simple_lvalue : array_acc
                  | IDENT
    '''
    if p.slice[1].type == 'IDENT':
        p[0] = p[1]
    else:
        p[0] = ('IDENT', [p[1]])

# returns ('deref', ['*' or '~', *expr])
def p_deref(p):
    '''
    deref : '*' '(' expr ')'
          | '~' '(' expr ')'
    '''
    p[0] = (p.slice[0].type, [p[1], p[3]])

# returns ('address', [*simple_lvalue])
def p_address(p):
    '''
    address : '&' simple_lvalue
    '''
    p[0] = (p.slice[0].type, [p[2]])

# returns ('array_acc', [IDENT, *expr])
def p_array_acc(p):
    '''
    array_acc : IDENT '[' expr ']'
    '''
    p[0] = (p.slice[0].type, [p[1], p[3]])

def p_error(p):
    if p:
        print("Syntax error at %s (%s), line %d" % (p.value, p.type, p.lineno))
        print("Position: %d" % p.lexpos)
        parser.errok()
    else:
        print("Syntax error at EOF")

if __name__ == '__main__':
    import fileinput
    lexer = ply.lex.lex(module=canadalex)
    parser = ply.yacc.yacc()
    code = ''.join(fileinput.input())
    result = parser.parse(code, lexer=lexer)
    # print(result)
    # print graphviz
    print("digraph parse_tree {")
    print("    node [shape = box];")
    node_c = 0
    def node(*args):
        global node_c
        node_c += 1
        return "node" + str(node_c)
    def walk(n, i):
        if not isinstance(n, tuple):
            print("    " + i + " [label = \"" + str(n) + "\", shape = \"diamond\"]")
            return
        print("    " + i + " [label = \"" + n[0] + "\"]")
        nodes = list(map(node, n[1]))
        for nn in nodes:
            print("    " + i + " -> " + nn)
        for j, nn in enumerate(n[1]):
            walk(nn, nodes[j])
    walk(result, "node0")
    print("}")
