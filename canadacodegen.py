import functools
import canadaparse

from canadaparse import Program, GlobalDeclaration, GlobalVariable, VariableType, PrimitiveType, Void, ArrayDeclaration, ArrayLiteral, Function, BlockStatement, Statement, EmptyStatement, IfStatement, WhileLoop, BreakStatement, ContinueStatement, ReturnStatement, VariableDeclaration, Block, Expression, ExpressionStatement, Literal, BinaryExpression, FunctionCall, LValue, SimpleLValue, Identifier, Dereference, Address, ArrayAccess, Unary, Export, Extern
from syscall import syscalls

import os

# dword to byte
int_to_char = {'eax': 'al', 'ebx': 'bl', 'ecx': 'cl', 'edx': 'dl'}
# j_ and set_
rel_ops = {
    '>': 'g',
    '<': 'l',
    '>=': 'ge',
    '<=': 'le',
    '>|': 'a',
    '>|=': 'ae',
    '<|': 'b',
    '<|=': 'be',
    '==': 'e',
    '!=': 'ne',
}

rel_ops_not = {
    '>': 'le',
    '<': 'ge',
    '>=': 'l',
    '<=': 'g',
    '>|': 'be',
    '>|=': 'b',
    '<|': 'ae',
    '<|=': 'a',
    '==': 'ne',
    '!=': 'e',
}

class CompilationError(Exception):
    def __init__(self, message, source):
        super().__init__(message)
        self.source = source

class CFunction(Function):
    def __init__(self, ext):
        ":type ext: Extern"
        Function.__init__(self, ext.type, ext.name, ext.par_list)
        self.varargs = ext.varargs
    def parameters(self):
        return self.par_list + ['...']

class StackEntry:
    def __init__(self, var, addr):
        """
        :type var: VariableDeclaration
        :type addr: int
        """
        self.var = var
        self.addr = addr
    def value(self, offset=0, prefix=True):
        oprefix = '4*' if self.var.type == 'int' else ''
        if isinstance(offset, str):
            return self.value(0, prefix)[:-1] + '+' + oprefix + offset + ']'
        offset += self.addr
        pt = self.var.type.type if isinstance(self.var.type, PrimitiveType) else self.var.type.prim_type
        return (('dword' if pt == 'int' else 'byte') if prefix else '') + '[ebp' + ('+' + oprefix + str(offset) if offset >= 0 else '-' + oprefix + str(-offset)) + ']'
    def __str__(self):
        return '<' + repr(self.var) + ' at ' + self.value() + '>'

class GlobalStackEntry(StackEntry):
    def __init__(self, type, name):
        """
        :type var: GlobalVariable
        """
        super().__init__(VariableDeclaration(type, name), name)
        self.name = name
    def value(self, offset=0, prefix=True):
        oprefix = '4*' if self.var.type == 'int' else ''
        pt = self.var.type.type if isinstance(self.var.type, PrimitiveType) else self.var.type.prim_type
        if isinstance(offset, str):
            return (('dword' if pt == 'int' else 'byte') if prefix else '') + '[' + self.name + '+' + oprefix + offset + ']'
        return (('dword' if pt == 'int' else 'byte') if prefix else '') + '[' + self.name + ('+' + oprefix + str(offset) if offset >= 0 else '-' + oprefix + str(-offset)) + ']'

class StackFrame:
    def __init__(self, parameters):
        if parameters is None: return
        self.stack = [StackEntry(VariableDeclaration(PrimitiveType('int'), p), 8 + 4 * i) for i, p in reversed(list(enumerate(parameters)))]
        self.build_table()
    def get_last(self):
        "get last address on stack (not parameter)"
        if self.stack and self.stack[-1].addr <= 0:
            return self.stack[-1].addr
        return 0
    def build_table(self):
        "rebuild variable table"
        self.table = {p.var.name: p for p in self.stack}
    def _extend(self, variables):
        old = self.get_last()
        for v in variables:
            self.stack.append(StackEntry(v, self.get_last() - v.type.size()))
        ret = old - self.get_last()
        self.build_table()
        assert ret == sum(v.type.size() for v in variables)
        return ret
    def extend(self, variables):
        "returns (StackFrame, int) where int is size of variables"
        newstack = StackFrame(None)
        newstack.stack = self.stack[:]
        newstack.table = None # will be filled in _extend
        return newstack, newstack._extend(variables)
    def size(self):
        "in bytes, does not include parameters"
        if not self.stack:
            return 0
        last = self.stack[-1]
        if last.addr > 0:
            return 0
        ret = -last.addr
        assert ret == sum(a.var.type.size() for a in self.stack if a.addr < 0)
        return ret
    def __getitem__(self, key):
        return self.table[key]
    def __contains__(self, key):
        return key in self.table

def generate(fn, out=None, margin=16, iwidth=8, width=40):
    """
    Generate assembly file (out defaults to fn with the
    file extension replaced by '.s')
    """
    import os
    if not out:
        out = os.path.splitext(fn)[0] + '.s'
    with open(fn) as f, open(out, 'w') as outf:
        ast = canadaparse.parse(f.read())
        CodeGenerator(outf,
                      margin=margin,
                      iwidth=iwidth,
                      width=width).generate(ast)

class CodeGenerator:
    def __init__(self, out, margin=16, iwidth=8, width=40, linux=None, c_prefix=None):
        import os
        self.out = out
        self.margin = margin
        self.iwidth = iwidth
        self.width = width
        self.whilec = 0
        self.ifc = 0
        self.stringc = 0
        self.labelc = 0 # number of generic labels
        # generic labels are usually generated by comparisons
        # and short-circuiting
        self.gvars = {}
        self.gfuncs = {}
        self.functions = []
        self.variables = []
        self.exports = []
        self.externs = []
        self._label = None
        # autodetect os stuff
        sysname = os.uname()[0]
        if sysname == 'Linux':
            self.linux = True
            self.c_prefix = '' # I think
        elif sysname == 'FreeBSD':
            self.linux = False
            self.c_prefix = '' # I think
        elif sysname == 'Darwin':
            self.linux = False
            self.c_prefix = '_'
        else:
            self.linux = None
            self.c_prefix = None
        if linux is not None:
            self.linux = linux
        if c_prefix is not None:
            self.c_prefix = c_prefix
        if self.linux is None:
            raise Exception("Unknown if " + sysname + " is linux or not")
        if self.c_prefix is None:
            raise Exception("Unknown if " + sysname + " has prefix for C symbols")
    def warn(self, message, source):
        import sys
        sys.stderr.write('WARNING: ' + message + '\n')
    def label(self, label):
        if not label: return
        if self._label:
            self.write()
        self._label = label
    def write(self, inst = None, code = None, label=None, comment=None):
        """
        :type inst: str
        :type code: str
        :type label: str
        :type comment: str
        """
        if self._label:
            if label:
                self.out.write(self._label + ':\n')
            else:
                label = self._label
            self._label = None
        if not inst:
            if label:
                self.out.write(label + ':\n')
            else:
                self.out.write('\n')
            return
        if self.margin:
            if not label:
                label = ''
            else:
                label += ':'
            label = label.ljust(self.margin)
        if code:
            if self.iwidth:
                inst = inst.ljust(self.iwidth - 1)
            inst += ' ' + code
        if comment and self.width:
            code = code.ljust(self.width)
        if not comment:
            comment = ''
        self.out.write(label + inst + comment + '\n')
    def generate(self, ast):
        """
        Generate the assembly code from the AST
        """
        assert isinstance(ast, Program)
        self.variables = [d for d in ast.decls if isinstance(d, GlobalVariable)]
        self.functions = [d for d in ast.decls if isinstance(d, Function)]
        self.exports = [d for d in ast.decls if isinstance(d, Export)]
        self.externs = [d for d in ast.decls if isinstance(d, Extern)]
        assert all(sum((x in self.variables, x in self.functions, x in self.exports, x in self.externs)) == 1 for x in ast.decls)
        self.gvars = {v.name: GlobalStackEntry(v.var_type, v.name) for v in self.variables}
        self.gfuncs = {v.name: v for v in self.functions}
        self.generate_exports()
        self.generate_externs()
        self.generate_text()
        self.generate_data()
    def string(self, s):
        i = self.stringc
        self.stringc += 1
        name = '??sl' + str(i)
        self.variables.append(GlobalVariable(VariableDeclaration(ArrayDeclaration('char', len(s) - s.count('\\') + s.count('\\\\')), name), Literal('STRING_LIT', s)))
        return name
    def value(self, t, v):
        """
        :type t: str
        :type v: Literal
        """
        if t == 'int':
            if v.type == 'INT_LIT':
                return v.value
            elif v.type == 'CHAR_LIT':
                return ord(v.value)
            else:
                assert v.type == 'STRING_LIT'
                return self.string(v.value)
        else:
            if v.type == 'INT_LIT':
                if v.value > 255:
                    raise CompilationError("%d too big to fit in char" %
                                      v.value, v)
                return v.value
            elif v.type == 'CHAR_LIT':
                return ord(v.value)
            else:
                raise CompilationError("String literal cannot be a char", v)
    def generate_variable(self, v):
        """
        Generate the instructions for a variable
        :type v: GlobalVariable
        """
        if v.name == '_start':
            raise CompilationError('Reserved name', v)
        prim_type = v.var_type if isinstance(v.var_type, PrimitiveType) else v.var_type.prim_type
        dd = 'db' if prim_type == 'char' else 'dd'
        if isinstance(v.var_type, ArrayDeclaration):
            arr_size = v.var_type.length
            if not isinstance(v.value, ArrayLiteral):
                if isinstance(v.value, Literal) and v.value.type == 'STRING_LIT' and prim_type == 'char':
                    lit_len = len(v.value.value) - v.value.value.count('\\') + v.value.value.count('\\\\')
                    if not arr_size:
                        arr_size = lit_len
                        v.var_type.length = lit_len
                    if lit_len != arr_size:
                        raise CompilationError("String literal wrong "
                                          "size", v)
                    self.write('db', "`" + v.value.value + "`", label=v.name)
                else:
                    raise CompilationError("Array not initialized with "
                                      "array literal", v)
            else:
                if not arr_size:
                    arr_size = len(v.value.elements)
                    v.var_type.length = arr_size
                if len(v.value.elements) != arr_size:
                    raise CompilationError("Array literal wrong size", v)
                self.write(dd, ','.join(map(str, map(
                    functools.partial(self.value, prim_type), v.value.elements))),
                    label=v.name)
        else:
            self.write(dd, str(self.value(prim_type, v.value)), label=v.name)
    def generate_data(self):
        """
        Generate the .data section
        """
        self.write('SECTION .data')
        vl = len(self.variables)
        for v in self.variables[:]:
            self.generate_variable(v)
        # second pass, if there were any arrays of string literals
        for v in self.variables[vl:]:
            self.generate_variable(v)
    def generate_text(self):
        """
        Generate the .text section
        """
        self.write('SECTION .text')
        for f in self.functions:
            self.generate_function(f)
    def generate_function(self, f):
        """
        :type f: Function
        """
        if f.name == 'main':
            if len(f.par_list) != 2:
                raise CompilationError("Main must have 2 parameters", f)
        self.gfuncs[f.name] = f
        stack = StackFrame(f.par_list)
        self.label('?@' + f.name)
        self.write('push', 'ebp')
        self.write('mov', 'ebp,esp')
        # function body
        self.generate_statement(f.statement, stack, function=True)
        # return
        self.write('push', '0')
        self.label('.return')
        self.write('pop', 'eax')
        self.write('mov', 'esp,ebp')
        self.write('pop','ebp')
        self.write('pop','ebx')
        self.write('add', 'esp,' + str(4 * len(f.par_list)))
        if not isinstance(f.type, Void):
            self.write('push', 'eax')
        self.write('jmp', 'ebx')
    class BlockWrapper:
        def __init__(self, cg, block, stack, function = False):
            """
            :type cg: CodeGenerator
            :type block: Block
            :type stack: StackFrame

            will not generate instruction to deallocate locals if function
            """
            self.cg = cg
            self.block = block
            self.stack = stack
            self.function = function
        def __enter__(self):
            self.vardecs = [v for v in self.block.statements if isinstance(v, VariableDeclaration)]
            self.stack, self.bsize = self.stack.extend(self.vardecs)
            assert isinstance(self.stack.size(), int) # make sure this works
            if self.bsize > 0:
                self.cg.write('sub', 'esp,' + str(self.bsize))
            return self
        def __exit__(self, *args):
            if not self.function:
                if self.bsize > 0:
                    self.cg.write('add', 'esp,' + str(self.bsize))
    def generate_block_body(self, bw, clabel = None, blabel = None):
        """
        :type bw: CodeGenerator.BlockWrapper
        """
        for s in bw.block.statements:
            if isinstance(s, Statement):
                self.generate_statement(s, bw.stack, False, clabel, blabel)
            else:
                assert isinstance(s, VariableDeclaration)
    def generate_block(self, block, stack, function = False, clabel = None, blabel = None):
        """
        :type block: Block
        :type stack: StackFrame

        will not generate instruction to deallocate locals if function

        clabel and blabel are for continue and break
        """
        with CodeGenerator.BlockWrapper(self, block, stack, function) as bw:
            self.generate_block_body(bw, clabel, blabel)
    def generate_statement(self, stmt, stack, function = False, clabel = None, blabel = None):
        """
        :type stmt: Statement
        :type stack: StackFrame

        function is only passed to generate_block
        """
        if isinstance(stmt, Block):
            return self.generate_block(stmt, stack, function)
        if isinstance(stmt, IfStatement):
            l_if = '.if' + str(self.ifc)
            l_else = '.ifelse' + str(self.ifc)
            l_end = '.ifend' + str(self.ifc)
            self.ifc += 1
            self.label(l_if)
            self.generate_condition(stmt.condition, stack, false=l_else if stmt.else_clause else l_end)
            self.generate_statement(stmt.statement, stack, False, clabel, blabel)
            if stmt.else_clause:
                self.write('jmp', l_end)
                self.label(l_else)
                self.generate_statement(stmt.else_clause, stack, False, clabel, blabel)
            self.label(l_end)
        elif isinstance(stmt, WhileLoop):
            l_begin = '.while' + str(self.whilec)
            l_end = '.endwhile' + str(self.whilec)
            self.whilec += 1
            if isinstance(stmt.statement, Block):
                with CodeGenerator.BlockWrapper(self, stmt.statement, stack) as bw:
                    self.label(l_begin)
                    self.generate_condition(stmt.condition, bw.stack, false=l_end)
                    self.generate_block_body(bw, l_begin, l_end)
                    self.write('jmp', l_begin)
                    self.label(l_end)
            elif isinstance(stmt.statement, BreakStatement):
                self.generate_statement(ExpressionStatement(stmt.condition), stack)
            elif isinstance(stmt.statement, ContinueStatement) or isinstance(stmt.statement, EmptyStatement):
                # busy loop
                self.label(l_begin)
                self.generate_condition(stmt.condition, stack, true=l_begin)
            else:
                self.label(l_begin)
                self.generate_condition(stmt.condition, stack, false=l_end)
                self.generate_block_body(bw, l_begin, l_end)
                self.write('jmp', l_begin)
                self.label(l_end)
        elif isinstance(stmt, BreakStatement):
            if not blabel:
                raise CompilationError("Nowhere to break", stmt)
            self.write('jmp', blabel)
        elif isinstance(stmt, ContinueStatement):
            if not clabel:
                raise CompilationError("Nowhere to continue", stmt)
            self.write('jmp', clabel)
        elif isinstance(stmt, ReturnStatement):
            if stmt.expr is not None:
                self.push_expr(stmt.expr, stack)
            self.write('jmp', '.return')
        elif isinstance(stmt, ExpressionStatement):
            self.push_expr(stmt.expr, stack, False)
        elif isinstance(stmt, EmptyStatement):
            pass
        else:
            assert False
    def generate_condition(self, cond, stack, true=None, false=None):
        """
        :type cond: Expression
        """
        # some easy conditions
        if isinstance(cond, Unary) and cond.op == '!':
            return self.generate_condition(cond.expr, stack, false, true)
        elif isinstance(cond, Literal):
            if cond.type == 'INT_LIT':
                if cond.value == 0:
                    if false:
                        self.write('jmp', false)
                else:
                    if true:
                        self.write('jmp', true)
            elif cond.type == 'CHAR_LIT':
                if cond.value == '\0':
                    if false:
                        self.write('jmp', false)
                else:
                    if true:
                        self.write('jmp', true)
            else:
                if true:
                    self.write('jmp', true)
        elif isinstance(cond, Address):
            if true:
                self.write('jmp', true)
        elif isinstance(cond, BinaryExpression) and (cond.op in ('&&', '||', '&') or cond.op in rel_ops):
            if cond.op == '&':
                lit = None
                other = None
                if isinstance(cond.lhs, Literal):
                    lit = cond.lhs
                    other = cond.rhs
                else:
                    if isinstance(cond.rhs, Literal):
                        lit = cond.rhs
                        other = cond.lhs
                    else:
                        # neither is literal, but can still be optimized
                        self.push_expr(cond.lhs, stack)
                        self.reg_expr(cond.rhs, 'ebx', stack)
                        self.write('pop', 'eax')
                        self.write('test', 'eax,ebx')
                        if true and false:
                            self.write('je', true)
                            self.write('jmp', false)
                        elif true:
                            self.write('je', true)
                        elif false:
                            self.write('jne', false)
                if lit and other:
                    self.reg_expr(other, 'eax', stack)
                    self.write('test', 'eax,' + str(self.value('int', lit)))
                    if true and false:
                        self.write('je', true)
                        self.write('jmp', false)
                    elif true:
                        self.write('je', true)
                    elif false:
                        self.write('jne', false)
            elif cond.op in rel_ops:
                self.push_expr(cond.lhs, stack)
                self.reg_expr(cond.rhs, 'ebx', stack)
                self.write('pop', 'eax')
                self.write('cmp', 'eax,ebx')
                if true and false:
                    self.write('j' + rel_ops[cond.op], true)
                    self.write('jmp', false)
                elif true:
                    self.write('j' + rel_ops[cond.op], true)
                elif false:
                    self.write('j' + rel_ops_not[cond.op], false)
            else:
                # short-circuit
                if cond.op == '&&':
                    self.generate_condition(cond.lhs, stack, None, false)
                    self.generate_condition(cond.rhs, stack, true, false)
                else:
                    assert cond.op == '||'
                    self.generate_condition(cond.lhs, stack, true, None)
                    self.generate_condition(cond.rhs, stack, true, false)
        else:
            # otherwise use a cmp
            self.reg_expr(cond, 'eax', stack)
            self.write('cmp', 'eax,0')
            if true:
                self.write('jne', true)
            if false:
                self.write('je', false)
    def simple_lvalue(self, lvalue, reg, stack, prefix=True):
        """
        :type lvalue: SimpleLValue
        reg is a temporary register
        it is OK to change any registers that aren't
        reg or ebp before dereferencing
        """
        ident = None
        offset = 0
        if isinstance(lvalue, Identifier):
            ident = lvalue.name
        else:
            assert isinstance(lvalue, ArrayAccess)
            ident = lvalue.array
            if isinstance(lvalue.index, Literal):
                offset = self.value('int', lvalue.index)
            else:
                self.reg_expr(lvalue.index, reg, stack)
                offset = reg
        return self.lookup(stack, ident).value(offset, prefix)
    def reg_expr(self, expr, reg, stack):
        """
        :type expr: Expression
        :type reg: str
        :type stack: StackFrame

        Warning: may clobber every register but reg
        """
        if isinstance(expr, Literal):
            self.write('mov', reg + ',' + str(self.value('int', expr)))
        elif isinstance(expr, Address):
            if isinstance(expr.lvalue, SimpleLValue):
                self.write('lea', reg + ',' + self.simple_lvalue(expr.lvalue, reg, stack, False))
            else:
                assert isinstance(expr.lvalue, Dereference)
                self.warn('Will not attempt to dereference', expr)
                self.reg_expr(expr.lvalue.expr, reg, stack)
        elif isinstance(expr, LValue):
            if isinstance(expr, SimpleLValue):
                val = self.simple_lvalue(expr, reg, stack)
                if val.startswith('byte'):
                    creg = int_to_char.get(reg, 'al')
                    self.write('mov', creg + ',' + val)
                    self.write('movsx', reg + ',' + creg)
                else:
                    self.write('mov', reg + ',' + val)
            else:
                assert isinstance(expr, Dereference)
                self.reg_expr(expr.expr, reg, stack)
                if not expr.char:
                    self.write('mov', reg + ',dword[' + reg + ']')
                else:
                    creg = int_to_char.get(reg, 'al')
                    self.write('mov', creg + ',byte[' + reg + ']')
                    self.write('movsx', reg + ',' + creg)
        elif isinstance(expr, Unary):
            self.reg_expr(expr.expr, reg, stack)
            if expr.op == '!':
                self.write('cmp', reg + ',0')
                breg = int_to_char.get(reg, 'al')
                self.write('sete', breg)
                self.write('movzx', reg + ',' + breg)
            elif expr.op == '~':
                self.write('not', reg)
            elif expr.op == '-':
                self.write('neg', reg)
        elif isinstance(expr, BinaryExpression):
            # lhs, op, rhs
            ireg = 'eax' if reg != 'eax' else 'ebx'
            if expr.op == '*': # signed
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg, stack)
                self.write('pop', reg)
                self.write('imul', reg + ',' + ireg)
            elif expr.op == '#': # unsigned
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, 'ebx', stack)
                self.write('pop', 'eax')
                self.write('mul', 'ebx')
                self.write('mov', reg + ',' + 'eax')
            elif expr.op in '/\\%@':
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, 'ebx', stack)
                self.write('pop', 'eax')
                self.write('cdq')
                self.write('idiv' if expr.op in '/%' else 'div', 'ebx')
                self.write('mov', reg + ',' + ('eax' if expr.op in '/\\' else 'edx'))
            elif expr.op in '+-':
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg, stack)
                self.write('pop', reg)
                self.write('add' if expr.op == '+' else 'sub', reg + ',' + ireg)
            elif expr.op in ('<<', '>>', '>>>'):
                inst = 'sar' if expr.op == '>>>' else ('shl' if expr.op == '<<' else 'shr')
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg, stack)
                self.write('pop', reg)
                self.write(inst, reg + ',' + ireg)
            elif expr.op in '&|^':
                inst = 'xor' if expr.op == '^' else ('and' if expr.op == '&' else 'or')
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg, stack)
                self.write('pop', reg)
                self.write(inst, reg + ',' + ireg)
            elif expr.op in rel_ops:
                inst = 'set' + rel_ops[expr.op]
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg, stack)
                self.write('pop', reg)
                self.write('cmp', reg + ',' + ireg)
                creg = int_to_char.get(reg, 'al')
                self.write(inst, creg)
                self.write('movzx', reg + ',' + creg)
            elif expr.op in ('&&', '||'):
                # use a condition
                l_false = '.l' + str(self.labelc)
                l_end = '.l' + str(self.labelc + 1)
                self.labelc += 2
                self.generate_condition(expr, stack, None, l_false)
                self.write('mov', reg +',1')
                self.write('jmp', l_end)
                self.write('mov', reg + ',0', l_false)
                self.label(l_end)
            else:
                assert expr.op == '='
                assert isinstance(expr.lhs, LValue)
                self.push_expr(expr.rhs, stack)
                if isinstance(expr.lhs, SimpleLValue):
                    lval = self.simple_lvalue(expr.lhs, ireg, stack)
                    self.write('pop', reg)
                    if lval.startswith('byte'):
                        if reg in int_to_char:
                            creg = int_to_char[reg]
                            self.write('movsx', reg + ',' + creg)
                        else:
                            creg = 'al'
                            self.write('mov', 'eax', + reg)
                            self.write('movsx', reg + ',al')
                        self.write('mov', lval + ',' + creg)
                    else:
                        self.write('mov', lval + ',' + reg)
                else:
                    assert isinstance(expr.lhs, Dereference)
                    self.reg_expr(expr.lhs.expr, ireg, stack)
                    self.write('pop', reg)
                    if not expr.lhs.char:
                        self.write('mov', 'dword[' + ireg + '],' + reg)
                    else:
                        if reg not in int_to_char:
                            creg = 'al'
                            self.write('mov', 'eax,' + reg)
                            self.write('movsx', reg + ',al')
                        else:
                            creg = int_to_char[reg]
                            self.write('movsx', reg + ',' + creg)
                        self.write('mov', 'byte[' + ireg + '],' + creg)
        else:
            assert isinstance(expr, FunctionCall)
            self.push_expr(expr, stack, stack)
            self.write('pop', reg)
    def push_expr(self, expr, stack, push = True):
        """
        :type expr: Expression

        Warning: may clobber every register
        """
        if isinstance(expr, FunctionCall):
            fname = expr.name
            if fname.startswith('$'):
                try:
                    sysc = syscalls[fname]
                except KeyError:
                    raise CompilationError("Unknown syscall: " + fname, expr)
                # on linux, prevent clobbering
                for arg in reversed(expr.args):
                    self.push_expr(arg, stack)
                if self.linux:
                    if len(expr.args) == 6:
                        self.write('push', 'ebp')
                    if len(expr.args) > 6:
                        raise CompilationError("More than 6 arguments to linux syscall", expr)
                    for arg, reg in zip(expr.args, ('ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')):
                        self.write('pop', reg)
                else:
                    self.write('push', 'dword 0')
                self.write('mov', 'eax,' + str(sysc))
                self.write('int', '80h')
                if self.linux:
                    if len(expr.args) == 6:
                        self.write('pop', 'ebp')
                else:
                    self.write('add', 'esp,' + str(4 * len(expr.args) + 4))
                if push:
                    self.write('push', 'eax')
            else:
                try:
                    func = self.gfuncs[fname]
                except KeyError:
                    raise CompilationError("Function does not exist: " + fname, expr)
                if isinstance(func.type, Void) and push:
                    raise CompilationError(repr(func) + " does not return a value", expr)
                if isinstance(func, CFunction):
                    self.write('mov', 'eax,esp')
                    self.write('and', 'esp,0fffffff0h')
                    pn = len(expr.args)
                    if (pn & 3) != 3:
                        self.write('sub', 'esp,' + str(4 * (3 - (pn & 3))))
                    self.write('push', 'eax')
                if not isinstance(func, CFunction) or not func.varargs:
                    if len(func.par_list) != len(expr.args):
                        raise CompilationError("Incorrect number of arguments to " + func.prototype(), expr)
                else:
                    if len(expr.args) < len(func.par_list):
                        raise CompilationError("Not enough arguments to " + func.prototype(), expr)
                for arg in reversed(expr.args):
                    self.push_expr(arg, stack)
                if isinstance(func, CFunction):
                    # ebx is callee-save
                    self.write('call', '_' + fname)
                    self.write('mov', 'esp,[esp+' + str(4*pn) + ']')
                    if push:
                        self.write('push', 'eax')
                else:
                    self.write('call', '?@' + fname)
                    if not isinstance(func.type, Void) and not push:
                        self.write('add', 'esp,4')
        elif isinstance(expr, Literal):
            self.write('push', str(self.value('int', expr)))
        else:
            self.reg_expr(expr, 'eax', stack)
            if push:
                self.write('push', 'eax')
    def generate_exports(self):
        for exp in self.exports:
            self.write('GLOBAL ' + ('?@' if exp.function else '') + exp.name)
        if 'main' in self.gfuncs:
            self.write('GLOBAL ?@main')
    def lookup(self, stack, name):
        if name in stack:
            return stack[name]
        if name in self.gvars:
            return self.gvars[name]
        raise CompilationError("No such variable: " + name, None)
    def generate_externs(self):
        for ext in self.externs:
            ename = ext.name
            if ext.c is not None:
                if ext.c != 'C' and ext.c != 'c':
                    raise CompilationError("Invalid extern", ext)
                ename = self.c_prefix + ename
            if ext.is_var:
                self.gvars[ext.name] = GlobalStackEntry(ext.type, ename)
            else:
                if ext.c:
                    self.gfuncs[ext.name] = CFunction(ext)
                else:
                    if ext.varargs:
                        raise CompilationError("Native functions do not support varargs")
                    ename = '?@' + ext.name
                    self.gfuncs[ext.name] = Function(ext.type, ext.name, ext.par_list)
            self.write('EXTERN ' + ename)

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        try:
            generate(fn)
        except CompilationError as err:
            sys.stdout.write("ERROR in " + fn + ": ")
            sys.stdout.write(str(err))
            sys.stdout.write('\n')
            sys.exit(1)
