from ply import *
import vhdllex

tokens = vhdllex.tokens

def p_vhdl(p) :
	'''vhdl : entity'''
	
def p_entity(p):
	'''entity : ENTITY ID LBRACE ports_list RBRACE'''
	
def p_ports_list(p):
	'''ports_list : ports
				  | ports COMMA ports_list'''
	
def p_ports(p) :
	'''ports : generic
			 | in
			 | out'''
	
def p_generic(p) :
	'''generic : GENERIC COLON LBRACKET port_list RBRACKET'''
	
def p_in(p) :
	'''in : IN COLON LBRACKET port_list RBRACKET'''

def p_out(p) :
	'''out : OUT COLON LBRACKET port_list RBRACKET'''
	
def p_port_list(p):
	'''port_list : port
				 | port COMMA port_list'''

def p_port(p) :
	'''port : ID COLON state'''
	
def p_state(p) :
	'''state : std_logic
			 | natural'''
	
def p_std_logic(p) :
	'''std_logic : INTEGER
				 | INTEGER ARROW STDLOGIC'''

def p_natural(p) :
	'''natural : NATURAL
			   | NATURAL LPAREN INTEGER RPAREN'''

def p_error(p):
	print "error :", repr(p[0])
	
bparser = yacc.yacc(debug=True,debuglog=vhdllex.log)

def parse(data,debug=0):
	bparser.error = 0
	p = bparser.parse(data,debug=debug)
	if bparser.error: return None
	return p
