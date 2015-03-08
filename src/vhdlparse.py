# An implementation of Dartmouth BASIC (1964)
#

from ply import *
import vhdllex

tokens = vhdllex.tokens

def p_vhdl(p):
	'''vhdl : ENTITY ID LBRACE ports_list RBRACE'''
	print "find VHDL"
	
def p_ports_list(p):
	'''ports_list : ports
				  | ports COMMA ports_list'''
	print "find ports list"
	
def p_ports(p) :
	'''ports : GENERIC
			 | IN
			 | OUT'''
	print "find port"
	
def p_generic(p) :
	'''generic : GENERIC COLON LBRACKET port_list RBRACKET'''
	print "find generic"
	
def p_in(p) :
	'''in : IN COLON LBRACKET port_list RBRACKET'''
	print "find in"

def p_out(p) :
	'''out : OUT COLON LBRACKET port_list RBRACKET'''
	print "find out"
	
def p_port_list(p):
	'''port_list : port
				 | port COMMA port_list'''
	print "find port list"

def p_port(p) :
	'''port : ID COLON state'''
	print p[0]
	
def p_state(p) :
	'''state : std_logic
			 | natural'''
	print "find std logic natural"
	
def p_std_logic(p) :
	'''std_logic : INTEGER
				 | INTEGER ARROW STDLOGIC'''
	print "find std_logic"

def p_natural(p) :
	'''natural : NATURAL
			   | NATURAL LPAREN INTEGER RPAREN'''
	print "find natural"
	
bparser = yacc.yacc()

def parse(data,debug=0):
    bparser.error = 0
    p = bparser.parse(data,debug=debug)
    if bparser.error: return None
    return p
	



       
   
  
            






