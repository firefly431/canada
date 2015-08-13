import functools
import canadaparse

from canadaparse import Program, GlobalDeclaration, GlobalVariable, VariableType, PrimitiveType, Void, ArrayDeclaration, ArrayLiteral, Function, BlockStatement, Statement, EmptyStatement, IfStatement, WhileLoop, BreakStatement, ContinueStatement, ReturnStatement, VariableDeclaration, Block, Expression, ExpressionStatement, Literal, BinaryExpression, FunctionCall, LValue, SimpleLValue, Identifier, Dereference, Address, ArrayAccess, Negate, Export

class StackEntry:
    def __init__(self, var, addr):
        """
        :type var: VariableDeclaration
        :type addr: int
        """
        self.var = var
        self.addr = addr
        self.next = addr - var.type.size()
    def value(self):
        return '[ebp' + ('+' + str(self.addr) if self.addr > 0 else str(self.addr)) + ']'

class StackFrame:
    def __init__(self, parameters):
        if parameters is None: return
        self.stack = [StackEntry(VariableDeclaration(PrimitiveType('int'), p), 8 + 4 * i) for i, p in reversed(list(enumerate(parameters)))]
        self.table = {p.var.name: p for p in self.stack}
        if self.stack:
            self.stack[-1].next = -4
    def _extend(self, variables):
        oldn = self.stack[-1].next if self.stack else -4
        for v in variables:
            self.stack.append(StackEntry(v, self.stack[-1].next if self.stack else -4))
        ret = oldn - (self.stack[-1].next if self.stack else -4)
        self.table = {p.var.name: p for p in self.stack}
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
        ret = -last.next - 4
        assert ret == sum(a.var.type.size() for a in self.stack if a.addr > 0)
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
    def __init__(self, out, margin=16, iwidth=8, width=40):
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
    def warn(self, warning):
        import sys
        sys.stderr.write('WARNING: ' + warning + '\n')
    def label(self, label):
        if not label: return
        if self._label:
            self.write(label=self._label)
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
        self.generate_text()
        self.generate_data()
        self.generate_exports()
        for name, var in sorted(self.gvars.items()):
            print(repr(var))
        for name, func in sorted(self.gfuncs.items()):
            print(repr(func))
        for exp in self.exports:
            print(repr(exp))
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
                    raise SyntaxError("%d too big to fit in char" %
                                      v.value)
                return v.value
            elif v.type == 'CHAR_LIT':
                return ord(v.value)
            else:
                raise SyntaxError("String literal cannot be a char")
    def generate_variable(self, v):
        """
        Generate the instructions for a variable
        :type v: GlobalVariable
        """
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
                        raise SyntaxError("String literal wrong "
                                          "size")
                    self.write('db', "'" + v.value.value + "'", label=v.name)
                else:
                    raise SyntaxError("Array not initialized with "
                                      "array literal")
            else:
                if not arr_size:
                    arr_size = len(v.value.elements)
                    v.var_type.length = arr_size
                if len(v.value.elements) != arr_size:
                    raise SyntaxError("Array literal wrong size")
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
            _, jf = self.generate_condition(stmt.condition)
            self.write(jf, l_else)
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
                    _, jf = self.generate_condition(stmt.condition)
                    self.write(jf, l_end)
                    self.generate_block_body(bw, l_begin, l_end)
                    self.write('jmp', l_begin)
                    self.label(l_end)
            elif isinstance(stmt.statement, BreakStatement):
                self.generate_statement(ExpressionStatement(stmt.condition))
            elif isinstance(stmt.statement, ContinueStatement) or isinstance(stmt.statement, EmptyStatement):
                # busy loop
                self.label(l_begin)
                jt, _ = self.generate_condition(stmt.condition)
                self.write(jt, l_begin)
            else:
                self.label(l_begin)
                _, jf = self.generate_condition(stmt.condition)
                self.write(jf, l_end)
                self.generate_block_body(bw, l_begin, l_end)
                self.write('jmp', l_begin)
                self.label(l_end)
        elif isinstance(stmt, BreakStatement):
            if not blabel:
                raise SyntaxError("Nowhere to break")
            self.write('jmp', blabel)
        elif isinstance(stmt, ContinueStatement):
            if not clabel:
                raise SyntaxError("Nowhere to continue")
            self.write('jmp', clabel)
        elif isinstance(stmt, ReturnStatement):
            a = ReturnStatement()
            if stmt.expr is not None:
                self.push_expr(stmt.expr)
            self.write('jmp', '.return')
        elif isinstance(stmt, ExpressionStatement):
            self.push_expr(stmt.expr)
            self.write('pop', 'eax')
        elif isinstance(stmt, EmptyStatement):
            pass
        else:
            assert False
    def generate_condition(self, cond):
        """
        :type cond: Expression

        returns jump true, jump false
        e.g. jnz, jz
        """
        # some easy conditions
        if isinstance(cond, Negate):
            a, b = self.generate_condition(cond.expr)
            return b, a
        if isinstance(cond, Literal):
            if cond.type == 'INT_LIT':
                if cond.value == 0:
                    return None, 'jmp'
                else:
                    return 'jmp', None
            elif cond.type == 'CHAR_LIT':
                if cond.value == '\0':
                    return None, 'jmp'
                else:
                    return 'jmp', None
            else:
                return 'jmp', None
        if isinstance(cond, Address):
            return 'jmp', None
        # otherwise use a cmp
        self.push_expr(cond)
        self.write('pop', 'eax')
        self.write('cmp', 'eax,0')
        return 'jnz', 'jz'
    def push_expr(self, expr):
        """
        :type expr: Expression
        """
        self.write('push', '0')
    def generate_exports(self):
        for exp in self.exports:
            self.write('GLOBAL ' + ('?@' if exp.function else '') + exp.name)

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        generate(fn)
