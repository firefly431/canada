import ply.lex
import ply.yacc

import sys

import canadalex
from canadalex import tokens

start = 'program'

precedence = (
    ('left', ';'),
    ('left', 'IF'), # resolve dangling else
    ('left', 'ELSE'),
    ('right', 'EQ'),
    ('left', 'AND', 'OR'),
    ('left', '&', '|', '^'),
    ('left', 'RELOP'),
    ('left', 'SHIFT'),
    ('left', '+', '-'),
    ('left', '*', '/', '#', '\\', '%', '@'),
    ('right', 'UNARY'),
)

class FakeTuple:
    def __init__(self, elements):
        if isinstance(elements, FakeTuple):
            elements = elements._tuple_elements
        self._tuple_elements = elements
    def __getitem__(self, key):
        return self._tuple_elements.__getitem__(key)
    def __repr__(self):
        return type(self).__name__ + ': ' + str(self._tuple_elements)

class Program(FakeTuple):
    def __init__(self):
        self.decls = []
        FakeTuple.__init__(self, ('program', self.decls))
    def append(self, decl):
        self.decls.append(decl)
        return self
    def __repr__(self):
        return '\n'.join(map(repr, self.decls))

class GlobalDeclaration(FakeTuple): pass

class GlobalVariable(GlobalDeclaration):
    def __init__(self, decl, value):
        """
        :type decl: VariableDeclaration
        :type value: Literal or ArrayLiteral
        """
        self.var_type = decl.type
        self.name = decl.name
        self.value = value
        FakeTuple.__init__(self, ('global_var',
                           [self.var_type, self.name, value]))
    def __repr__(self):
        return repr(self.var_type) + ' ' + self.name + ' = ' + repr(self.value) + ';'

class VariableType(FakeTuple):
    def size(self):
        raise NotImplementedError()

class PrimitiveType(VariableType):
    def __init__(self, type):
        ":type type: str"
        self.type = type
        FakeTuple.__init__(self, ('PRIM_TYPE', [type]))
    def __repr__(self):
        return self.type
    def size(self):
        return 4
    @staticmethod
    def sizeof(t):
        if t == 'int':
            return 4
        elif t == 'char':
            return 1
        else:
            raise ValueError()

class Void():
    def __init__(self):
        FakeTuple.__init__(self, ('VOID', ['void']))
    def __repr__(self):
        return 'void'

class ArrayDeclaration(VariableType):
    def __init__(self, prim_type, length):
        """
        :type prim_type: str
        :type length: int
        """
        self.prim_type = prim_type
        self.length = length
        FakeTuple.__init__(self, ('array_decl',
                                 [prim_type, length]))
    def __repr__(self):
        return self.prim_type + '[' + (str(self.length) if self.length else '') + ']'
    def size(self):
        r = self.length * PrimitiveType.sizeof(self.prim_type)
        # round up
        if r & 3: r = (r & ~3) + 4
        return r

class ArrayLiteral(FakeTuple):
    def __init__(self, elements):
        """
        :type elements: list
        """
        self.elements = elements
        FakeTuple.__init__(self, ('array_lit', self.elements))
    def __repr__(self):
        return '{' + ', '.join(map(repr, self.elements)) + '}'

class Function(FakeTuple):
    def __init__(self, name_or_vardecl, header_and_body, par_list = None, statement = None):
        """
        :type name_or_vardecl: str or VariableDeclaration
        :type header_and_body: tuple
        """
        if par_list:
            self.type = name_or_vardecl
            self.name = header_and_body
            self.par_list = par_list
            self.statement = statement
        else:
            if isinstance(name_or_vardecl, VariableDeclaration):
                self.type = name_or_vardecl.type
                self.name = name_or_vardecl.name
            else:
                self.type = Void()
                self.name = name_or_vardecl
            self.par_list, self.statement = header_and_body
        FakeTuple.__init__(self, ('function', [self.type, self.name, ('par_list', self.par_list), self.statement]))
    def __repr__(self):
        return repr(self.type) + ' ' + self.name + '(' + ', '.join(self.parameters()) + ') ' + repr(self.statement)
    def parameters(self):
        return self.par_list
    def prototype(self):
        return repr(self.type) + ' ' + self.name + '(' + ', '.join(self.parameters()) + ')'

class BlockStatement(FakeTuple): pass
class Statement(BlockStatement): pass

class EmptyStatement(Statement):
    def __init__(self):
        FakeTuple.__init__(self, None)
    def __repr__(self):
        return ';'

class IfStatement(Statement):
    def __init__(self, cond, stmt, else_c = None):
        self.condition = cond
        self.statement = stmt
        self.else_clause = else_c
        FakeTuple.__init__(self, ('if_stmt', [cond, stmt] + ([else_c] if else_c else [])))
    def __repr__(self):
        return 'if (' + repr(self.condition) + ') ' + repr(self.statement) + (' else ' + repr(self.else_clause) if self.else_clause else '')

class WhileLoop(Statement):
    def __init__(self, cond, stmt):
        self.condition = cond
        self.statement = stmt
        FakeTuple.__init__(self, ('if_stmt', [cond, stmt]))
    def __repr__(self):
        return 'while (' + repr(self.condition) + ') ' + repr(self.statement)

class BreakStatement(Statement):
    def __init__(self):
        FakeTuple.__init__(self, ('break_stmt', []))
    def __repr__(self):
        return 'break;'
class ContinueStatement(Statement):
    def __init__(self):
        FakeTuple.__init__(self, ('continue_stmt', []))
    def __repr__(self):
        return 'continue;'
class ReturnStatement(Statement):
    def __init__(self, expr = None):
        """
        :type expr: Expression
        :type array: bool
        """
        self.expr = expr
        FakeTuple.__init__(self, ('return', [expr] if expr else []))
    def __repr__(self):
        if not self.expr: return 'return;'
        return 'return ' + repr(self.expr) + ';'

class VariableDeclaration(BlockStatement):
    def __init__(self, type, name):
        """
        :type type: VariableType
        :type name: str
        """
        self.type = type
        self.name = name
        FakeTuple.__init__(self, ('var_decl', [type, name]))
    def __repr__(self):
        return repr(self.type) + ' ' + self.name

def _indent(s):
    # lol
    if (isinstance(s, VariableDeclaration)):
        s = repr(s) + ';'
    else:
        s = repr(s)
    return '\n'.join('    ' + l for l in s.splitlines())

class Block(Statement):
    def __init__(self, statements):
        """
        :type statements: list
        """
        self.statements = statements
        FakeTuple.__init__(self, ('block', statements))
    def __repr__(self):
        return '{\n' + '\n'.join(map(_indent, self.statements)) + '\n}'

class Expression(FakeTuple): pass
class ExpressionStatement(Statement):
    def __init__(self, expr):
        """
        :type expr: Expression
        """
        self.expr = expr
        FakeTuple.__init__(self, expr)
    def __repr__(self):
        return repr(self.expr) + ';'

class Unary(Expression):
    def __init__(self, op, expr):
        """
        :type op: str
        :type expr: Expression
        """
        self.op = op
        self.expr = expr
        FakeTuple.__init__(self, ('unary', [op, expr]))
    def __repr__(self):
        return self.op + '(' + repr(self.expr) + ')'

class Literal(Expression):
    def __init__(self, type, value):
        """
        :type type: str
        :type value: str or int
        """
        self.type = type
        self.value = value
        FakeTuple.__init__(self, (type, [value]))
    def __repr__(self):
        if self.type == 'INT_LIT':
            return str(self.value)
        elif self.type == 'CHAR_LIT':
            return "'" + self.value + "'"
        else:
            return '"' + self.value + '"'

class BinaryExpression(Expression):
    def __init__(self, op, lhs, rhs):
        """
        :type op: str
        :type lhs: Expression or LValue
        :type rhs: Expression
        """
        self.op = op
        self.lhs = lhs
        self.rhs = rhs
        FakeTuple.__init__(self, ('bin_expr', [op, lhs, rhs]))
    def __repr__(self):
        return ('(' + repr(self.lhs) + ') ' if self.op != '=' else repr(self.lhs) + ' ') + self.op + ' (' + repr(self.rhs) + ')'

class FunctionCall(Expression):
    def __init__(self, name, args):
        """
        :type name: str
        :type args: list
        """
        self.name = name
        self.args = args
        FakeTuple.__init__(self, ('function_call', [name, ('arg_list', args)]))
    def __repr__(self):
        return self.name + '(' + ', '.join(map(repr, self.args)) + ')'

class LValue(Expression): pass
class SimpleLValue(LValue): pass

class Identifier(SimpleLValue):
    def __init__(self, name):
        """
        :type name: str
        """
        self.name = name
        FakeTuple.__init__(self, ('IDENT', [name]))
    def __repr__(self):
        return self.name

class Dereference(LValue):
    def __init__(self, expr, char = False):
        """
        :type expr: Expression
        :type char: bool
        """
        self.expr = expr
        self.char = char
        FakeTuple.__init__(self, ('deref', ['#' if char else '*', expr]))
    def __repr__(self):
        return ('#' if self.char else '*') + '(' + repr(self.expr) + ')'

class Address(Expression):
    def __init__(self, lvalue):
        """
        :type lvalue: SimpleLValue
        """
        self.lvalue = lvalue
        FakeTuple.__init__(self, ('address', [lvalue]))
    def __repr__(self):
        return '&' + repr(self.lvalue)

class ArrayAccess(SimpleLValue):
    def __init__(self, array, index):
        """
        :type array: str
        :type index: Expression
        """
        self.array = array
        self.index = index
        FakeTuple.__init__(self, ('array_acc', [array, index]))
    def __repr__(self):
        return self.array + '[' + repr(self.index) + ']'

class Export(GlobalDeclaration):
    def __init__(self, name, function = False):
        """
        :type name: str
        :type function: bool
        """
        self.name = name
        self.function = function
        FakeTuple.__init__(self, ('export_func' if function else 'export', [name]))
    def __repr__(self):
        return 'export ' + self.name + ('();' if self.function else ';')

class Extern(GlobalDeclaration):
    def __init__(self, decl, c = None):
        """
        :type decl: VariableDeclaration or (VariableDeclaration or str, tuple)
        :type c: bool
        """
        if isinstance(decl, VariableDeclaration):
            self.name = decl.name
            self.type = decl.type
            self.par_list = None
            self.is_var = True
            self.varargs = False
        else:
            self.is_var = False
            if isinstance(decl[0], VariableDeclaration):
                self.name = decl[0].name
                self.type = decl[0].type
            else:
                self.name = decl[0]
                self.type = Void()
            self.varargs, self.par_list = decl[1]
        self.c = c
        FakeTuple.__init__(self, ('extern' + ('_c' if self.c else '') + ('_var' if self.is_var else ''), [self.type, self.name] if self.is_var else [self.type, self.name, self.par_list]))
    def __repr__(self):
        return 'extern ' + ('"C" ' if self.c else '') + repr(self.type) + ' ' + self.name + ('(' + ', '.join(map(repr, self.par_list + ([Ellipsis] if self.varargs else []))) + ')' if not self.is_var else '') + ';'

# return ('program', [*global_decl...])
def p_program(p):
    '''
    program : program global_decl
            |
    '''
    if len(p) == 1:
        p[0] = Program()
    else:
        p[0] = p[1].append(p[2])

# forwards
def p_global_decl(p):
    '''
    global_decl : global_var
                | function
                | export
                | extern
    '''
    p[0] = p[1]

# return ('global_var', [var_type, IDENT, *literal or array_lit])
def p_global_var(p):
    '''
    global_var : var_decl EQ literal ';'
               | var_decl EQ array_lit ';'
    '''
    p[0] = GlobalVariable(p[1], p[3])

# forwards array_decl or wraps PRIM_TYPE
def p_var_type(p):
    '''
    var_type : array_decl
             | PRIM_TYPE
    '''
    if p.slice[1].type == 'PRIM_TYPE':
        p[0] = PrimitiveType(p[1])
    else:
        p[0] = p[1]

# return ('array_decl', [PRIM_TYPE, INT_LIT])
def p_array_decl(p):
    '''
    array_decl : PRIM_TYPE '[' INT_LIT ']'
               | PRIM_TYPE '[' ']'
    '''
    p[0] = ArrayDeclaration(p[1], p[3] if len(p) >= 5 else None)

# returns ('INT_LIT' or 'CHAR_LIT' or 'STRING_LIT', INT_LIT or CHAR_LIT or STRING_LIT)
def p_literal(p):
    '''
    literal : INT_LIT
            | CHAR_LIT
            | STRING_LIT
    '''
    p[0] = Literal(p.slice[1].type, p[1])

# forwards
def p_array_lit(p):
    '''
    array_lit : '{' array_list '}'
    '''
    p[0] = ArrayLiteral(p[2])

# return [*literal...]
# returns ('array_lit', [*literal...])
def p_array_list(p):
    '''
    array_list : array_list ',' literal
               | literal
               |
    '''
    if len(p) <= 2:
        p[0] = p[1:]
    else:
        p[0] = p[1] + [p[3]]

# return ('function', [('VOID', [VOID]) or var_type, IDENT, par_list, statement])
def p_function(p):
    '''
    function : var_decl function_header_body
             | VOID IDENT function_header_body
    '''
    p[0] = Function(p[len(p) - 2], p[len(p) - 1])

# return (par_list, statement)
def p_function_header_body(p):
    '''
    function_header_body : '(' par_list ')' statement
    '''
    p[0] = (p[2], p[4])

# return [IDENT...]
def p_par_list(p):
    '''
    par_list : par_list ',' IDENT
             | IDENT
             |
    '''
    if len(p) <= 2:
        p[0] = p[1:]
    else:
        p[0] = p[1] + p[3:]

# return ('var_decl', [var_type, IDENT])
def p_var_decl(p):
    '''
    var_decl : var_type IDENT
    '''
    p[0] = VariableDeclaration(p[1], p[2])

# forwards
def p_statement(p):
    '''
    statement : simple_stmt
              | block
    '''
    p[0] = p[1]

# forwards or returns None
def p_simple_stmt(p):
    '''
    simple_stmt : if_stmt
                | while_loop
                | break_stmt
                | continue_stmt
                | return_stmt
                | expr_stmt
                | ';'
    '''
    if p.slice[1].type == ';': p[0] = EmptyStatement()
    else:
        p[0] = p[1]

# returns ('if_stmt', [*expr, *statement, else_clause])
def p_if_stmt(p):
    '''
    if_stmt : IF condition statement
            | IF condition statement ELSE statement
    '''
    p[0] = IfStatement(p[2], p[3], p[5] if len(p) >= 6 else None)

# returns ('while_loop', [*expr, *statement])
def p_while_loop(p):
    '''
    while_loop : WHILE condition statement
    '''
    p[0] = WhileLoop(p[2], p[3])

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
    p[0] = BreakStatement()

# returns ('continue_stmt', [])
def p_continue_stmt(p):
    '''
    continue_stmt : CONTINUE ';'
    '''
    p[0] = ContinueStatement()

# returns ('return_stmt', [*expr] or [])
# or returns ('return_arr', [IDENT])
def p_return_stmt(p):
    '''
    return_stmt : RETURN expr ';'
                | RETURN ';'
    '''
    if len(p) == 4:
        p[0] = ReturnStatement(p[2])
    else:
        p[0] = ReturnStatement()

# forwards
def p_expr_stmt(p):
    '''
    expr_stmt : expr ';'
    '''
    p[0] = ExpressionStatement(p[1])

# forwards with name 'block'
def p_block(p):
    '''
    block : '{' block_stmt_list '}'
    '''
    p[0] = Block(p[2])

# returns [block_stmt...]
def p_block_stmt_list(p):
    '''
    block_stmt_list : block_stmt_list block_stmt
                    |
    '''
    if len(p) == 1:
        p[0] = []
    else:
        p[0] = p[1] + p[2:]

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
             | expr '#' expr
             | expr '%' expr
             | expr '@' expr
             | expr '+' expr
             | expr '-' expr
             | expr SHIFT expr
             | expr RELOP expr
             | expr '&' expr
             | expr '|' expr
             | expr '^' expr
             | expr AND expr
             | expr OR expr
             | lvalue EQ expr
    '''
    p[0] = BinaryExpression(p[2], p[1], p[3])

# forwards something
def p_expr(p):
    '''
    expr : bin_expr
         | function_call
         | '(' expr ')'
         | lvalue %prec ';'
         | address
         | literal
         | '!' expr %prec UNARY
         | '-' expr %prec UNARY
         | '~' expr %prec UNARY
    '''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = Unary(p[1], p[2])
    else:
        p[0] = p[2]

# returns ('function_call', [*function_name, arg_list])
def p_function_call(p):
    '''
    function_call : function_name '(' arg_list ')'
    '''
    p[0] = FunctionCall(p[1], p[3])

# forwards
def p_function_name(p):
    '''
    function_name : IDENT
                  | SYSCALL
    '''
    p[0] = p[1]

# returns [*expr...]
def p_arg_list(p):
    '''
    arg_list : arg_list ',' expr
             | expr
             |
    '''
    if len(p) <= 2:
        p[0] = p[1:]
    else:
        p[0] = p[1] + [p[3]]

# forwards or returns ('IDENT', [IDENT])
def p_lvalue(p):
    '''
    lvalue : deref
           | simple_lvalue
    simple_lvalue : array_acc
                  | IDENT
    '''
    if p.slice[1].type != 'IDENT':
        p[0] = p[1]
    else:
        p[0] = Identifier(p[1])

# returns ('deref', ['*' or '#', *expr])
def p_deref(p):
    '''
    deref : '*' expr %prec UNARY
          | '#' expr %prec UNARY
    '''
    p[0] = Dereference(p[2], p[1] == '#')

# returns ('address', [*simple_lvalue])
def p_address(p):
    '''
    address : '&' simple_lvalue
    '''
    p[0] = Address(p[2])

def p_export(p):
    '''
    export : EXPORT IDENT ';'
           | EXPORT IDENT '(' ')' ';'
    '''
    p[0] = Export(p[2], len(p) == 6)

def p_extern(p):
    '''
    extern : EXTERN extern_decl
           | EXTERN STRING_LIT extern_decl
    '''
    p[0] = Extern(p[2] if len(p) == 3 else p[3], None if len(p) == 3 else p[2])

def p_extern_decl(p):
    '''
    extern_decl : var_decl ';'
                | extern_func
    '''
    p[0] = p[1]

def p_extern_func(p):
    '''
    extern_func : var_decl '(' extern_par_list ')' ';'
                | VOID IDENT '(' extern_par_list ')' ';'
    '''
    p[0] = (p[1] if len(p) == 6 else p[2], p[3] if len(p) == 6 else p[4])

def p_extern_par_list(p):
    '''
    extern_par_list : par_list
                    | par_list ',' ELLIPSIS
                    | ELLIPSIS
    '''
    if len(p) == 4:
        p[0] = (True, p[1])
    else:
        if p[1] == Ellipsis:
            p[0] = (True, [])
        else:
            p[0] = (False, p[1])

# returns ('array_acc', [IDENT, *expr])
def p_array_acc(p):
    '''
    array_acc : IDENT '[' expr ']'
    '''
    p[0] = ArrayAccess(p[1], p[3])

def p_error(p):
    if p:
        print("Syntax error at %s (%s), line %d" % (p.value, p.type, p.lineno))
        print("Position: %d" % p.lexpos)
        parser.errok()
    else:
        print("Syntax error at EOF")

lexer = canadalex.lexer
parser = ply.yacc.yacc()

def parse(code):
    return parser.parse(code, lexer=lexer)

if __name__ == '__main__':
    import fileinput
    import sys
    import os
    code = ''.join(fileinput.input())
    result = parse(code)
    # print(result)
    # print graphviz
    # lazy, so redirect stdout
    if len(sys.argv) >= 2:
        sys.stdout = open(os.path.splitext(sys.argv[1])[0] + '.dot', 'w')
        print("digraph parse_tree {")
        print("    node [shape = box];")
        node_c = 0
        def node(*args):
            global node_c
            node_c += 1
            return "node" + str(node_c)
        def walk(n, i):
            if not isinstance(n, tuple) and not (isinstance(n, FakeTuple) and n._tuple_elements):
                print("    " + i + " [label = \"" + str(n).replace('\\', '\\\\') + "\", shape = \"diamond\"]")
                return
            print("    " + i + " [label = \"" + n[0] + "\"]")
            nodes = list(map(node, n[1]))
            for nn in nodes:
                print("    " + i + " -> " + nn)
            for j, nn in enumerate(n[1]):
                walk(nn, nodes[j])
        walk(result, "node0")
        print("}")
    else:
        print(repr(result))
