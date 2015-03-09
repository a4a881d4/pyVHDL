from ply import *
import vhdllex

tokens = vhdllex.tokens

def p_vhdl(p) :
	'''vhdl : vhdl statement
	        | statement'''
	if len(p) == 2 and p[1]:
		p[0] = { }
		line,stat = p[1]
		p[0][line] = stat
	elif len(p) ==3:
		p[0] = p[1]
		if not p[0]: p[0] = { }
		if p[2]:
			line,stat = p[2]
			p[0][line] = stat

def p_statement(p) :
	'''statement : entity
	             | bus'''
	p[0] = p[1]

def p_bus(p) :
	'''bus : BUS'''
	p[0] = p[1]
	
def p_entity(p):
	'''entity : ENTITY ID LBRACE ports_list RBRACE'''
	p[0] = ( 'entity',(p[2],p[4]) )
	
def p_ports_list(p):
	'''ports_list : ports
	              | ports COMMA ports_list'''
	if len(p) == 2 and p[1]:
		p[0] = { }
		line,stat = p[1]
		p[0][line] = stat
	elif len(p) ==3:
		p[0] = p[2]
		if not p[0]: p[0] = { }
		if p[1]:
			line,stat = p[1]
			p[0][line] = stat
				
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
	print "error :"
	
bparser = yacc.yacc(debug=True,debuglog=vhdllex.log)

def parse(data,debug=0):
	bparser.error = 0
	p = bparser.parse(data,debug=debug)
	if bparser.error: return None
	return p
