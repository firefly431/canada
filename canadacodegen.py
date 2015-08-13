import functools
import canadaparse

from canadaparse import Program, GlobalDeclaration, GlobalVariable, VariableType, PrimitiveType, Void, ArrayDeclaration, ArrayLiteral, Function, BlockStatement, Statement, BreakStatement, ContinueStatement, ReturnStatement, VariableDeclaration, Block, Expression, ExpressionStatement, Literal, BinaryExpression, FunctionCall, LValue, SimpleLValue, Identifier, Dereference, Address, ArrayAccess

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
        self.loopc = 0
        self.ifc = 0
        self.stringc = 0
        self.gvars = {}
        self.gfuncs = {}
        self.functions = []
        self.variables = []
    def write(self, inst = None, code = None, label=None, comment=None):
        """
        :type inst: str
        :type code: str
        :type label: str
        :type comment: str
        """
        if not inst:
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
        assert all((x in self.variables) ^ (x in self.functions) for x in ast.decls)
        self.generate_text()
        self.generate_data()
        for name, type in sorted(self.gvars.items()):
            print(repr(type), name)
        print(self.gfuncs)
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
        self.gvars[v.name] = v.var_type
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
        pass

if __name__ == '__main__':
    import sys
    for fn in sys.argv[1:]:
        generate(fn)
