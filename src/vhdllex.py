from ply import *

import logging
logging.basicConfig(
    level = logging.DEBUG,
    filename = "lexlog.txt",
    filemode = "w",
    format = "%(filename)10s:%(lineno)4d:%(message)s"
)

log = logging.getLogger()

keywords = (
    'ENTITY','COMPONENT','GENERIC','SLAVE','MASTER','NATURAL','BUS','ARCH'
)

tokens = keywords + (
    'ID','INTEGER','STRING',
    # Structure dereference (->)
    'ARROW',

    # Conditional operator (?)
    'CONDOP',
    
    # Delimeters ( ) [ ] { } , . ; :
    'LPAREN', 'RPAREN',
    'LBRACKET', 'RBRACKET',
    'LBRACE', 'RBRACE',
    'COMMA', 'PERIOD', 'SEMI', 'COLON'

)

t_ignore = ' \t\x0c'
t_ignore_comment = '\#.*'

def t_NEWLINE(t):
	r'\n+'
	t.lexer.lineno += t.value.count("\n")

def t_comment(t):
	r'\#.*'

keywords_map = { }
for r in keywords:
	keywords_map[r.lower()] = r

def t_ID(t):
	r'[A-Za-z_][\w_]*'
	t.type = keywords_map.get(t.value,"ID")
	return t

t_INTEGER = r'\d+'
t_STRING  = r'\".*?\"'
t_ARROW   = r'->'

# ?
t_CONDOP           = r'\?'

# Delimeters
t_LPAREN           = r'\('
t_RPAREN           = r'\)'
t_LBRACKET         = r'\['
t_RBRACKET         = r'\]'
t_LBRACE           = r'\{'
t_RBRACE           = r'\}'
t_COMMA            = r','
t_PERIOD           = r'\.'
t_SEMI             = r';'
t_COLON            = r':'

def t_error(t):
    print("Illegal character %s" % repr(t.value[0]))
    print t.type,t.lexer.lineno
    t.lexer.skip(1)

lexer = lex.lex(debug=False)

if __name__ == "__main__":
    lex.runmain(lexer)



