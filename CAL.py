
import os,sys,time

def comment(text,width=80):
    print( '#'*(width-len(text)-1) + ' ' + text )
# comment('global environment')


########################################### Marvin Minsky's extended frame model

class Frame:
    def __init__(self,V):
        self.type = self.__class__.__name__.lower()
        self.val  = V
        self.slot = {}
        self.nest = []

    def __repr__(self): return self.dump()
    def dump(self,depth=0,prefix=''):
        tree = self.pad(depth) + self.head(prefix)
        for i in self.slot:
            tree += self.slot[i].dump(depth+1,prefix='%s = '%i)
        idx = 0
        for j in self.nest:
            tree += j.dump(depth+1,prefix='%s : '%idx) ; idx += 1
        return tree
    def head(self,prefix):
        return '%s<%s:%s> @%x' % (prefix,self.type,self._val(),id(self))
    def pad(self,depth):
        return '\n' + '\t' * depth
    def _val(self):
        return '%s' % self.val

    def __getitem__(self,key):
        return self.slot[key]
    def __setitem__(self,key,that):
        if callable(that): return self.__setitem__(key,Cmd(that))
        self.slot[key] = that ; return self
    def __floordiv__(self,that):
        self.nest.append(that) ; return self

    def top(self): return self.nest[-1]
    def pop(self): return self.nest.pop(-1)

##################################################################### primitives

class Primitive(Frame):
    def eval(self,env): return env // self

class Symbol(Primitive): pass
class String(Primitive): pass
class Number(Primitive): pass
class Integer(Number): pass
class Hex(Integer): pass
class Bin(Integer): pass

##################################################################### containers

class Container(Frame): pass
class Vector(Container): pass
class Dict(Container): pass
class Stack(Container): pass
class Queue(Container): pass

############################################################################ I/O

class IO(Frame): pass

######################################################################## network

class Net(IO): pass
class Socket(Net): pass

class IP(Net,Primitive): pass
class Port(Net,Primitive): pass
class Email(Net,Primitive): pass
class Url(Net,Primitive): pass

################################################# EDS: Executable Data Structure

class Active(Frame): pass
class Seq(Active,Vector): pass

class Cmd(Active):
    def __init__(self,F):
        Active.__init__(self,F.__name__)
        self.fn = F
    def eval(self,env):
        return self.fn(env)

class VM(Active): pass

############################################################# global environment

vm = VM('CAL')

########################################################################## debug

def BYE(env): sys.exit(0)

def Q(env): print(env)
vm['?'] = Q

def QQ(env): print(env) ; BYE(env)
vm['??'] = QQ

################################################################## manipulations

def EQ(env): addr = env.pop().val ; env[addr] = env.pop()
vm['='] = EQ

def PUSH(env): that = env.pop() ; env.top() // that
vm['//'] = PUSH

######################################################### no-syntax parser /PLY/

import ply.lex as lex

tokens = ['symbol','string','integer','email','url','ip']

t_ignore = ' \t\r\n'
t_ignore_comment = r'[#\\].*\n'

states = (('str','exclusive'),)

t_str_ignore = ''

def t_str(t):
    r'\''
    t.lexer.string = '' ; t.lexer.push_state('str')
def t_str_str(t):
    r'\''
    t.lexer.pop_state() ; return String(t.lexer.string)
def t_str_anychar(t):
    r'.'
    t.lexer.string += t.value

def t_email(t):
    r'\w+@(\w+\.)+\w+'
    return Email(t.value)

def t_url(t):
    r'https?://[^ \t\r\n\#\\]+'
    return Url(t.value)

def t_ip(t):
    r'\d+\.\d+\.\d+\.\d+'
    return IP(t.value)

def t_integer(t):
    r'[+\-]?\d+'
    return Integer(t.value)

def t_symbol(t):
    r'[`]|[^ \t\r\n\#\\]+'
    return Symbol(t.value)

def t_ANY_error(t): raise SyntaxError(t)

lexer = lex.lex()

#################################################################### interpreter

def WORD(env):
    token = lexer.token()
    if token: env // token
    return token
vm['`'] = WORD

def FIND(env):
    token = env.pop()
    try:             env // env[token.val] ; return True
    except KeyError: env // token          ; return False

def EVAL(env): env.pop().eval(env)

def INTERP(env):
    lexer.input(env.pop().val)
    while True:
        if not WORD(env): break
        if isinstance(env.top(),Symbol):
            if not FIND(env): raise SyntaxError(env.top())
        EVAL(env)
    print(env)

################################################################## web interface

class Web(Net):
    def eval(self,env):
        from flask import Flask,Response,render_template
        app = Flask(self.val)

        @app.route('/')
        def index(): return render_template('index.html',env=env)

        @app.route('/css.css')
        def css(): return Response(render_template('css.css',env=env),mimetype='text/css')

        @app.route('/logo.png')
        def logo(): return app.send_static_file('logo.png')

        app.run(host=env['IP'].val,port=env['PORT'].val,debug=True)

class Font(Web): pass
class Color(Web): pass

def _WEB(env): web = Web(env.val) ; env['WEB'] = web ; web.eval(env)
vm['WEB'] = _WEB

################################################################# system startup

if __name__ == '__main__':
    print(sys.argv)
    for infile in sys.argv[1:]:
        with open(infile) as src:
            vm // String(src.read()) ; INTERP(vm)
