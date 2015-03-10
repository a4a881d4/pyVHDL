from ply import *
import vhdllex

tokens = vhdllex.tokens

def itemATlistHead(p) :
	if len(p) == 2 and p[1]:
		p[0] = { }
		line,stat = p[1]
		p[0][line] = stat
	elif len(p) >3 :
		p[0] = p[3]
		if p[1]:
			line,stat = p[1]
			p[0][line] = stat
	return p[0]

def p_vhdl(p) :
	'''vhdl : vhdl statement
	        | statement'''
	if len(p) == 2 and p[1]:
		p[0] = { }
		line,stat = p[1]
		if not p[0].has_key(line):
			p[0][line] = []
		p[0][line].append(stat)
	elif len(p) >2:
		p[0] = p[1]
		if p[2]:
			line,stat = p[2]
		if not p[0].has_key(line):
			p[0][line] = []
		p[0][line].append(stat)
	
def p_statement(p) :
	'''statement : entity
	             | arch
	             | bus'''
	p[0] = p[1]

def p_bus(p) :
	'''bus : BUS ID LBRACE ports_list RBRACE'''
	p[0] = ( 'bus',(p[2],p[4]) )
	
def p_entity(p):
	'''entity : ENTITY ID LBRACE ports_list RBRACE'''
	p[0] = ( 'entity',(p[2],p[4]) )

def p_arch(p):
	'''arch : ARCH ID LBRACE arch_struct RBRACE'''
	p[0] = ( 'arch',(p[2],p[4]) )
	
def p_ports_list(p):
	'''ports_list : ports
	              | ports COMMA ports_list'''
	p[0] = itemATlistHead(p)

def p_ports(p) :
	'''ports : generic
	         | slave
	         | master'''
	p[0] = p[1]

def p_generic(p) :
	'''generic : GENERIC COLON LBRACKET port_list RBRACKET'''
	p[0] = ( 'generic', p[4] )
	
def p_slave(p) :
	'''slave : SLAVE COLON LBRACKET port_list RBRACKET'''
	p[0] = ( 'slave', p[4] )

def p_master(p) :
	'''master : MASTER COLON LBRACKET port_list RBRACKET'''
	p[0] = ( 'master', p[4] )

def p_port_list(p):
	'''port_list : port
				 | port COMMA port_list'''
	p[0] = itemATlistHead(p)

def p_port(p) :
	'''port : ID COLON state'''
	p[0] = ( p[1], p[3] )
	
def p_state(p) :
	'''state : std_logic
	         | natural
	         | bus_statement'''
	p[0] = p[1]
	
def p_std_logic(p) :
	'''std_logic : INTEGER
	             | INTEGER ARROW STRING'''
	width = 0
	p[0] = {}
	if p[1]:
		width = int(p[1])
	if width == 1:
		p[0] = { 'type':'std_logic' }
	elif width > 1:
		p[0] = { 'type':'std_logic_vector', 'width':width }
	if len(p) == 4:
		p[0]['init'] = p[3]	
		

def p_natural(p) :
	'''natural : NATURAL
			   | NATURAL LPAREN INTEGER RPAREN'''
	p[0] = { 'type':'natural' }
	if len(p) == 5:
		p[0]['init'] = int(p[3])
		
def p_bus_statement(p) :
	'''bus_statement : BUS LPAREN ID RPAREN'''
	p[0] = { 'type':'bus' }
	p[0]['id'] = p[3]
	
def p_error(p):
	print "error :"
	
bparser = yacc.yacc(debug=True)

def parse(data,debug=0):
	bparser.error = 0
	p = bparser.parse(data,debug=debug)
	if bparser.error: return None
	return p
