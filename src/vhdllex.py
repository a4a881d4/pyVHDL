# An implementation of Dartmouth BASIC (1964)

from ply import *

keywords = (
    'ENTITY','COMPONENT','GENERIC','IN','OUT','NATURAL',
)

tokens = keywords + (
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

t_ignore = ' \t'

def t_NEWLINE(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")
	
def t_ID(t):
    r'[A-Za-z][A-Za-z0-9]*'
    if t.value in keywords:
        t.type = t.value
    return t
    
t_INTEGER = r'\d+'    
t_STRING  = r'\".*?\"'
t_STDLOGIC  = r'\"[01]?\"'
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

def t_NEWLINE(t):
    r'\n'
    t.lexer.lineno += 1
    return t

def t_error(t):
    print("Illegal character %s" % t.value[0])
    t.lexer.skip(1)

lexer = lex.lex(optimize=1)
if __name__ == "__main__":
    lex.runmain(lexer)







       
   
  
            






