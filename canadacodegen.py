import functools
import canadaparse

from canadaparse import Program, GlobalDeclaration, GlobalVariable, VariableType, PrimitiveType, Void, ArrayDeclaration, ArrayLiteral, Function, BlockStatement, Statement, EmptyStatement, IfStatement, WhileLoop, BreakStatement, ContinueStatement, ReturnStatement, VariableDeclaration, Block, Expression, ExpressionStatement, Literal, BinaryExpression, FunctionCall, LValue, SimpleLValue, Identifier, Dereference, Address, ArrayAccess, Negate, Export
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
    '<|=', 'be',
    '==': 'e',
    '!=': 'ne',
}

class ChangeThisNameError(Exception):
    def __init__(self, message, source):
        super().__init__(self, message)
        self.source = source

class StackEntry:
    def __init__(self, var, addr):
        """
        :type var: VariableDeclaration
        :type addr: int
        """
        self.var = var
        self.addr = addr
    def value(self, offset=0):
        if isinstance(offset, str):
            return self.value()[:-1] + '+' + offset + ']'
        offset += self.addr
        return '[ebp' + ('+' + str(offset) if offset > 0 else str(offset)) + ']'
    def __str__(self):
        return '<' + repr(self.var) + ' at ' + self.value() + '>'

class GlobalStackEntry(StackEntry):
    def __init__(self, var):
        """
        :type var: GlobalVariable
        """
        super().__init__(VariableDeclaration(var.var_type, var.name), var.name)
        self.name = var.name
    def value(self, offset=0):
        if isinstance(offset, str):
            return '[' + self.name + '+' + offset + ']'
        return '[' + self.name + ('+' + str(offset) if offset > 0 else str(offset)) + ']'

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
    def __init__(self, out, margin=16, iwidth=8, width=40, linux=None):
        self.out = out
        self.margin = margin
        self.iwidth = iwidth
        self.width = width
        self.whilec = 0
        self.ifc = 0
        self.stringc = 0
        self.gvars = {}
        self.gfuncs = {}
        self.functions = []
        self.variables = []
        self.exports = []
        self._label = None
        if linux is not None:
            self.linux = linux
        else:
            # autodetect
            import os
            sysname = os.uname()[0]
            if sysname == 'Linux':
                self.linux = True
            elif sysname == 'FreeBSD':
                self.linux = False
            elif sysname == 'Darwin':
                self.linux = False
            else:
                self.linux = False
                raise Exception("Unknown uname: " + sysname)
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
        assert all(sum((x in self.variables, x in self.functions, x in self.exports)) == 1 for x in ast.decls)
        self.generate_exports()
        self.generate_text()
        self.generate_data()
        for exp in self.exports:
            print(repr(exp))
        for name, var in sorted(self.gvars.items()):
            print(repr(var))
        for name, func in sorted(self.gfuncs.items()):
            print(repr(func))
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
                    raise ChangeThisNameError("%d too big to fit in char" %
                                      v.value, v)
                return v.value
            elif v.type == 'CHAR_LIT':
                return ord(v.value)
            else:
                raise ChangeThisNameError("String literal cannot be a char", v)
    def generate_variable(self, v):
        """
        Generate the instructions for a variable
        :type v: GlobalVariable
        """
        if v.name == '_start':
            raise ChangeThisNameError('Reserved name', v)
        self.gvars[v.name] = v
        prim_type = v.var_type if isinstance(v.var_type, PrimitiveType) else v.var_type.prim_type
        dd = 'db' if prim_type == 'char' else 'dw'
        if isinstance(v.var_type, ArrayDeclaration):
            arr_size = v.var_type.length
            if not isinstance(v.value, ArrayLiteral):
                if isinstance(v.value, Literal) and v.value.type == 'STRING_LIT' and prim_type == 'char':
                    lit_len = len(v.value.value) - v.value.value.count('\\') + v.value.value.count('\\\\')
                    if not arr_size:
                        arr_size = lit_len
                        v.var_type.length = lit_len
                    if lit_len != arr_size:
                        raise ChangeThisNameError("String literal wrong "
                                          "size", v)
                    self.write('db', "'" + v.value.value + "'", label=v.name)
                else:
                    raise ChangeThisNameError("Array not initialized with "
                                      "array literal", v)
            else:
                if not arr_size:
                    arr_size = len(v.value.elements)
                    v.var_type.length = arr_size
                if len(v.value.elements) != arr_size:
                    raise ChangeThisNameError("Array literal wrong size", v)
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
            self.cg.write('sub', 'esp,' + str(self.bsize))
            return self
        def __exit__(self, *args):
            if not self.function:
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
            return self.generate_block(stmt, stack)
        if isinstance(stmt, IfStatement):
            l_if = '.if' + str(self.ifc)
            l_else = '.ifelse' + str(self.ifc)
            self.ifc += 1
            self.label(l_if)
            self.generate_condition(stmt.condition, stack, false=l_else)
            self.generate_statement(stmt.statement, stack, False, clabel, blabel)
            self.label(l_else)
            if stmt.else_clause:
                self.generate_statement(stmt.else_clause, stack, False, clabel, blabel)
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
                raise ChangeThisNameError("Nowhere to break", stmt)
            self.write('jmp', blabel)
        elif isinstance(stmt, ContinueStatement):
            if not clabel:
                raise ChangeThisNameError("Nowhere to continue", stmt)
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

        returns jump true, jump false
        e.g. jnz, jz
        """
        # some easy conditions
        if isinstance(cond, Negate):
            return self.generate_condition(cond.expr, stack, false, true)
        if isinstance(cond, Literal):
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
        if isinstance(cond, Address):
            if true:
                self.write('jmp', true)
        # otherwise use a cmp
        self.reg_expr(cond, 'eax', stack)
        self.write('cmp', 'eax,0')
        if true:
            self.write('jnz', true)
        if false:
            self.write('jz', false)
    def simple_lvalue(self, lvalue, reg, stack):
        """
        :type lvalue: SimpleLValue
        reg is a temporary register
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
        return self.lookup(stack, lvalue.name).value(offset)
    def reg_expr(self, expr, reg, stack):
        """
        :type expr: Expression
        :type reg: str
        :type stack: StackFrame

        Warning: may clobber every register but reg
        """
        if isinstance(expr, Literal):
            self.write('mov', reg + ',' + self.value('int', expr))
        elif isinstance(expr, Address):
            if isinstance(expr.lvalue, SimpleLValue):
                self.write('lea', reg + ',' + self.simple_lvalue(expr.lvalue, reg, stack))
            else:
                assert isinstance(expr.lvalue, Dereference)
                self.warn('Will not attempt to dereference', expr)
                self.reg_expr(expr.lvalue.expr, reg, stack)
        elif isinstance(expr, LValue):
            if isinstance(expr.lvalue, SimpleLValue):
                self.write('mov', reg + ',' + self.simple_lvalue(expr, reg, stack))
            else:
                assert isinstance(expr.lvalue, Dereference)
                self.reg_expr(expr.expr, reg, stack)
                self.write('mov', reg + ',[' + reg + ']')
        elif isinstance(expr, Negate):
            a = 0
            while isinstance(expr.expr, Negate):
                expr = expr.expr
                a = 1 - a
            self.reg_expr(expr.expr, reg, stack)
            self.write('cmp', reg + ',0')
            breg = int_to_char.get(reg, 'al')
            self.write(('sete', 'setne')[a], breg)
            self.write('movzx', reg + ',' + breg)
        elif isinstance(expr, BinaryExpression):
            # lhs, op, rhs
            ireg = 'eax' if reg != 'eax' else 'ebx'
            if expr.op == '*': # signed
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg)
                self.write('pop', reg)
                self.write('imul', reg + ',' + ireg)
            elif expr.op == '~': # unsigned
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, 'ebx')
                self.write('pop', 'eax')
                self.write('mul', 'ebx')
                self.write('mov', reg + ',' + 'eax')
            elif expr.op in '/\\%@':
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, 'ebx')
                self.write('pop', 'eax')
                self.write('cdq')
                self.write('idiv' if expr.op in '/%' else 'div', 'ebx')
                self.write('mov', reg + ',' + ('eax' if expr.op in '/\\' else 'edx'))
            elif expr.op in '+-':
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg)
                self.write('pop', reg)
                self.write('add' if expr.op == '+' else 'sub', reg + ',' + ireg)
            elif expr.op in ('<<', '>>', '>>>'):
                inst = 'sar' if expr.op == '>>>' else ('shl' if expr.op == '<<' else 'shr')
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg)
                self.write('pop', reg)
                self.write(inst, reg + ',' + ireg)
            elif expr.op in '&|^':
                inst = 'xor' if expr.op == '^' else ('and' if expr.op == '&' else 'or')
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg)
                self.write('pop', reg)
                self.write(inst, reg + ',' + ireg)
            elif expr.op in ('<=', '>=', '<', '>', '==', '!='):
                inst = 'set' + rel_ops[expr.op]
                self.push_expr(expr.lhs, stack)
                self.reg_expr(expr.rhs, ireg)
                self.write('pop', reg)
                self.write('cmp', reg + ',' + ireg)
                self.write(inst, reg)
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
                pass
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
                    raise ChangeThisNameError("Unknown syscall: " + fname, expr)
                # on linux, prevent clobbering
                for arg in reversed(expr.args):
                    self.push_expr(arg, stack)
                if self.linux:
                    if len(expr.args) == 6:
                        self.write('push', 'ebp')
                    if len(expr.args) > 6:
                        raise ChangeThisNameError("More than 6 arguments to linux syscall", expr)
                    for arg, reg in zip(expr.args, ('ebx', 'ecx', 'edx', 'esi', 'edi', 'ebp')):
                        self.write('pop', reg)
                else:
                    self.write('push', 'dword 0')
                self.write('mov', 'eax,' + str(sysc), comment=fname)
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
                    raise ChangeThisNameError("Function does not exist: " + fname, expr)
                if len(func.par_list) != len(expr.args):
                    raise ChangeThisNameError("Incorrect number of arguments to " + repr(func), expr)
                if isinstance(func.type, Void) and push:
                    raise ChangeThisNameError(repr(func) + " does not return a value", expr)
                for arg in reversed(expr.args):
                    self.push_expr(arg, stack)
                self.write('call', '?@' + fname)
                if not isinstance(func.type, Void) and not push:
                    self.write('add', 'esp,4')
        elif isinstance(expr, Literal):
            self.write('push', self.value('int', self.expr))
        else:
            self.reg_expr(expr, 'eax', stack)
            if push:
                self.write('push', 'eax')
    def generate_exports(self):
        for exp in self.exports:
            self.write('GLOBAL ' + ('?@' if exp.function else '') + exp.name)
        self.write('GLOBAL ?@main')
    def lookup(self, stack, name):
        if name in stack:
            return stack[name]
        if name in self.gvars:
            return GlobalStackEntry(self.gvars[name])

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        generate(fn)
