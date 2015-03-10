#! /usr/bin/env python
# vim:ts=4:expandtab:sw=4:tw=0
###############################################################################
# vhdl_parser.py - lexer and parser for VHDL                                  #
#                                                                             #
# $Id: vhd2xml.py 6902 2009-02-03 13:35:57Z xrehak5 $
#                                                                             #
# Author: Ales Smrcka <smrcka@fit.vutbr.cz>                                   #
#         Zdenek Rehak <xrehak5@fi.muni.cz>                                   #
#                                                                             #
# This program is free software; you can redistribute it and/or modify        #
#   it under the terms of the GNU General Public License as published by      #
#   the Free Software Foundation; either version 2 of the License, or         #
#   (at your option) any later version.                                       #
#   See http://www.gnu.org/licenses/gpl.html for more details.                #
#                                                                             #
###############################################################################
###############################################################################
# tokens based on liberouter VHDL files
# * grammar based on VHDL Quick Reference Card (95-00,Qualis Design Corp.)
#   http://soc.eurecom.fr/EDC/vhdlref.pdf
# * 1164 pkg quick reference card: http://soc.eurecom.fr/EDC/1164pkg.pdf
# 

import sys
import os # for OS functions
from xml.dom.minidom import getDOMImplementation

###############################################################################
# LEXER
###############################################################################
import lex

# output file
DOMimplement = None
xml_document = None
top_element = None

# lexer
lexer = None

# misc
debug = False

# reserved tokens
tokens_reserved = (
    # key words
    'ENTITY', 'ARCHITECTURE', 'PACKAGE', 'CONFIGURATION', 'LIBRARY', 'USE',
    'GENERIC', 'PORT', 'BEGIN', 'END', 'IS', 'FOR', 'OF', 'ALL', 'MAP',
    'TYPE', 'RANGE', 'TO', 'DOWNTO', 'ARRAY', 'RECORD', 'BODY',
    'IN', 'OUT', 'INOUT', 'ALIAS', 'ATTRIBUTE',
    'SIGNAL', 'CONSTANT', 'COMPONENT', 'SUBTYPE', 'ACCESS',
    'VARIABLE', 'OTHERS', 'PROCEDURE', 'FUNCTION', 'LABEL',
    'PROCESS', 'IF', 'THEN', 'ELSIF', 'LOOP', 'GENERATE',
    'RETURN', 'FILE', 'NEW', 'NULL', 'WAIT', 'UNTIL', 'ON',
    'ASSERT', 'WHEN', 'NEXT', 'EXIT', 'REPORT', 'SEVERITY', 'NOTE',
    'WARNING', 'ERROR', 'FAILURE', 'TRANSPORT', 'AFTER',
    'ELSE', 'CASE', 'WHILE', 'BLOCK', 'WITH', 'SELECT',
    'GUARDED', 'REJECT',
    # VHDL-1993
    'SHARED', 'OPEN', 'READ_MODE', 'WRITE_MODE', 'APPEND_MODE',
    'IMPURE', 'PURE', 'POSTPONED', 'INERTIAL', 'UNAFFECTED',
    # binary operators
    'AND', 'NAND', 'OR', 'NOR', 'XOR', 'XNOR',
    'MOD', 'REM', 'SLL', 'SRL', 'SLA', 'SRA', 'ROL', 'ROR',
    # unary operators
    'ABS', 'NOT',
)

# string values for reserved tokens
RESERVED_TYPES = {}
for token in tokens_reserved:
    RESERVED_TYPES[token.lower()] = token
del token

# tokens of symbols
tokens_symbols = (
    'ASSIGN', 'EXPSIGN', 'APOSTROPHE', 'CONNECT',
    'EQ', 'NEQ', 'LE', 'LT', 'GE', 'GT', 'RANGESIGN',
    # due to bug in ply-2.[0-3], DOT is a special token for '.'
    'DOT',
)

# list of all tokens (for lex)
tokens = tokens_reserved + tokens_symbols + (
    'ID', 'LITERAL', 'CLITERAL',
)

# one char literals (for lex)
literals = (
    ';', '(', ')', ',', ':',
    '+', '-', '&', '*', '/', '|',
)

# token definitions
t_ignore = " \t"

t_DOT = r'\.'
t_GE = r'>='
t_LE = r'<='
t_EQ = r'='
t_NEQ = r'/='
t_LT = r'<'
t_GT = r'>'
t_ASSIGN = r':='
t_CONNECT = r'=>'
t_EXPSIGN = r'\*\*'
t_APOSTROPHE = r'\''
t_RANGESIGN = r'<>'

# xml objects definitions


# VHDL comment or abstract specification
def t_ignore_COMMENT(t):
    r'--.*\n'
    t.lexer.lineno += 1

# int value -> str in binary
def digit2bin(value, length):
    s=''
    while value:
        s = str(value&1)+s
        value = value>>1
    s = '0'*(length-len(s))+s
    return s

    return t

def t_LITERAL(t):
    # could be:
    # 1. digit+#hexdigit+#  => integer of hexdigit in base digit+
    # 2. digit+ => integer in decimal
    # 3. digit+.digit+ => real number
    # 4. [BOX]'string' => binary, octal or hex. integer from string
    # 5. [BOX]"string" => binary, octal or hex. integer from string
    # 6. 'string' => vector of values (could be 0,1, or Z,-,...)
    # 7. "string" => any string
    r'(\d+\#[0-9a-fA-F]+\#|\d+(\.\d+)?|[BOX]?\'[^ \']*\'|[BOX]\"([^\\\n]|(\\.))*?\")'
    return t

def t_CLITERAL(t):
    # "string" => any string
    r'\"([^\\\n]|(\\.))*?\"'
    return t

# VHDL ID - regexp is compatible with key words, 
# token type must be distinguished
def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    if t.value.upper() in tokens_reserved:
        t.type = t.value.upper()
    t.value = t.value.lower()
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count('\n')

def t_error(t):
    print "%s:%d:illegal character '%s'" % \
        (t.lexer.filename, t.lexer.lineno, t.value[0])


###############################################################################

###############################################################################
# PARSER
###############################################################################

###############################################################################
# Functions for syntax structure
###############################################################################

# common rule for appending location information - attribute
def location(p, e, lineno=0):
    if e == None:
        return p.lineno(1)
    if lineno == 0:
        lineno = p.lineno(1)
    if debug:
        print '  tag: ' + e.tagName + ' (line: ' + str(lineno) + ')'
    e.setAttribute('line', str(lineno))

# common function to find out line nbr of target element
def getLineTarget(e):
    if e.tagName == 'objectExpression':
        return e.getAttribute('line')
    else:
        return getFirstChildLine(e)

# handy recursive function
def getFirstChildLine(e):
    first = e.firstChild
    if first.hasAttribute('line'):
        return first.getAttribute('line')
    else:
        return getFirstChildLine(first)

###############################################################################
# 0. Common Productions
###############################################################################

# start symbol - 20080707
def p_start(p):
    """start : start library"""
    if p[2]: 
        top_element.appendChild(p[2])

# start symbol empty - 20080707
def p_start_empty(p):
    """start : empty"""

# empty rule - 20080707
def p_empty(p):
    "empty :"

###############################################################################

# match: [:= expr] - 20080708 - xsd
def p_assign_expr_opt1(p):
    """assign_expr_opt : ASSIGN expr"""
    e = xml_document.createElement('value')
    e.appendChild(p[2])
    p[0] = e

# match: [:= expr] - empty - 20080809 - xsd
def p_assign_expr_opt2(p):
    """assign_expr_opt : empty"""

# match: {range,} - 20080709 - xsd
def p_range_list1(p):
    """range_list : range"""
    e = xml_document.createElement('ranges')
    e.appendChild(p[1])
    p[0] = e

# match: {range,} - 20080709 - xsd
def p_range_list2(p):
    """range_list : range_list ',' range"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# match: range - 20080711 - xsd
def p_range1(p):
    """range : expr range_dir expr"""
    e = xml_document.createElement('range')
    e.setAttribute('direction', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

# match: range - 20080728 - xsd
def p_range2(p):
    """range : '(' ID RANGE RANGESIGN ')'"""
    e = xml_document.createElement('range')
    e.setAttribute('id', p[1])
    p[0] = e

# match: to|downto - 20080708 - xsd
def p_range_dir(p):
    """range_dir : TO
                 | DOWNTO"""
    p[0] = p[1]

# match: [generic ( {ID:TYPEID [:= expr];} );] - 20080708 - xsd
def p_generic_opt1(p):
    """generic_opt : GENERIC '(' id_type_expr_list ')' ';'"""
    p[0] = p[3]

# match: [generic ( {ID:TYPEID [:= expr];} );] - 20080809 - xsd
def p_generic_opt2(p):
    """generic_opt : empty"""

# match: {ID:TYPEID [:= expr];} - 20080708 - xsd
def p_id_type_expr_list1(p):
    """id_type_expr_list : id_type_expr"""
    e = xml_document.createElement('generic')
    e.appendChild(p[1])
    p[0] = e

# match: {ID:TYPEID [:= expr];} - 20080708 - xsd
def p_id_type_expr_list2(p):
    """id_type_expr_list : id_type_expr_list ';' id_type_expr"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# match: ID:TYPEID [:= expr] - 20080809 - xsd
def p_id_type_expr(p):
    """id_type_expr : ID ':' typeid assign_expr_opt"""
    e = xml_document.createElement('parameter')
    location(p, e)
    e.setAttribute('id', p[1])
    e.appendChild(p[3])
    if p[4] != None:
        e.appendChild(p[4])
    p[0] = e

# match: [port ( {ID: in|out|inout TYPEID [:= expr];} );] - 20080708 - xsd
def p_port_opt1(p):
    """port_opt : PORT '(' id_port_type_expr_list ')' ';'"""
    p[0] = p[3]

# match: ports - empty - 20080809 - xsd
def p_port_opt2(p):
    """port_opt : empty"""

# match: {ID: in|out|inout TYPEID [:= expr];} - 20080708 - xsd
def p_id_port_type_expr_list1(p):
    """id_port_type_expr_list : id_port_type_expr"""
    e = xml_document.createElement('ports')
    e.appendChild(p[1])
    p[0] = e

# 20080708 - xsd
def p_id_port_type_expr_list2(p):
    """id_port_type_expr_list : id_port_type_expr_list ';' id_port_type_expr"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# match: in|out|inout - 20080708 - xsd
def p_port_type(p):
    """port_type : IN
                 | OUT
                 | INOUT"""
    p[0] = p[1]

# match: ID: in|out|inout TYPEID [:= expr] - 20080708 - xsd
def p_id_port_type_expr(p):
    """id_port_type_expr : ID ':' port_type typeid assign_expr_opt"""
    e = xml_document.createElement('port')
    e.setAttribute('id', p[1])
    e.setAttribute('io', p[3])
    location(p, e)
    e.appendChild(p[4])
    if p[5] != None:
        e.appendChild(p[5])
    p[0] = e

# match: {[constant|variable|signal] ID : in|out|inout TYPEID [:= expr];} - 20080816 - xsd
def p_parameter_expr_list1(p):
    """parameter_expr_list : parameter_expr"""
    e = xml_document.createElement('functionParameters')
    e.appendChild(p[1])
    p[0] = e

# - 20080816 - xsd
def p_parameter_expr_list2(p):
    """parameter_expr_list : parameter_expr_list ';' parameter_expr"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# match: [constant|variable|signal] ID : in|out|inout TYPEID [:= expr] - 20081028 - xsd
def p_parameter_expr1(p):
    """parameter_expr : CONSTANT id_list ':' port_type typeid assign_expr_opt"""
    e = xml_document.createElement('constantParameter')
    e.appendChild(p[2])
    e.setAttribute('io', p[4])
    location(p, e)
    e.appendChild(p[5])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

# - 20081028 - xsd
def p_parameter_expr2(p):
    """parameter_expr : VARIABLE id_list ':' port_type typeid assign_expr_opt"""
    e = xml_document.createElement('variableParameter')
    e.appendChild(p[2])
    e.setAttribute('io', p[4])
    location(p, e)
    e.appendChild(p[5])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

# - 20081028 - xsd
def p_parameter_expr3(p):
    """parameter_expr : SIGNAL id_list ':' port_type typeid assign_expr_opt"""
    e = xml_document.createElement('signalParameter')
    e.appendChild(p[2])
    e.setAttribute('io', p[4])
    location(p, e)
    e.appendChild(p[5])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

# - 20081028 - xsd
def p_parameter_expr4(p):
    """parameter_expr : id_list ':' port_type typeid assign_expr_opt"""
    e = xml_document.createElement('idParameter')
    e.appendChild(p[1])
    e.setAttribute('io', p[3])
    location(p, e, p[1].firstChild.getAttribute('line'))
    e.appendChild(p[4])
    if p[5] != None:
        e.appendChild(p[5])
    p[0] = e

# match: {ID:TYPEID;} - 20080728 - xsd
def p_id_type_list1(p):
    """id_type_list : id_type_list ';' id_type"""
    p[1].appendChild(p[3])
    p[0] = p[1]

#- 20080728 - xsd
def p_id_type_list2(p):
    """id_type_list : id_type"""
    e = xml_document.createElement('generic')
    e.appendChild(p[1])
    p[0] = e

# match: ID:TYPEID - 20080728 - xsd
def p_id_type(p):
    "id_type : ID ':' typeid"
    e = xml_document.createElement('parameter')
    location(p, e)
    e.setAttribute('id', p[1])
    e.appendChild(p[3])
    p[0] = e

# match: {ID: in|out|inout TYPEID;} - 20080728 - xsd
def p_id_port_type_list1(p):
    """id_port_type_list : id_port_type"""
    e = xml_document.createElement('ports')
    e.appendChild(p[1])
    p[0] = e

#- 20080728 - xsd
def p_id_port_type_list2(p):
    """id_port_type_list : id_port_type_list ';' id_port_type"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# match: ID: in|out|inout TYPEID - 20080728 - xsd
def p_id_port_type(p):
    "id_port_type : ID ':' port_type typeid"
    e = xml_document.createElement('port')
    e.setAttribute('id', p[1])
    e.setAttribute('io', p[3])
    e.appendChild(p[4])
    location(p, e)
    p[0] = e

# match: [[generic map ( {ID => expr,} )] port map ( {ID => ID|expr ,} )] - 20081003 - xsd
def p_map_opt1(p):
    "map_opt : map_forced"
    p[0] = p[1]

# - 20081003 - xsd
def p_map_opt2(p):
    "map_opt : empty"

# - 20081003 - xsd
def p_map_forced(p):
    "map_forced : generic_map_opt port_map"
    p[0] = (p[1], p[2])

# match: [generic map ( {ID => expr,} )] - 20080724 - xsd
def p_generic_map_opt1(p):
    """generic_map_opt : GENERIC MAP '(' id_map_list ')'"""
    p[4].tagName = 'genericMap'
    p[0] = p[4]

# - 20080820 - xsd
def p_generic_map_opt2(p):
    """generic_map_opt : empty"""

# match: {ID => expr,} - 20080724 - xsd
def p_id_map_list1(p):
    """id_map_list : id_map"""
    e = xml_document.createElement('universalMap')
    e.appendChild(p[1])
    p[0] = e

# match: {ID => expr,} - 20080724 - xsd
def p_id_map_list2(p):
    """id_map_list : id_map_list ',' id_map"""
    p[1].appendChild(p[3])
    p[0] = p[1]

#match: ID => expr - 20080919 - xsd
def p_id_map1(p):
    """id_map : id_object CONNECT expr"""
    e = xml_document.createElement('map')
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#match: ID => open - 20080919 - xsd
def p_id_map2(p):
    """id_map : id_object CONNECT OPEN"""
    e = xml_document.createElement('map')
    e.appendChild(p[1])
    e1 = xml_document.createElement(p[3])
    e.appendChild(e1)
    p[0] = e

# match: port map ( {[ID =>] expr ,} ) - 20080724 - xsd
def p_port_map(p):
    "port_map : PORT MAP '(' id_map_list ')'"
    p[4].tagName = 'portMap'
    p[0] = p[4]

# match: [generic map ( {[ID =>] expr,} )] - 20080728 - xsd
def p_generic_map_key_opt1(p):
    """generic_map_key_opt : GENERIC MAP '(' id_map_key_opt_list ')'"""
    p[4].tagName = 'genericMap'
    p[0] = p[4]

#- 20080820 - xsd
def p_generic_map_key_opt2(p):
    """generic_map_key_opt : empty"""

# match: {[ID =>] expr,} - 20080728 - xsd 
def p_id_map_key_opt_list1(p):
    """id_map_key_opt_list : id_map_key_opt"""
    e = xml_document.createElement('universalMap')
    e.appendChild(p[1])
    p[0] = e

#- 20080728 - xsd
def p_id_map_key_opt_list2(p):
    """id_map_key_opt_list : id_map_key_opt_list ',' id_map_key_opt"""
    p[1].appendChild(p[3])
    p[0] = p[1]

#match: [ID =>] expr - 20080904 - xsd
def p_id_map_key_opt1(p):
    """id_map_key_opt : expr"""
    p[0] = p[1]

#- 20080919 - xsd
def p_id_map_key_opt2(p):
    """id_map_key_opt : id_object CONNECT expr"""
    e = xml_document.createElement('map')
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#- 20080919 - xsd
def p_id_map_key_opt3(p):
    """id_map_key_opt : id_object CONNECT OPEN"""
    e = xml_document.createElement('map')
    e.appendChild(p[1])
    e1 = xml_document.createElement(p[3])
    e.appendChild(e1)
    p[0] = e

# match: port map ( {[ID =>] expr ,} ) - 20080728 - xsd
def p_port_map_key_opt(p):
    "port_map_key_opt : PORT MAP '(' id_map_key_opt_list ')'"
    p[4].tagName = 'portMap'
    p[0] = p[4]

# match: TYPEID - 20081015 - xsd
def p_typeid(p):
    "typeid : id_item"
    p[1].tagName = 'type'
    p[0] = p[1]

# match: [is] - 20080725 - xsd
def p_is_opt(p):
    """is_opt : IS
              | empty"""

# match: [ID] - 20080725 - xsd
def p_id_opt(p):
    """id_opt : ID
              | empty"""

# match: {expr [after time],} - 20080730 - xsd
def p_expr_list1(p):
    "expr_list : expr_list_item"
    e = xml_document.createElement('expressions')
    e.appendChild(p[1])
    p[0] = e

#- 20080730 - xsd
def p_expr_list2(p):
    "expr_list : expr_list ',' expr_list_item"
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20080904 - xsd
def p_expr_list_item(p):
    "expr_list_item : expr expr_list_after_opt"
    if p[2] == None:
        p[0] = p[1]
    else:
        e = xml_document.createElement('afterExpression')
        e.appendChild(p[1])
        e.appendChild(p[2][0])
        location(p, e, p[2][1])
        p[0] = e

# match: [after time] - 20080904 - xsd
def p_expr_list_after_opt1(p):
    """expr_list_after_opt : AFTER expr"""
    p[0] = (p[2], location(p, None))

#- 20080730 - xsd
def p_expr_list_after_opt2(p):
    """expr_list_after_opt : empty"""

# match: LITERAL ID (where ID must be one of hr|min|sec|ms|us|ns|ps|fs) - 20080811 - xsd
def p_time1(p):
    "time : LITERAL ID"
    e = xml_document.createElement('timeExpression')
    e.setAttribute('value', p[1])
    e.setAttribute('id', p[2])
    location(p, e)
    p[0] = e

# match: {choice |} - 20080711 - xsd
def p_choice_list1(p):
    """choice_list : choice"""
    e = xml_document.createElement('choices')
    e.appendChild(p[1])
    p[0] = e                   

# match: {choice |} - 20080711 - xsd
def p_choice_list2(p):
    """choice_list : choice_list '|' choice"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# match: choice - 20080711 - xsd
def p_choice1(p):
    """choice : range
              | sexpr"""
    p[0] = p[1]

# match: choice - 20080711 - xsd
def p_choice2(p):
    """choice : OTHERS"""
    e = xml_document.createElement('others')
    p[0] = e                   

###############################################################################
# 1. Library Units
###############################################################################

#-------- library - use_clause - 20080904 - xsd
def p_library1(p):
    """library : use_clause"""
    p[0] = p[1]

#-------- library - entity - 20080708 - xsd
def p_library2(p):
    """library : entity ';'"""
    p[0] = p[1]

#-------- library - architecture - 20080708 - xsd
def p_library3(p):
    """library : architecture ';'"""
    if p[1] != None:
        p[0] = p[1]

#-------- library - package - 20080708 - xsd
def p_library4(p):
    """library : package ';'"""
    if p[1] != None:
        p[0] = p[1]

#-------- library - package_body - 20080708 - xsd
def p_library5(p):
    """library : package_body ';'"""
    if p[1] != None:
        p[0] = p[1]

#-------- library - configuration - 20080708 - xsd
def p_library6(p):
    """library : configuration ';'"""
    if p[1] != None:
        p[0] = p[1]

#-------- use clause - library - 20080904 - xsd
def p_use_clause1(p):
    """use_clause : LIBRARY ID ';'"""
    e = xml_document.createElement('useClause')
    e.setAttribute('library', p[2])
    location(p, e)
    p[0] = e

#-------- use clause - library + use_list - 20080904 - xsd
def p_use_clause2(p):
    """use_clause : LIBRARY ID ';' use_list"""
    p[4].setAttribute('library', p[2])
    location(p, p[4])    
    p[0] = p[4]

#-------- use clause - useList - 20080904 - xsd
def p_use_list1(p):
    """use_list : use"""
    e = xml_document.createElement('useClause')
    e.appendChild(p[1])
    p[0] = e

#-------- use clause - useList - 20080708 - xsd
def p_use_list2(p):
    """use_list : use_list use"""
    p[1].appendChild(p[2])
    p[0] = p[1]

#-------- use clause - use 1dot - 20080708 - xsd
def p_use1(p):
    """use : USE ID DOT ID ';'"""
    e = xml_document.createElement('use')
    e.setAttribute('id', p[2]+p[3]+p[4])
    location(p, e)
    p[0] = e

#-------- use clause - use 1dot all - 20081029 - xsd
def p_use1a(p):
    """use : USE ID DOT ALL ';'"""
    e = xml_document.createElement('use')
    e.setAttribute('id', p[2]+p[3]+p[4])
    location(p, e)
    p[0] = e

#-------- use clause - use 2dot - 20080708 - xsd
def p_use2(p):
    """use : USE ID DOT ID DOT ID ';'"""
    e = xml_document.createElement('use')
    e.setAttribute('id', p[2]+p[3]+p[4]+p[5]+p[6])
    location(p, e)
    p[0] = e

#-------- use clause - use 2dot all - 20080708 - xsd
def p_use2a(p):
    """use : USE ID DOT ID DOT ALL ';'"""
    e = xml_document.createElement('use')
    e.setAttribute('id', p[2]+p[3]+p[4]+p[5]+p[6])
    location(p, e)
    p[0] = e

#-------- entity unit - 20080809 - xsd
def p_entity(p):
    """entity : entity_header generic_opt entity1 port_opt declaration_list entity_body_opt entity_tail"""
    e = xml_document.createElement('entity')
    location(p, e, p[1][0])
    e.setAttribute('id', p[1][1])
    if p[2] != None:
        e.appendChild(p[2])
    if p[4] != None:
        e.appendChild(p[4])
    if p[5].hasChildNodes():
        e.appendChild(p[5])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

#-------- entity_header - 20080708 - xsd
def p_entity_header(p):
    """entity_header : ENTITY ID IS"""
    p[0] = (p.lineno(1), p[2])

#-------- entity - eps - 20080708 - xsd
def p_entity1(p):
    """entity1 :"""

#-------- entity_body_opt - 20080809 - xsd
def p_entity_body_opt1(p):
    """entity_body_opt : BEGIN parallel_stmt_list END"""
    p[0] = p[2]

#-------- entity_body_opt - 20080809 - xsd
def p_entity_body_opt2(p):
    """entity_body_opt : END"""

#-------- entity_tail - 20080809 - xsd
def p_entity_tail(p):
    """entity_tail : ID
                   | ENTITY ID
                   | ENTITY
                   | empty"""

#-------- architecture unit - 20080924 - xsd
def p_architecture(p):
    """architecture : architecture_header declaration_list architecture1 BEGIN parallel_stmt_list_opt architecture_tail"""
    e = xml_document.createElement('architecture')
    location(p, e, p[1][0])
    e.setAttribute('id', p[1][1])
    e.setAttribute('entity', p[1][2])
    if p[2].hasChildNodes():
        e.appendChild(p[2])
    if p[5] != None:
        e.appendChild(p[5])
    p[0] = e

# - 20080924 - xsd
def p_architecture_header(p):
    """architecture_header : ARCHITECTURE ID OF ID IS"""
    p[0] = (p.lineno(1), p[2], p[4])

# - 20080924 - xsd
def p_architecture1(p):
    """architecture1 :"""

# - 20080924 - xsd
def p_architecture_tail(p):
    """architecture_tail : END ARCHITECTURE ID
                         | END ARCHITECTURE
                         | END ID
                         | END"""

#-------- package unit - 20080930 - xsd
def p_package(p):
    """package : package_header declaration_list package_tail"""
    e = xml_document.createElement('package')
    location(p, e, p[1][0])
    e.setAttribute('id', p[1][1])
    if p[2].hasChildNodes():
        e.appendChild(p[2])
    p[0] = e

# - 20080930 - xsd
def p_package_header(p):
    """package_header : PACKAGE ID IS"""
    p[0] = (p.lineno(1), p[2])

# - 20080930 - xsd
def p_package_tail(p):
    """package_tail : END PACKAGE ID
                    | END ID"""

#-------- package body unit - 20080930 - xsd
def p_package_body(p):
    """package_body : package_body_header declaration_list package_body_tail"""
    e = xml_document.createElement('packageBody')
    location(p, e, p[1][0])
    e.setAttribute('id', p[1][1])
    if p[2].hasChildNodes():
        e.appendChild(p[2])
    p[0] = e

# - 20080930 - xsd
def p_package_body_header(p):
    """package_body_header : PACKAGE BODY ID IS"""
    p[0] = (p.lineno(1), p[3])

# - 20080930 - xsd
def p_package_body_tail(p):
    """package_body_tail : END PACKAGE BODY ID
                         | END ID"""

#-------- configuration - 20080930 - xsd
def p_configuration(p):
    """configuration : configuration_header FOR ID config_list configuration_tail"""
    e = xml_document.createElement('configuration')
    location(p, e, p[1][0])
    e.setAttribute('id', p[1][1])
    e.setAttribute('entity', p[1][2])
    p[4].tagName = 'forArchitecture'
    p[4].setAttribute('id', p[3])
    location(p, p[4], p[1][0])
    e.appendChild(p[4])
    p[0] = e

# - 20080930 - xsd
def p_configuration_header(p):
    """configuration_header : CONFIGURATION ID OF ID IS"""
    p[0] = (p.lineno(1), p[2], p[4])

# - 20080930 - xsd
def p_configuration_tail(p):
    """configuration_tail : END FOR ';' CONFIGURATION ID
                          | END FOR ';' ID"""

#---- config list
# match: [{block_config|comp_config}] - 20080930 - xsd
def p_config_list1(p):
    """config_list : config_list block_config 
                   | config_list comp_config"""
    p[1].appendChild(p[2])
    p[0] = p[1]

# - 20080930 - xsd
def p_config_list2(p):
    """config_list : empty"""
    e = xml_document.createElement('configList')
    p[0] = e

#---- block config - 20080930 - xsd
def p_block_config(p):
    "block_config : FOR ID config_list END FOR ';'"
    e = p[3]
    e.tagName = 'blockConfiguration'
    e.setAttribute('label', p[2])
    location(p, e)
    p[0] = e

#---- comp config - 20080930 - xsd
def p_comp_config(p):
    """comp_config : FOR ALL ':' ID comp_entity END FOR ';'
                   | FOR ALL ':' ID comp_configuration END FOR ';'
                   | FOR ID ':' ID comp_entity END FOR ';'
                   | FOR ID ':' ID comp_configuration END FOR ';'"""
    e = xml_document.createElement('componentConfiguration')
    location(p, e)
    e.setAttribute('which', p[2])
    e.setAttribute('id', p[4])
    e.appendChild(p[5])
    p[0] = e

# - 20080930 - xsd
def p_comp_entity1(p):
    """comp_entity : USE ENTITY ID DOT ID '(' ID ')' map_opt ';' comp_entity_for_opt END FOR ';'"""
    e = xml_document.createElement('useEntity')
    e.setAttribute('id', p[3]+p[4]+p[5])
    e.setAttribute('architecture', p[3])
    location(p, e)
    if p[9][0] != None:
        e.appendChild(p[9][0])
    if p[9][1] != None:
        e.appendChild(p[9][1])
    if p[11] != None:
        e.appendChild(p[11])
    p[0] = e

# - 20080930 - xsd
def p_comp_entity2(p):
    """comp_entity : USE ENTITY ID DOT ID map_opt ';' comp_entity_for_opt END FOR ';'"""
    e = xml_document.createElement('useEntity')
    e.setAttribute('id', p[3]+p[4]+p[5])
    location(p, e)
    if p[6][0] != None:
        e.appendChild(p[6][0])
    if p[6][1] != None:
        e.appendChild(p[6][1])
    if p[8] != None:
        e.appendChild(p[8])
    p[0] = e

# - 20080930 - xsd
def p_comp_entity3(p):
    """comp_entity : USE ENTITY ID '(' ID ')' map_opt ';' comp_entity_for_opt END FOR ';'"""
    e = xml_document.createElement('useEntity')
    e.setAttribute('id', p[3])
    e.setAttribute('architecture', p[5])
    location(p, e)
    if p[7][0] != None:
        e.appendChild(p[7][0])
    if p[7][1] != None:
        e.appendChild(p[7][1])
    if p[9] != None:
        e.appendChild(p[9])
    p[0] = e

# - 20080930 - xsd
def p_comp_entity4(p):
    """comp_entity : USE ENTITY ID map_opt ';' comp_entity_for_opt END FOR ';'"""
    e = xml_document.createElement('useEntity')
    e.setAttribute('id', p[3])
    location(p, e)
    if p[4][0] != None:
        e.appendChild(p[4][0])
    if p[4][1] != None:
        e.appendChild(p[4][1])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

# - 20080930 - xsd
def p_comp_entity_for_opt1(p):
    """comp_entity_for_opt : FOR ID config_list END FOR ';'"""
    e = p[3]
    e.tagName = 'forArchitecture'
    e.setAttribute('id', p[2])
    location(p, e)
    p[0] = e

# - 20080930 - xsd
def p_comp_entity_for_opt2(p):
    """comp_entity_for_opt : empty"""

# - 20080930 - xsd
def p_comp_configuration1(p):
    """comp_configuration : USE CONFIGURATION ID DOT ID map_opt ';'"""
    e = xml_document.createElement('useConfiguration')
    e.setAttribute('id', p[3]+p[4]+p[5])
    location(p, e)
    if p[6][0] != None:
        e.appendChild(p[6][0])
    if p[6][1] != None:
        e.appendChild(p[6][1])
    p[0] = e

# - 20080930 - xsd
def p_comp_configuration2(p):
    """comp_configuration : USE CONFIGURATION ID map_opt ';'"""
    e = xml_document.createElement('useConfiguration')
    e.setAttribute('id', p[3])
    location(p, e)
    if p[4][0] != None:
        e.appendChild(p[4][0])
    if p[4][1] != None:
        e.appendChild(p[4][1])
    p[0] = e


###############################################################################
# 2. Declaration
###############################################################################

#-------- declaration list - 20080811 - xsd
# match: [{declaration}]
# correction LeftRec
def p_declaration_list1(p):
    "declaration_list : declaration_list declaration ';'"
    p[1].appendChild(p[2])
    p[0] = p[1]

# - 20080811 - xsd
def p_declaration_list2(p):
    "declaration_list : empty"
    e = xml_document.createElement('declarations')
    p[0] = e

# - 20080811 - xsd
def p_declaration(p):
    """declaration : decl_type
                   | decl_constant
                   | decl_variable
                   | decl_signal
                   | decl_file
                   | decl_alias
                   | decl_attrib
                   | decl_component
                   | decl_function
                   | decl_procedure
                   | decl_for"""
    p[0] = p[1]

#-------- Type Declarations - 20080811 - xsd
def p_decl_type1(p):
    """decl_type : TYPE ID IS decl_type_def"""
    e = xml_document.createElement('typeDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    e.appendChild(p[4])
    p[0] = e

# - 20080811 - xsd
def p_decl_type2(p):
    """decl_type : SUBTYPE ID IS decl_type_subdef"""
    e = xml_document.createElement('subtypeDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    e.appendChild(p[4][0])
    e.appendChild(p[4][1])
    p[0] = e

#---- decl_type TYPE definition - 20080811 - xsd
def p_decl_type_def1(p):
    """decl_type_def : '(' id_list ')'"""
    p[0] = p[2]
    
# - 20080811 - xsd
def p_decl_type_def2(p):
    """decl_type_def : RANGE LITERAL range_dir LITERAL"""
    e = xml_document.createElement('range')
    e.setAttribute('direction', p[3])
    e1 = xml_document.createElement('constantExpression')
    e2 = xml_document.createElement('constantExpression')
    e1.setAttribute('id', p[2])
    e2.setAttribute('id', p[4])
    e.appendChild(e1)
    e.appendChild(e2)
    p[0] = e

# - 20080811 - xsd
def p_decl_type_def3(p):
    """decl_type_def : ARRAY '(' decl_type_range_list ')' OF expr"""
    e = xml_document.createElement('array')
    e.appendChild(p[3])
    e.appendChild(p[6])
    p[0] = e

# - 20080811 - xsd
def p_decl_type_def4(p):
    """decl_type_def : RECORD decl_type_record_item_list END RECORD"""
    p[0] = p[2]

# - 20080811 - xsd
def p_decl_type_def5(p):
    """decl_type_def : ACCESS typeid"""
    e = xml_document.createElement('access')
    e.appendChild(p[2])
    p[0] = e

# - 20080811 - xsd
def p_decl_type_def6(p):
    """decl_type_def : FILE OF typeid"""
    e = xml_document.createElement('fileOf')
    e.appendChild(p[3])
    p[0] = e

# - 20080811 - xsd
def p_id_list1(p):
    "id_list : id_list_item"
    e = xml_document.createElement('ids')
    e.appendChild(p[1])
    p[0] = e

# - 20080811 - xsd
def p_id_list2(p):
    "id_list : id_list ',' id_list_item"
    p[1].appendChild(p[3])
    p[0] = p[1]
    
# - 20081028 - xsd
def p_id_list_item(p):
    "id_list_item : ID"
    e = xml_document.createElement('id')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = e

# - 20080811 - xsd
def p_decl_type_range_list1(p):
    """decl_type_range_list : range"""
    e = xml_document.createElement('rangesTypes')
    e.appendChild(p[1])
    p[0] = e

# - 20080811 - xsd
def p_decl_type_range_list2(p):
    """decl_type_range_list : typeid"""
    e = xml_document.createElement('rangesTypes')
    e.appendChild(p[1])
    p[0] = e

# - 20080811 - xsd
def p_decl_type_range_list3(p):
    """decl_type_range_list : decl_type_range_list ',' range"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20080811 - xsd
def p_decl_type_range_list4(p):
    """decl_type_range_list : decl_type_range_list ',' typeid"""
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20080811 - xsd
def p_decl_type_record_item_list1(p):
    """decl_type_record_item_list : decl_type_record_item_list_item ';'"""
    e = xml_document.createElement('records')
    e.appendChild(p[1])
    p[0] = e

# - 20080811 - xsd
def p_decl_type_record_item_list2(p):
    """decl_type_record_item_list : decl_type_record_item_list decl_type_record_item_list_item ';'"""
    p[1].appendChild(p[2])
    p[0] = p[1]

# - 20081028 - xsd
def p_decl_type_record_item_list_item(p):
    """decl_type_record_item_list_item : id_list ':' typeid"""
    e = xml_document.createElement('record')
    location(p, e, p[1].firstChild.getAttribute('line'))
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#---- decl_type SUBTYPE definition - 20080811 - xsd
def p_decl_type_subdef1(p):
    """decl_type_subdef : ID RANGE range ';'"""
    e = xml_document.createElement('id')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = (e, p[3])

# - 20080811 - xsd
def p_decl_type_subdef2(p):
    """decl_type_subdef : ID typeid ';'"""
    e = xml_document.createElement('id')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = (e, p[2])

# - 20080811 - xsd
def p_decl_type_subdef3(p):
    """decl_type_subdef : ID '(' range_list ')'"""
    e = xml_document.createElement('id')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = (e, p[3])

#-------- Other Declarations
#---- constant declaration - 20081028 - xsd
def p_decl_constant(p):
    "decl_constant : CONSTANT id_list ':' typeid ASSIGN expr"
    e = xml_document.createElement('constantDeclaration')
    location(p, e)
    e.appendChild(p[2])
    e.appendChild(p[4])
    e1 = xml_document.createElement('value')
    e1.appendChild(p[6])
    e.appendChild(e1)
    p[0] = e

#---- shared variable declaration - 20081028 - xsd
def p_decl_variable1(p):
    """decl_variable : SHARED VARIABLE id_list ':' typeid assign_expr_opt"""
    e = xml_document.createElement('variableDeclaration')
    location(p, e)
    e.appendChild(p[3])
    e.setAttribute('shared', 'true')
    e.appendChild(p[5])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

#---- variable declaration - 20081028 - xsd
def p_decl_variable2(p):
    """decl_variable : VARIABLE id_list ':' typeid assign_expr_opt"""
    e = xml_document.createElement('variableDeclaration')
    location(p, e)
    e.appendChild(p[2])
    e.setAttribute('shared', 'false')
    e.appendChild(p[4])
    if p[5] != None: 
        e.appendChild(p[5])
    p[0] = e

#---- signal declaration - 20081028 - xsd
def p_decl_signal(p):
    """decl_signal : SIGNAL id_list ':' typeid assign_expr_opt"""
    e = xml_document.createElement('signalDeclaration')
    location(p, e)
    e.appendChild(p[2])
    e.appendChild(p[4])
    if p[5] != None: 
        e.appendChild(p[5])
    p[0] = e

#---- file declaration - 20081029 - xsd
def p_decl_file0(p):
    """decl_file : FILE id_list ':' typeid"""
    e = xml_document.createElement('fileDeclaration')
    location(p, e)
    e.appendChild(p[2])
    e.appendChild(p[4])
    p[0] = e

# - 20081028 - xsd
def p_decl_file1(p):
    """decl_file : FILE id_list ':' typeid IS inout CLITERAL"""
    e = xml_document.createElement('fileDeclaration')
    location(p, e)
    e.appendChild(p[2])
    e.appendChild(p[4])
    e.setAttribute('io', p[6])
    e.setAttribute('name', p[7])
    p[0] = e

# - 20081028 - xsd
def p_decl_file2(p):
    """decl_file : FILE id_list ':' typeid IS OPEN file_open_mode IS CLITERAL"""
    e = xml_document.createElement('fileDeclaration')
    location(p, e)
    e.appendChild(p[2])
    e.appendChild(p[4])
    e.setAttribute('mode', p[7])
    e.setAttribute('name', p[9])
    p[0] = e

# - 20080815 - xsd
def p_inout(p):
    """inout : IN
             | OUT"""
    p[0] = p[1]

# - 20080815 - xsd
def p_file_open_mode(p):
    """file_open_mode : READ_MODE
                      | WRITE_MODE
                      | APPEND_MODE"""
    p[0] = p[1]

#---- alias declaration - 20081029 - xsd
def p_decl_alias(p):
    "decl_alias : ALIAS ID ':' typeid IS id_item"
    e = xml_document.createElement('aliasDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    e.appendChild(p[4])
    e.appendChild(p[6])
    p[0] = e

#---- attribute declaration - 20081029 - xsd
def p_decl_attrib1(p):
    """decl_attrib : ATTRIBUTE ID ':' typeid"""
    e = xml_document.createElement('attributeDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    e.appendChild(p[4])
    p[0] = e

# - 20081029 - xsd
def p_decl_attrib2(p):
    """decl_attrib : ATTRIBUTE ID OF decl_attrib_which ':' decl_class IS expr"""
    e = xml_document.createElement('attributeDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    e.setAttribute('of', p[4])
    e.setAttribute('class', p[6])
    e.appendChild(p[8])
    p[0] = e

# - 20080815 - xsd
def p_decl_attrib_which(p):
    """decl_attrib_which : ID
                         | OTHERS
                         | ALL"""
    p[0] = p[1]

# - 20080815 - xsd
def p_decl_class(p):
    """decl_class : ENTITY
                  | ARCHITECTURE
                  | CONFIGURATION
                  | PROCEDURE
                  | FUNCTION
                  | PACKAGE
                  | TYPE
                  | SUBTYPE
                  | CONSTANT
                  | SIGNAL
                  | VARIABLE
                  | COMPONENT
                  | LABEL"""
    p[0] = p[1]

#---- component declaration - 20080815 - xsd
def p_decl_component1(p):
    """decl_component : COMPONENT ID generic_opt port_opt END COMPONENT
                      | COMPONENT ID generic_opt port_opt END COMPONENT ID"""
    e = xml_document.createElement('componentDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    if p[3] != None:
        e.appendChild(p[3])
    if p[4] != None:    
        e.appendChild(p[4])
    p[0] = e

# - 20080815 - xsd
def p_decl_component3(p):
    """decl_component : COMPONENT ID IS generic_opt port_opt END COMPONENT
                      | COMPONENT ID IS generic_opt port_opt END COMPONENT ID"""
    e = xml_document.createElement('componentDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    if p[4] != None:
        e.appendChild(p[4])
    if p[5] != None:
        e.appendChild(p[5])
    p[0] = e

#---- function declaration - 20081029 - xsd
def p_decl_function1a(p):
    """decl_function : FUNCTION ID function_decl_opt RETURN typeid function_body_opt"""
    e = xml_document.createElement('functionDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    e.setAttribute('pure', 'true')
    if p[3] != None: 
        e.appendChild(p[3])
    e.appendChild(p[5])
    if p[6] != None: 
        if p[6][0].hasChildNodes(): 
            e.appendChild(p[6][0])
        if p[6][1] != None: 
            e.appendChild(p[6][1])
    p[0] = e

# - 20081029 - xsd
def p_decl_function1b(p):
    """decl_function : PURE FUNCTION ID function_decl_opt RETURN typeid function_body_opt"""
    e = xml_document.createElement('functionDeclaration')
    location(p, e)
    e.setAttribute('id', p[3])
    e.setAttribute('pure', 'true')
    if p[4] != None: 
        e.appendChild(p[4])
    e.appendChild(p[6])
    if p[7] != None:
        if p[7][0].hasChildNodes(): 
            e.appendChild(p[7][0])
        if p[7][1] != None: 
            e.appendChild(p[7][1])
    p[0] = e

# - 20081029 - xsd
def p_decl_function2(p):
    """decl_function : IMPURE FUNCTION ID function_decl_opt RETURN typeid function_body_opt"""
    e = xml_document.createElement('functionDeclaration')
    location(p, e)
    e.setAttribute('id', p[3])
    e.setAttribute('pure', 'false')
    if p[4] != None: 
        e.appendChild(p[4])
    e.appendChild(p[6])
    if p[7] != None:
        if p[7][0].hasChildNodes(): 
            e.appendChild(p[7][0])
        if p[7][1] != None: 
            e.appendChild(p[7][1])
    p[0] = e

# - 20080816 - xsd
def p_function_decl_opt1(p):
    """function_decl_opt : '(' parameter_expr_list ')'"""
    p[0] = p[2]

# - 20080816 - xsd
def p_function_decl_opt2(p):
    """function_decl_opt : empty"""

# - 20080816 - xsd
def p_procedure_decl_opt(p):
    """procedure_decl_opt : function_decl_opt"""
    if p[1] != None:
        p[1].tagName = 'procedureParameters'
        p[0] = p[1]
    else:
        p[0] = None

# - 20081029 - xsd
def p_function_body_opt1(p):
    """function_body_opt : IS declaration_list BEGIN sequential_stmt_list END FUNCTION ID
                         | IS declaration_list BEGIN sequential_stmt_list END ID"""
    p[0] = (p[2], p[4])

# - 20080829 - xsd
def p_function_body_opt2(p):
    """function_body_opt : empty"""

#---- procedure declaration - 20081029 - xsd
def p_decl_procedure(p):
    "decl_procedure : PROCEDURE ID procedure_decl_opt procedure_body_opt"
    e = xml_document.createElement('procedureDeclaration')
    location(p, e)
    e.setAttribute('id', p[2])
    if p[3] != None: 
        e.appendChild(p[3])
    if p[4] != None:
        if p[4][0].hasChildNodes(): 
            e.appendChild(p[4][0])
        if p[4][1] != None: 
            e.appendChild(p[4][1])
    p[0] = e

# - 20081029 - xsd
def p_procedure_body_opt1(p):
    """procedure_body_opt : IS declaration_list BEGIN sequential_stmt_list_opt END PROCEDURE ID
                          | IS declaration_list BEGIN sequential_stmt_list_opt END ID"""
    p[0] = (p[2], p[4])

# - 20080816 - xsd
def p_procedure_body_opt2(p):
    """procedure_body_opt : empty"""

#---- for declaration - 20080816 - xsd
def p_decl_for(p):
    "decl_for : FOR decl_for_which ':' ID USE decl_for_ent_conf map_opt ';'"
    e = xml_document.createElement('forDeclaration')
    location(p, e)
    e.setAttribute('which', p[2])
    e.setAttribute('id', p[4])
    e.setAttribute(p[6][0][0], p[6][0][1])
    if p[6][1] != None:
        e.setAttribute(p[6][1][0], p[6][1][1])
    if p[7][0] != None:
        e.appendChild(p[7][0])
    if p[7][1] != None:
        e.appendChild(p[7][1])
    p[0] = e

# - 20080816 - xsd
def p_decl_for_which(p):
    """decl_for_which : ID
                      | OTHERS
                      | ALL"""
    p[0] = p[1]

# - 20080816 - xsd
def p_decl_for_ent_conf1aa(p):
    """decl_for_ent_conf : ENTITY ID DOT ID '(' ID ')'"""
    p[0] = (('entity', p[2]+p[3]+p[4]), ('architecture', p[6]))

# - 20080816 - xsd
def p_decl_for_ent_conf1ab(p):
    """decl_for_ent_conf : ENTITY ID '(' ID ')'"""
    p[0] = (('entity', p[2]), ('architecture', p[4]))

# - 20080816 - xsd
def p_decl_for_ent_conf1ba(p):
    """decl_for_ent_conf : ENTITY ID DOT ID"""
    p[0] = (('entity', p[2]+p[3]+p[4]))

# - 20080816 - xsd
def p_decl_for_ent_conf1bb(p):
    """decl_for_ent_conf : ENTITY ID"""
    p[0] = (('entity', p[2]))

# - 20080816 - xsd
def p_decl_for_ent_conf2a(p):
    """decl_for_ent_conf : CONFIGURATION ID DOT ID"""
    p[0] = (('configuration', p[2]+p[3]+p[4]))

# - 20080816 - xsd
def p_decl_for_ent_conf2b(p):
    """decl_for_ent_conf : CONFIGURATION ID"""
    p[0] = (('configuration', p[2]))

###############################################################################
# 3. Expression
###############################################################################

#-------- expression - 20080730 - xsd
def p_expr1(p):
    """expr : relexpr"""
    p[0] = p[1]

#-------- expression - 20080730 - xsd
def p_expr(p):
    """expr : expr AND relexpr
            | expr NAND relexpr
            | expr OR relexpr
            | expr NOR relexpr
            | expr XOR relexpr
            | expr XNOR relexpr"""
    e = xml_document.createElement('logicalExpression')
    e.setAttribute('op', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e
    
#-------- relexpr - 20080730 - xsd
def p_relexpr1(p):
    """relexpr : shexpr"""
    p[0] = p[1]

#-------- relexpr - 20080730 - xsd
def p_relexpr(p):
    """relexpr : relexpr EQ shexpr
               | relexpr NEQ shexpr
               | relexpr LT shexpr
               | relexpr LE shexpr
               | relexpr GT shexpr
               | relexpr GE shexpr"""
    e = xml_document.createElement('relationalExpression')
    e.setAttribute('op', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#-------- shexpr - 20080730 - xsd
def p_shexpr1(p):
    """shexpr : sexpr"""
    p[0] = p[1]

#-------- shexpr - 20080730 - xsd
def p_shexpr(p):
    """shexpr : shexpr SLL sexpr
               | shexpr SRL sexpr
               | shexpr SLA sexpr
               | shexpr SRA sexpr
               | shexpr ROL sexpr
               | shexpr ROR sexpr"""
    e = xml_document.createElement('shiftExpression')
    e.setAttribute('op', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#-------- sexpr - 20080730 - xsd
def p_sexpr1(p):
    """sexpr : mulexpr"""
    p[0] = p[1]

#-------- sexpr - 20080730 - xsd
def p_sexpr(p):
    """sexpr : sexpr '+' mulexpr
             | sexpr '-' mulexpr
             | sexpr '&' mulexpr"""
    e = xml_document.createElement('addingExpression')
    e.setAttribute('op', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#-------- mulexpr - 20080730 - xsd
def p_mulexpr1(p):
    """mulexpr : expexpr"""
    p[0] = p[1]

#-------- mulexpr - 20080730 - xsd
def p_mulexpr(p):
    """mulexpr : mulexpr '*' expexpr
               | mulexpr '/' expexpr
               | mulexpr MOD expexpr
               | mulexpr REM expexpr"""
    e = xml_document.createElement('multiplyingExpression')
    e.setAttribute('op', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#-------- expexpr - 20080730 - xsd
def p_expexpr1(p):
    """expexpr : factor"""
    p[0] = p[1]

#-------- expexpr - 20080730 - xsd
def p_expexpr2(p):
    """expexpr : expexpr EXPSIGN factor"""
    e = xml_document.createElement('exponentialExpression')
    e.setAttribute('op', p[2])
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#-------- factor - 20080731 - xsd
def p_factor1(p):
    """factor : '+' prim
              | '-' prim"""
    e = xml_document.createElement('prefixExpression')
    e.setAttribute('op', p[1])
    e.appendChild(p[2])
    p[0] = e

#-------- factor - 20080711 - xsd
def p_factor2(p):
    "factor : prim"
    p[0] = p[1]

#-------- factor - 20080731 - xsd
def p_factor3(p):
    """factor : NOT prim
              | ABS prim"""
    e = xml_document.createElement('prefixExpression')
    e.setAttribute('op', p[1])
    e.appendChild(p[2])
    p[0] = e

#-------- prim - 20081015 - xsd
def p_prim0(p):
    "prim : CLITERAL"
    e = xml_document.createElement('constantExpression')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = e

# - 20080711 - xsd
def p_prim1(p):
    "prim : LITERAL"
    e = xml_document.createElement('constantExpression')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = e

# - 20080711 - xsd
def p_prim2(p):
    """prim : '(' choice_expr_list ')'"""
    p[0] = p[2]

# - 20080711 - xsd
def p_prim3(p):
    """prim : NEW ID"""
    e = xml_document.createElement('newExpression')
    e.setAttribute('id', p[2])
    location(p, e)
    p[0] = e

# - 20080711 - xsd
def p_prim4(p):
    """prim : NEW ID APOSTROPHE '(' expr ')'"""
    e = xml_document.createElement('newExpression')
    e.setAttribute('id', p[2])
    location(p, e)
    e1 = xml_document.createElement('attribute')
    e.appendChild(e1)
    e1.appendChild(p[5])
    p[0] = e

# - 20080711 - xsd
def p_prim5(p):
    """prim : time"""
    p[0] = p[1]

# - 20080711 - xsd
def p_prim6(p):
    """prim : expr_object"""
    p[0] = p[1]

#-------- expr_object - 20080711 - xsd
def p_expr_object1(p):
    "expr_object : name"
    p[0] = p[1]

#---- choice - expression - 20080711 - xsd
def p_choice_expr_list2(p):
    "choice_expr_list : expr"
    p[0] = p[1]

#---- choice to expression list - 20080811 - xsd
def p_choice_expr_list1(p):
    "choice_expr_list : choice_expr_list_item"
    e = xml_document.createElement('aggregateExpression')
    e.appendChild(p[1])
    p[0] = e

#---- choice to expression list - 20081029 - xsd
def p_choice_expr_list3(p):
    "choice_expr_list : choice_expr_list ',' choice_expr_list_item"
    if p[1].tagName == 'aggregateExpression':
        p[1].appendChild(p[3])
        p[0] = p[1]
    else:
        e = xml_document.createElement('aggregateExpression')
        e.appendChild(p[1])
        e.appendChild(p[3])
        p[0] = e

#---- choice to expression list - 20081029 - xsd
def p_choice_expr_list4(p):
    "choice_expr_list : choice_expr_list ',' expr"
    if p[1].tagName == 'aggregateExpression':
        p[1].appendChild(p[3])
        p[0] = p[1]
    else:
        e = xml_document.createElement('aggregateExpression')
        e.appendChild(p[1])
        e.appendChild(p[3])
        p[0] = e

#---- choice to expression list: item - 20080804 - xsd
def p_choice_expr_list_item(p):
    "choice_expr_list_item : choice_list CONNECT expr"
    e = xml_document.createElement('connect')
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#---- key parameter (or index) - 20080711 - xsd
def p_parid1(p):
    """parid : expr"""
    p[0] = p[1]

#---- key parameter (or index) - 20080821 - xsd
def p_parid2(p):
    """parid : ID CONNECT expr"""
    e = xml_document.createElement('connect')
    e1 = xml_document.createElement('id')
    e1.setAttribute('id', p[1])
    e.appendChild(e1)
    e.appendChild(p[3])
    p[0] = e

###############################################################################
# 4. Sequential Statements
###############################################################################

# match: [postponed] (VHDL93) - xsd
def p_postponed_opt1(p):
    """postponed_opt : POSTPONED"""
    p[0] = p[1]

def p_postponed_opt2(p):
    """postponed_opt : empty"""

#-------- sequential statement list

# returns: ([CondAssign*], {Signal:[Signal*]} (i.e., sensitivity list))
#-------- 20080725 - xsd
def p_sequential_stmt_list_opt1(p):
    """sequential_stmt_list_opt : sequential_stmt_list"""
    p[0] = p[1]

#-------- 20080725 - xsd
def p_sequential_stmt_list_opt2(p):
    """sequential_stmt_list_opt : empty"""
    e = xml_document.createElement('sequentialStatements')
    p[0] = e

#-------- 20080725 - xsd
def p_sequential_stmt_list1(p):
    "sequential_stmt_list : sequential_stmt ';'"
    e = xml_document.createElement('sequentialStatements')
    e.appendChild(p[1])
    p[0] = e

#-------- 20080725 - xsd
def p_sequential_stmt_list2(p):
    "sequential_stmt_list : sequential_stmt_list sequential_stmt ';'"
    p[1].appendChild(p[2])
    p[0] = p[1]

#-------- 20080725 - xsd
def p_sequential_stmt(p):
    """sequential_stmt : seq_stmt_wait
                       | seq_stmt_assert
                       | seq_stmt_report
                       | seq_stmt_assign
                       | seq_stmt_varassign
                       | seq_stmt_proc_call
                       | seq_stmt_if
                       | seq_stmt_case
                       | seq_stmt_while
                       | seq_stmt_for
                       | seq_stmt_next
                       | seq_stmt_exit
                       | seq_stmt_return
                       | seq_stmt_null"""
    p[0] = p[1]

#---- seq statement wait - 20080924 - xsd
def p_seq_stmt_wait1(p):
    """seq_stmt_wait : WAIT ON id_list UNTIL expr FOR expr"""
    e = xml_document.createElement('waitSequentialStatement')
    location(p, e)
    e1 = xml_document.createElement(p[2])
    e1.appendChild(p[3])
    e.appendChild(e1)
    e2 = xml_document.createElement(p[4])
    e2.appendChild(p[5])
    e.appendChild(e2)
    e3 = xml_document.createElement(p[6])
    e3.appendChild(p[7])
    e.appendChild(e3)
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_wait2(p):
    """seq_stmt_wait : WAIT ON id_list UNTIL expr
                     | WAIT ON id_list FOR expr
                     | WAIT UNTIL expr FOR expr"""
    e = xml_document.createElement('waitSequentialStatement')
    location(p, e)
    e1 = xml_document.createElement(p[2])
    e1.appendChild(p[3])
    e.appendChild(e1)
    e2 = xml_document.createElement(p[4])
    e2.appendChild(p[5])
    e.appendChild(e2)
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_wait3(p):
    """seq_stmt_wait : WAIT ON id_list
                     | WAIT UNTIL expr
                     | WAIT FOR expr"""
    e = xml_document.createElement('waitSequentialStatement')
    location(p, e)
    e1 = xml_document.createElement(p[2])
    e1.appendChild(p[3])
    e.appendChild(e1)
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_wait4(p):
    """seq_stmt_wait : WAIT"""
    e = xml_document.createElement('waitSequentialStatement')
    location(p, e)
    p[0] = e

#---- seq statement assert - 20080923 - xsd
def p_seq_stmt_assert1(p):
    """seq_stmt_assert : ASSERT expr REPORT CLITERAL severity"""
    e = xml_document.createElement('assertSequentialStatement')
    location(p, e)
    e.appendChild(p[2])
    e.setAttribute('report', p[4])
    e.setAttribute('severity', p[5])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_assert2(p):
    """seq_stmt_assert : ASSERT expr REPORT CLITERAL"""
    e = xml_document.createElement('assertSequentialStatement')
    location(p, e)
    e.appendChild(p[2])
    e.setAttribute('report', p[4])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_assert3(p):
    """seq_stmt_assert : ASSERT expr severity"""
    e = xml_document.createElement('assertSequentialStatement')
    location(p, e)
    e.appendChild(p[2])
    e.setAttribute('severity', p[3])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_assert4(p):
    """seq_stmt_assert : ASSERT expr"""
    e = xml_document.createElement('assertSequentialStatement')
    location(p, e)
    e.appendChild(p[2])
    p[0] = e

# - 20080923 - xsd
def p_severity(p):
    """severity : SEVERITY NOTE
                | SEVERITY WARNING
                | SEVERITY ERROR
                | SEVERITY FAILURE"""
    p[0] = p[2]

#---- seq statement report (VHDL93) - 20080923 - xsd
def p_seq_stmt_report(p):
    """seq_stmt_report : REPORT CLITERAL severity
                       | REPORT CLITERAL"""
    e = xml_document.createElement('reportSequentialStatement')
    location(p, e)
    e.setAttribute('report', p[2])
    if p[3] != None:
        e.setAttribute('severity', p[3])
    p[0] = e

#---- seq statement signal assign - 20081029 - xsd
def p_seq_stmt_assign1(p):
    "seq_stmt_assign : target LE delay_mechanism expr_list"
    e = xml_document.createElement('signalAssignSequentialStatement')
    location(p, e, getLineTarget(p[1]))
    e.appendChild(p[1])
    e.setAttribute('delay', p[3][0])
    if p[3][1] != None:
        e.appendChild(p[3][1])
    e1 = xml_document.createElement('signalValue')
    e1.appendChild(p[4])
    e.appendChild(e1)
    p[0] = e

# - 20081029 - xsd
def p_seq_stmt_assign2(p):
    """seq_stmt_assign : target LE expr_list"""
    e = xml_document.createElement('signalAssignSequentialStatement')
    location(p, e, getLineTarget(p[1]))
    e.appendChild(p[1])
    e1 = xml_document.createElement('signalValue')
    e1.appendChild(p[3])
    e.appendChild(e1)
    p[0] = e

#---- seq statement variable assign - 20081029 - xsd
def p_seq_stmt_varassign(p):
    "seq_stmt_varassign : target ASSIGN expr"
    e = xml_document.createElement('variableAssignSequentialStatement')
    location(p, e, getLineTarget(p[1]))
    e.appendChild(p[1])
    e.appendChild(p[3])
    p[0] = e

#---- seq statement proc call - 20081015 - xsd
def p_seq_stmt_proc_call1(p):
    "seq_stmt_proc_call : seq_stmt_proc_call_form"
    p[0] = p[1]

# - 20081015 - xsd
def p_seq_stmt_proc_call_form(p):
    "seq_stmt_proc_call_form : id_item"
    p[1].tagName = 'procedureSequentialStatement'
    p[0] = p[1]

#---- seq statement if - 20080924 - xsd
def p_seq_stmt_if1(p):
    """seq_stmt_if : ID ':' IF expr THEN sequential_stmt_list seq_stmt_elsif_list_opt seq_stmt_else_opt END IF ID
                   | ID ':' IF expr THEN sequential_stmt_list seq_stmt_elsif_list_opt seq_stmt_else_opt END IF"""
    e = p[7]
    location(p, e)
    e.setAttribute('label', p[1])
    e1 = xml_document.createElement('then')
    e1.appendChild(p[6])
    e.insertBefore(e1, e.firstChild)
    e.insertBefore(p[4], e.firstChild)
    if p[8] != None:
        e.appendChild(p[8])
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_if2(p):
    """seq_stmt_if : IF expr THEN sequential_stmt_list seq_stmt_elsif_list_opt seq_stmt_else_opt END IF ID
                   | IF expr THEN sequential_stmt_list seq_stmt_elsif_list_opt seq_stmt_else_opt END IF"""
    e = p[5]
    location(p, e)
    e1 = xml_document.createElement('then')
    e1.appendChild(p[4])
    e.insertBefore(e1, e.firstChild)
    e.insertBefore(p[2], e.firstChild)
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_elsif_list_opt1(p):
    """seq_stmt_elsif_list_opt : seq_stmt_elsif_list"""
    p[0] = p[1]

# - 20080924 - xsd
def p_seq_stmt_elsif_list_opt2(p):
    """seq_stmt_elsif_list_opt : empty"""
    e = xml_document.createElement('ifSequentialStatement')
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_elsif_list1(p):
    "seq_stmt_elsif_list : seq_stmt_elsif"
    e = xml_document.createElement('ifSequentialStatement')
    e.appendChild(p[1])
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_elsif_list2(p):
    "seq_stmt_elsif_list : seq_stmt_elsif_list seq_stmt_elsif"
    p[1].appendChild(p[2])
    p[0] = p[1]

# - 20080924 - xsd
def p_seq_stmt_elsif(p):
    "seq_stmt_elsif : ELSIF expr THEN sequential_stmt_list"
    e = xml_document.createElement('elseif')
    e.appendChild(p[2])
    e1 = xml_document.createElement('then')
    e1.appendChild(p[4])
    e.appendChild(e1)
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_else_opt1(p):
    """seq_stmt_else_opt : ELSE sequential_stmt_list"""
    e = xml_document.createElement('else')
    e.appendChild(p[2])
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_else_opt2(p):
    """seq_stmt_else_opt : empty"""

#---- seq statement case - 20080924 - xsd
def p_seq_stmt_case1(p):
    """seq_stmt_case : ID ':' CASE expr IS seq_stmt_case_when_list END CASE ID
                     | ID ':' CASE expr IS seq_stmt_case_when_list END CASE"""
    e = p[6]
    location(p, e)
    e.setAttribute('label', p[1])
    e.insertBefore(p[4], e.firstChild)
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_case2(p):
    """seq_stmt_case : CASE expr IS seq_stmt_case_when_list END CASE"""
    e = p[4]
    location(p, e)
    e.insertBefore(p[2], e.firstChild)
    p[0] = e    

# - 20080924 - xsd
def p_seq_stmt_case_when_list1(p):
    """seq_stmt_case_when_list : seq_stmt_case_when_list_item"""
    e = xml_document.createElement('caseSequentialStatement')
    e.appendChild(p[1])
    p[0] = e

# - 20080924 - xsd
def p_seq_stmt_case_when_list2(p):
    """seq_stmt_case_when_list : seq_stmt_case_when_list seq_stmt_case_when_list_item"""
    p[1].appendChild(p[2])
    p[0] = p[1]

# - 20080924 - xsd
def p_seq_stmt_case_when_list_item(p):
    """seq_stmt_case_when_list_item : WHEN choice_list CONNECT sequential_stmt_list"""
    e = xml_document.createElement('case')
    e.appendChild(p[2])
    e.appendChild(p[4])
    p[0] = e

#---- seq statement while - 20080923 - xsd
def p_seq_stmt_while1(p):
    """seq_stmt_while : ID ':' WHILE expr LOOP sequential_stmt_list END LOOP ID"""
    e = xml_document.createElement('whileSequentialStatement')
    e.setAttribute('label', p[1])
    location(p, e)
    e.appendChild(p[4])
    e.appendChild(p[6])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_while2(p):
    """seq_stmt_while : ID ':' LOOP sequential_stmt_list END LOOP ID"""
    e = xml_document.createElement('whileSequentialStatement')
    e.setAttribute('label', p[1])
    location(p, e)
    e.appendChild(p[4])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_while3(p):
    """seq_stmt_while : WHILE expr LOOP sequential_stmt_list END LOOP"""
    e = xml_document.createElement('whileSequentialStatement')
    location(p, e)
    e.appendChild(p[2])
    e.appendChild(p[4])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_while4(p):
    """seq_stmt_while : LOOP sequential_stmt_list END LOOP"""
    e = xml_document.createElement('whileSequentialStatement')
    location(p, e)
    e.appendChild(p[2])
    p[0] = e

#---- seq statement for - 20080923 - xsd
def p_seq_stmt_for1(p):
    """seq_stmt_for : ID ':' FOR ID IN range LOOP sequential_stmt_list END LOOP ID
                    | ID ':' FOR ID IN range LOOP sequential_stmt_list END LOOP"""
    e = xml_document.createElement('forSequentialStatement')
    location(p, e)
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4])
    e.appendChild(p[6])
    e.appendChild(p[8])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_for2(p):
    """seq_stmt_for : FOR ID IN range LOOP sequential_stmt_list END LOOP"""
    e = xml_document.createElement('forSequentialStatement')
    location(p, e)
    e.setAttribute('id', p[2])
    e.appendChild(p[4])
    e.appendChild(p[6])
    p[0] = e

#---- seq statement next - 20080923 - xsd
def p_seq_stmt_next1(p):
    """seq_stmt_next : NEXT ID WHEN expr
                     | NEXT ID"""
    e = xml_document.createElement('nextSequentialStatement')
    location(p, e)
    e.setAttribute('label', p[2])
    if p[4] != None:
        e.appendChild(p[4])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_next2(p):
    """seq_stmt_next : NEXT WHEN expr
                     | NEXT"""
    e = xml_document.createElement('nextSequentialStatement')
    location(p, e)
    if p[3] != None:
        e.appendChild(p[3])
    p[0] = e

#---- seq statement exit - 20080923 - xsd
def p_seq_stmt_exit1(p):
    """seq_stmt_exit : EXIT ID WHEN expr
                     | EXIT ID"""
    e = xml_document.createElement('exitSequentialStatement')
    location(p, e)
    e.setAttribute('label', p[2])
    if p[4] != None:
        e.appendChild(p[4])
    p[0] = e

# - 20080923 - xsd
def p_seq_stmt_exit2(p):
    """seq_stmt_exit : EXIT WHEN expr
                     | EXIT"""
    e = xml_document.createElement('exitSequentialStatement')
    location(p, e)
    if p[3] != None:
        e.appendChild(p[3])
    p[0] = e

#---- seq statement return - 20080923 - xsd
def p_seq_stmt_return(p):
    """seq_stmt_return : RETURN expr
                       | RETURN"""
    e = xml_document.createElement('returnSequentialStatement')
    location(p, e)
    if p[2] != None:
        e.appendChild(p[2])
    p[0] = e

#---- seq statement null - 20080923 - xsd
def p_seq_stmt_null(p):
    "seq_stmt_null : NULL"
    e = xml_document.createElement('nullSequentialStatement')
    location(p, e)
    p[0] = e

###############################################################################
# 5. Parallel Statements
###############################################################################

#-------- parallel statement list - 20080722 - xsd
def p_parallel_stmt_list_opt1(p):
    """parallel_stmt_list_opt : parallel_stmt_list"""
    p[0] = p[1]

#-------- parallel statement list - 20080809 - xsd
def p_parallel_stmt_list_opt2(p):
    """parallel_stmt_list_opt : empty"""

#-------- parallel statement list - 20080722 - xsd
def p_parallel_stmt_list1(p):
    """parallel_stmt_list : parallel_stmt ';'"""
    e = xml_document.createElement('parallelStatements')
    e.appendChild(p[1])
    p[0] = e

#-------- parallel statement list - 20080722 - xsd
def p_parallel_stmt_list2(p):
    """parallel_stmt_list : parallel_stmt_list parallel_stmt ';'"""
    p[1].appendChild(p[2])
    p[0] = p[1]
   

#-------- parallel statement - 20080725 - xsd
def p_parallel_stmt(p):
    """parallel_stmt : par_stmt_block
                     | par_stmt_process
                     | par_stmt_proc_call
                     | par_stmt_assign
                     | par_stmt_assert
                     | par_stmt_with
                     | par_stmt_comp
                     | par_stmt_entity
                     | par_stmt_configuration
                     | par_stmt_if
                     | par_stmt_for"""
    p[0] = p[1]


#---- parallel statement block - 20080820 - xsd
def p_par_stmt_block(p):
    "par_stmt_block : ID ':' BLOCK is_opt par_generic_opt par_port_opt declaration_list BEGIN parallel_stmt_list_opt END BLOCK id_opt"
    e = xml_document.createElement('blockParallelStatement')
    e.setAttribute('label', p[1])
    location(p, e)
    if p[5] != None:
        e.appendChild(p[5])
    if p[6] != None:
        e.appendChild(p[6])
    if p[7].hasChildNodes():
        e.appendChild(p[7])
    if p[9] != None:
        e.appendChild(p[9])
    p[0] = e

#---- 20080820 - xsd
def p_par_generic_opt1(p):
    """par_generic_opt : GENERIC '(' id_type_list ')' ';' generic_map_key_opt"""
    if p[6] != None:
        p[3].appendChild(p[6])
    p[0] = p[3]

#---- 20080820 - xsd
def p_par_generic_opt2(p):
    """par_generic_opt : empty"""

#---- 20080820 - xsd
def p_par_port_opt1(p):
    """par_port_opt : PORT '(' id_port_type_list ')' ';' port_map_key_opt"""
    if p[6] != None:
        p[3].appendChild(p[6])
    p[0] = p[3]
                       
#---- 20080820 - xsd
def p_par_port_opt2(p):
    """par_port_opt : empty"""
                       
#---- parallel statement process - 20080919 - xsd
def p_par_stmt_process1a(p):
    "par_stmt_process : POSTPONED PROCESS process_sens_list_opt declaration_list BEGIN sequential_stmt_list_opt END postponed_opt PROCESS id_opt"
    e = xml_document.createElement('processParallelStatement')
    location(p, e)
    e.setAttribute('postponed', 'true')
    if p[3] != None:
        e.appendChild(p[3])
    if p[4].hasChildNodes():
        e.appendChild(p[4])
    if p[6] != None:
        e.appendChild(p[6])
    p[0] = e

#- 20080919 - xsd
def p_par_stmt_process1b(p):
    "par_stmt_process : PROCESS process_sens_list_opt declaration_list BEGIN sequential_stmt_list_opt END postponed_opt PROCESS id_opt"
    e = xml_document.createElement('processParallelStatement')
    location(p, e)
    e.setAttribute('postponed', 'false')
    if p[2] != None:
        e.appendChild(p[2])
    if p[3].hasChildNodes():
        e.appendChild(p[3])
    if p[5] != None:
        e.appendChild(p[5])
    p[0] = e

#-------- 20080904 - xsd
def p_par_stmt_process2(p):
    "par_stmt_process : ID ':' postponed_opt PROCESS process_sens_list_opt declaration_list BEGIN sequential_stmt_list_opt END postponed_opt PROCESS id_opt"
    e = xml_document.createElement('processParallelStatement')
    e.setAttribute('label', p[1])
    location(p, e)
    if p[3] != None:
        e.setAttribute('postponed', 'true')
    else:
        e.setAttribute('postponed', 'false')
    if p[5] != None:
        e.appendChild(p[5])
    if p[6].hasChildNodes():
        e.appendChild(p[6])
    if p[8] != None:
        e.appendChild(p[8])
    p[0] = e

#-------- 20080724 - xsd
def p_process_sens_list_opt1(p):
    """process_sens_list_opt : '(' expr_comma_list ')'"""
    p[0] = p[2]

#-------- 20080724 - xsd
def p_process_sens_list_opt2(p):
    """process_sens_list_opt : empty"""

#-------- 20081029 - xsd
def p_expr_comma_list1(p):
    """expr_comma_list : expressions_or_parameters"""
    p[0] = p[1]

#-------- 20081029 - xsd
def p_expr_comma_list2(p):
    """expr_comma_list : range"""
    p[0] = p[1]

#---- parallel statement proc call - 20081015 - xsd
def p_par_stmt_proc_call1(p):
    "par_stmt_proc_call : ID ':' par_stmt_proc_call_body"
    # diky nejednoznacnosti gramatiky tu vznika nejednoznacnost, zda se vola
    # procedura nebo se instancuje komponenta
    # nejednoznacnost kvuli temto pravidlum:
    #
    # parallel_stmt ::=
    #     par_stmt_comp
    #   | par_stmt_proc_call
    # par_stmt_comp ::=       ID ':' ID map_opt
    # par_stmt_proc_call ::=  ID ':' ID
    # map_opt ::= empty
    #
    # Takze, pokud p[3] obsahuje pouze ID a to identifikuje komponentu,
    # jedna se o par_stmt_comp.
    e = p[3]
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'false')
    p[0] = e

# - 20081015 - xsd
def p_par_stmt_proc_call2(p):
    "par_stmt_proc_call : par_stmt_proc_call_body"
    e = p[1]
    e.setAttribute('postponed', 'false')
    p[0] = e

# - 20081015 - xsd
def p_par_stmt_proc_call3(p):
    "par_stmt_proc_call : POSTPONED par_stmt_proc_call_body"
    e = p[2]
    e.setAttribute('postponed', 'true')
    p[0] = e

# - 20081015 - xsd
def p_par_stmt_proc_call4(p):
    "par_stmt_proc_call : ID ':' POSTPONED par_stmt_proc_call_body"
    e = p[4]
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'true')
    p[0] = e

# - 20081015 - xsd
def p_par_stmt_proc_call_body(p):
    "par_stmt_proc_call_body : id_item"
    # id_item has to be something like: ID(parameters or range),
    # where ID must be existing function/procedure identifier
    p[1].tagName('procedureParallelStatement')
    p[0] = p[1]

#---- parallel statement signal assign - 20080919 - xsd
# VHDL93 version
def p_par_stmt_assign1(p):
    "par_stmt_assign : ID ':' POSTPONED par_stmt_assign_part"
    e = p[4][1]
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'true')
    location(p, e)
    e.insertBefore(p[4][0], e.firstChild)
    p[0] = e

# - 20080919 - xsd
def p_par_stmt_assign2(p):
    "par_stmt_assign : ID ':' par_stmt_assign_part"
    e = p[3][1]
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'false')
    location(p, e)
    e.insertBefore(p[3][0], e.firstChild)
    p[0] = e


# - 20080919 - xsd
def p_par_stmt_assign3(p):
    "par_stmt_assign : POSTPONED par_stmt_assign_part"
    e = p[2][1]
    e.setAttribute('postponed', 'true')
    location(p, e)
    e.insertBefore(p[2][0], e.firstChild)
    p[0] = e

# - 20081029 - xsd
def p_par_stmt_assign4(p):
    "par_stmt_assign : par_stmt_assign_part"
    e = p[1][1]
    e.setAttribute('postponed', 'false')
    location(p, e, getLineTarget(p[1][0]))
    e.insertBefore(p[1][0], e.firstChild)
    p[0] = e

#- 20080920 - xsd
#return (id_object, par_stmt_assign_expr)
def p_par_stmt_assign_part1ab(p):
    "par_stmt_assign_part : target LE options par_stmt_assign_expr"
    p[4].setAttribute('guarded', p[3][0])
    if p[3][1] != None:
        p[4].setAttribute('delay', p[3][1])
    if p[3][2] != None:
        p[4].insertBefore(p[3][2], p[4].firstChild)
    p[0] = (p[1], p[4])

#---- assign expr - 20080904 - xsd
def p_par_stmt_assign_expr1(p):
    "par_stmt_assign_expr : signal_value"
    e = xml_document.createElement('assignParallelStatement')
    e.appendChild(p[1])
    p[0] = e

#- 20080904 - xsd
def p_par_stmt_assign_expr2a(p):
    "par_stmt_assign_expr : signal_value WHEN expr ELSE par_stmt_assign_expr"
    e = xml_document.createElement('when')
    e.appendChild(p[3])
    p[1].appendChild(e)
    p[5].insertBefore(p[1], p[5].firstChild)  
    p[0] = p[5]

#---- signal value - 20080904 - xsd
def p_signal_value(p):
    """signal_value : expr_list"""
    e = xml_document.createElement('signalValue')
    e.appendChild(p[1])
    p[0] = e

#- 20080904 - xsd
def p_signal_value1(p):
    """signal_value : UNAFFECTED"""
    e = xml_document.createElement('signalValue')
    e1 = xml_document.createElement(p[1])
    e.appendChild(e1)
    p[0] = e

#---- parallel statement assert - 20080910 - xsd
def p_par_stmt_assert1(p):
    """par_stmt_assert : ID ':' POSTPONED ASSERT expr report_opt severity_opt"""
    e = xml_document.createElement('assertParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'true')
    location(p, e)
    e.appendChild(p[5])
    if p[6] != None:
        e.setAttribute('report', p[6])
    if p[7] != None:
        e.setAttribute('severity', p[7])
    p[0] = e

# - 20080910 - xsd
def p_par_stmt_assert2(p):
    """par_stmt_assert : ID ':' ASSERT expr report_opt severity_opt"""
    e = xml_document.createElement('assertParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'false')
    location(p, e)
    e.appendChild(p[4])
    if p[5] != None:
        e.setAttribute('report', p[5])
    if p[6] != None:
        e.setAttribute('severity', p[6])
    p[0] = e

# - 20080910 - xsd
def p_par_stmt_assert3(p):
    """par_stmt_assert : POSTPONED ASSERT expr report_opt severity_opt"""
    e = xml_document.createElement('assertParallelStatement')
    e.setAttribute('postponed', 'true')
    location(p, e)
    e.appendChild(p[3])
    if p[4] != None:
        e.setAttribute('report', p[4])
    if p[5] != None:
        e.setAttribute('severity', p[5])
    p[0] = e

# - 20080910 - xsd
def p_par_stmt_assert4(p):
    """par_stmt_assert : ASSERT expr report_opt severity_opt"""
    e = xml_document.createElement('assertParallelStatement')
    e.setAttribute('postponed', 'false')
    location(p, e)
    e.appendChild(p[2])
    if p[3] != None:
        e.setAttribute('report', p[3])
    if p[4] != None:
        e.setAttribute('severity', p[4])
    p[0] = e

# - 20080910 - xsd
def p_report_opt1(p):
    """report_opt : REPORT CLITERAL"""
    p[0] = p[2]

# - 20080910 - xsd
def p_report_opt2(p):
    """report_opt : empty"""

# - 20080910 - xsd
def p_severity_opt1(p):
    """severity_opt : SEVERITY NOTE
                    | SEVERITY WARNING
                    | SEVERITY ERROR
                    | SEVERITY FAILURE"""
    p[0] = p[2]

# - 20080910 - xsd
def p_severity_opt2(p):
    """severity_opt : empty"""

#---- parallel statement select - 20080923 - xsd
def p_par_stmt_with1(p):
    "par_stmt_with : ID ':' POSTPONED WITH expr SELECT target LE options selected_waveforms"
    e = p[10]
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'true')
    location(p, e)
    if p[9][1] != None:
        e.setAttribute('delay', p[9][1])
    if p[9][2] != None:
        e.insertBefore(p[9][2], e.firstChild)
    e.insertBefore(p[7], e.firstChild)
    e.insertBefore(p[5], e.firstChild)
    e.setAttribute('guarded', p[9][0])
    p[0] = e

# - 20080923 - xsd
def p_par_stmt_with2(p):
    "par_stmt_with : ID ':' WITH expr SELECT target LE options selected_waveforms"
    e = p[9]
    e.setAttribute('label', p[1])
    e.setAttribute('postponed', 'false')
    location(p, e)
    if p[8][1] != None:
        e.setAttribute('delay', p[8][1])
    if p[8][2] != None:
        e.insertBefore(p[8][2], e.firstChild)
    e.insertBefore(p[6], e.firstChild)
    e.insertBefore(p[4], e.firstChild)
    e.setAttribute('guarded', p[8][0])
    p[0] = e

# - 20080923 - xsd
def p_par_stmt_with3(p):
    "par_stmt_with : POSTPONED WITH expr SELECT target LE options selected_waveforms"
    e = p[8]
    e.setAttribute('postponed', 'true')
    location(p, e)
    if p[7][1] != None:
        e.setAttribute('delay', p[7][1])
    if p[7][2] != None:
        e.insertBefore(p[7][2], e.firstChild)
    e.insertBefore(p[5], e.firstChild)
    e.insertBefore(p[3], e.firstChild)
    e.setAttribute('guarded', p[7][0])
    p[0] = e

# - 20080923 - xsd
def p_par_stmt_with4(p):
    "par_stmt_with : WITH expr SELECT target LE options selected_waveforms"
    e = p[7]
    e.setAttribute('postponed', 'false')
    location(p, e)
    if p[6][1] != None:
        e.setAttribute('delay', p[6][1])
    if p[6][2] != None:
        e.insertBefore(p[6][2], e.firstChild)
    e.insertBefore(p[4], e.firstChild)
    e.insertBefore(p[2], e.firstChild)
    e.setAttribute('guarded', p[6][0])
    p[0] = e

# - 20081024 - xsd
def p_target1(p):
    "target : name"
    p[0] = p[1]

# - 20081024 - xsd
def p_name1(p):
    "name : id_object"
    p[0] = p[1]
    
# - 20081016 - xsd
def p_name2(p):
    "name : id_object attribute_selection"
    p[1].appendChild(p[2])
    p[0] = p[1]

# - 20081016 - xsd
def p_attribute_selection1(p):
    "attribute_selection : APOSTROPHE ID"
    e = xml_document.createElement('attribute')
    e.setAttribute('id', p[2])
    location(p, e)
    p[0] = e

# - 20081016 - xsd
def p_attribute_selection2(p):
    "attribute_selection : APOSTROPHE ID '(' expr ')'"
    e = xml_document.createElement('attribute')
    e.setAttribute('id', p[2])
    location(p, e)
    e.appendChild(p[4])
    p[0] = e

# btw, VHDL sucks! Its constructs (is it a procedure call, indexing or just
# this Id is a function call or value of some object?) are context sensitive.
# The original grammar is really mess created by some HW developer, I spent
# almost a day of harvesting grammar rules to transform them to something
# simple like the following, instead of doing serious work. Dont want to be
# rude, but 'got some nasty words on my mind!
# And yes, it really IS simple wrt. "VHDL Std" version.

# id_object is something which starts with ID and optionally follows with
# some refinement. Beware, that the same sentence could be either function call
# or indexing of an array object.
# e.g., p(i)(j) is:
#   1. function call of function p with parameter (i), which returns an array object; which is indexed by number j
#   2. indexing of an array p, which is two-dimensional field
#   ...

# - 20081017 - xsd
def p_id_object1(p):
    "id_object : id_item"
    p[0] = p[1]

# string suffix - 20081017 - xsd
def p_id_object2(p):
    "id_object : id_object DOT suffix"
    if p[1].tagName == 'recordExpression':
        p[1].appendChild(p[3])
        p[0] = p[1]
    else:
        e = xml_document.createElement('recordExpression')
        e.appendChild(p[1])
        e.appendChild(p[3])
        p[0] = e

# - 20081017 - xsd
def p_suffix1(p):
    "suffix : id_item"
    # selected suffix, i.e. record field selection
    # e.g., p(i).q(j) which could mean the function call returning the record,
    # which has the field 'q' of an array type
    p[0] = p[1]
    
# - 20081017 - xsd
def p_suffix2(p):
    # actually, don't know what that means, but VHDL allows it
    # CLITERAL is a simple string, like "Hello" or whatever
    """suffix : CLITERAL
              | ALL"""
    e = xml_document.createElement('suffix')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = e

# - 20081015 - xsd
def p_id_item1(p):
    "id_item : id_item '(' expressions_or_parameters ')'"
    # (a) function/procedure call with parameters
    # (b) indexing of id_object
    # if the expression list has more than one item, then it is definitely
    # the function call
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20081015 - xsd
def p_id_item2(p):
    "id_item : id_item '(' range ')'"
    # (a) function/procedure call with parameters
    # (b) indexing of id_object
    # depends on the type of id_object
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20081015 - xsd
def p_id_item3(p):
    "id_item : ID"
    e = xml_document.createElement('objectExpression')
    e.setAttribute('id', p[1])
    location(p, e)
    p[0] = e

# - 20081009 - xsd
def p_expressions1(p):
    "expressions_or_parameters : parid"
    e = xml_document.createElement('parameters')
    e.appendChild(p[1])
    p[0] = e

# - 20081009 - xsd
def p_expressions2(p):
    "expressions_or_parameters : expressions_or_parameters ',' parid"
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20081024 - xsd
def p_target2(p):
    "target : aggregate"
    p[0] = p[1]

# - 20081024 - xsd
def p_aggregate(p):
    "aggregate : '(' element_association_list ')'"
    p[0] = p[1]

# - 20081024 - xsd
def p_element_association_list1(p):
    "element_association_list : element_association"
    e = xml_document.createElement('aggregateExpression')
    e.appendChild(p[1])
    p[0] = e 

# - 20081024 - xsd
def p_element_association_list2(p):
    "element_association_list : element_association_list ',' element_association"
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20081024 - xsd
def p_element_association1(p):
    "element_association : expr"
    p[0] = p[1]

# - 20081024 - xsd
def p_element_association2(p):
    "element_association : choice_expr_list_item"
    p[0] = p[1]

# - 20080920 - xsd
# options ::= [guarded] [delay_mechanism]
# (guarded, delay, reject)
def p_options1(p):
    "options : "
    p[0] = ('false', None, None)

# - 20080920 - xsd
def p_options2(p):
    "options : GUARDED"
    p[0] = ('true', None, None)

# - 20080920 - xsd
def p_options3(p):
    "options : delay_mechanism"
    p[0] = ('false', p[2][0], p[2][1])

# - 20080920 - xsd
def p_options4(p):
    "options : GUARDED delay_mechanism"
    p[0] = ('true', p[2][0], p[2][1])
    
# - 20080920 - xsd
def p_delay_mechanism1(p):
    "delay_mechanism : TRANSPORT"
    p[0] = (p[1], None)

# - 20080920 - xsd
def p_delay_mechanism2(p):
    "delay_mechanism : INERTIAL"
    p[0] = (p[1], None)

# - 20080920 - xsd
def p_delay_mechanism3(p):
    "delay_mechanism : REJECT time INERTIAL"
    e = xml_document.createElement('reject')
    e.appendChild(p[2])
    p[0] = (p[3], e)

# selected_waveforms ::= waveform WHEN choices { , waveform WHEN choices } - 20080923 - xsd
def p_selected_waveforms1(p):
    "selected_waveforms : waveform WHEN choice_list"
    e = xml_document.createElement('selectParallelStatement')
    e1 = xml_document.createElement('when')
    e1.appendChild(p[3])
    p[1].appendChild(e1)
    e.appendChild(p[1])
    p[0] = e

# - 20080923 - xsd
def p_selected_waveforms2(p):
    "selected_waveforms : selected_waveforms ',' waveform WHEN choice_list"
    e = xml_document.createElement('when')
    e.appendChild(p[5])
    p[3].appendChild(e)
    p[1].appendChild(p[3])
    p[0] = p[1]

# - 20080923 - xsd
# waveform ::=
#       waveform_element { , waveform_element }
#     | unaffected
def p_waveform1(p):
    "waveform : waveform_element_list"
    e = xml_document.createElement('signalValue')
    e.appendChild(p[1])
    p[0] = e

# - 20080923 - xsd
def p_waveform2(p):
    "waveform : UNAFFECTED"
    e = xml_document.createElement('signalValue')
    e1 = xml_document.createElement(p[1])
    e.appendChild(e1)
    p[0] = e

# - 20080923 - xsd
def p_waveform_element_list1(p): # stejne jako expr_list az na waveform_element2
    "waveform_element_list : waveform_element"
    e = xml_document.createElement('expressions')
    e.appendChild(p[1])
    p[0] = e

# - 20080923 - xsd
def p_waveform_element_list2(p):
    "waveform_element_list : waveform_element_list ',' waveform_element"
    p[1].appendChild(p[3])
    p[0] = p[1]


# - 20080923 - xsd
# waveform_element ::= 
#       value_expression [after time_expression]
#     | null [after time_expression]
def p_waveform_element1(p):
    "waveform_element : expr_list_item"
    p[0] = p[1]

# - 20080923 - xsd
def p_waveform_element2(p):
    "waveform_element : NULL expr_list_after_opt"
    e1 = xml_document.createElement('null')
    if p[2] == None:
        p[0] = e1
        location(p, e1)
    else:
        e = xml_document.createElement('afterExpression')
        location(p, e)
        e.appendChild(e1)
        e.appendChild(p[2][0])
        p[0] = e

# - 20081024 - xsd
def p_par_stmt_comp(p):
    "par_stmt_comp : ID ':' ID map_forced"
    e = xml_document.createElement('componentParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[3])
    location(p, e)
    if p[4][0] != None:
        e.appendChild(p[4][0])
    if p[4][1] != None:
        e.appendChild(p[4][1])
    p[0] = e

#---- parallel statement entity (VHDL93) - 20080919 - xsd
def p_par_stmt_entity1(p):
    """par_stmt_entity : ID ':' ENTITY ID DOT ID '(' ID ')' map_opt"""
    e = xml_document.createElement('entityParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4]+p[5]+p[6])
    e.setAttribute('architecture', p[8])
    location(p, e)
    if p[10][0] != None:
        e.appendChild(p[10][0])
    if p[10][1] != None:
        e.appendChild(p[10][1])
    p[0] = e

#---- parallel statement entity (VHDL93) - 20080919 - xsd
def p_par_stmt_entity2(p):
    """par_stmt_entity : ID ':' ENTITY ID DOT ID map_opt"""
    e = xml_document.createElement('entityParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4]+p[5]+p[6])
    location(p, e)
    if p[7][0] != None:
        e.appendChild(p[7][0])
    if p[7][1] != None:
        e.appendChild(p[7][1])
    p[0] = e

#---- parallel statement entity (VHDL93) - 20080919 - xsd
def p_par_stmt_entity3(p):
    """par_stmt_entity : ID ':' ENTITY ID '(' ID ')' map_opt"""
    e = xml_document.createElement('entityParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4])
    e.setAttribute('architecture', p[6])
    location(p, e)
    if p[8][0] != None:
        e.appendChild(p[8][0])
    if p[8][1] != None:
        e.appendChild(p[8][1])
    p[0] = e

#---- parallel statement entity (VHDL93) - 20080919 - xsd
def p_par_stmt_entity4(p):
    """par_stmt_entity : ID ':' ENTITY ID map_opt"""
    e = xml_document.createElement('entityParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4])
    location(p, e)
    if p[5][0] != None:
        e.appendChild(p[5][0])
    if p[5][1] != None:
        e.appendChild(p[5][1])
    p[0] = e

#---- parallel statement configuriaton (VHDL93) - 20080919 - xsd
def p_par_stmt_configuration1(p):
    """par_stmt_configuration : ID ':' CONFIGURATION ID DOT ID map_opt"""
    e = xml_document.createElement('configurationParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4]+p[5]+p[6])
    location(p, e)
    if p[7][0] != None:
        e.appendChild(p[7][0])
    if p[7][1] != None:
        e.appendChild(p[7][1])
    p[0] = e

#---- parallel statement configuration (VHDL93) - 20080919 - xsd
def p_par_stmt_configuration2(p):
    """par_stmt_configuration : ID ':' CONFIGURATION ID map_opt"""
    e = xml_document.createElement('configurationParallelStatement')
    e.setAttribute('label', p[1])
    e.setAttribute('id', p[4])
    location(p, e)
    if p[5][0] != None:
        e.appendChild(p[5][0])
    if p[5][1] != None:
        e.appendChild(p[5][1])
    p[0] = e

#---- parallel statement if - 20080919 - xsd
def p_par_stmt_if(p):
    """par_stmt_if : ID ':' IF expr GENERATE parallel_stmt_list_opt END GENERATE ID
                   | ID ':' IF expr GENERATE parallel_stmt_list_opt END GENERATE"""
    e = xml_document.createElement('ifParallelStatement')
    e.setAttribute('label', p[1])
    location(p, e)
    e.appendChild(p[4])
    if p[6] != None:
        e1 = xml_document.createElement('generate')
        e1.appendChild(p[6])
        e.appendChild(e1)
    p[0] = e

#---- parallel statement for - 20080919 - xsd
def p_par_stmt_for(p):
    """par_stmt_for : ID ':' FOR ID IN range GENERATE parallel_stmt_list_opt END GENERATE ID
                    | ID ':' FOR ID IN range GENERATE parallel_stmt_list_opt END GENERATE"""
    e = xml_document.createElement('forParallelStatement')
    e.setAttribute('label', p[1])
    location(p, e)
    e.setAttribute('id', p[4])
    e.appendChild(p[6])
    if p[8] != None: 
        e1 = xml_document.createElement('generate')
        e1.appendChild(p[8])
        e.appendChild(e1)
    p[0] = e

###############################################################################
# 6. Others
###############################################################################
def p_error(p):
    if p:
        print >>sys.stderr, "%s:%d:invalid syntax `%s'" % \
            (p.lexer.filename, p.lexer.lineno, p.value)
        yacc.errok()
    else:
        print >>sys.stderr, \
            '%s:%d:unexpected EOF' % (lexer.filename, lexer.lineno)

# build the parser
import yacc
yacc.yacc(method='LALR')

entities=[]

###############################################################################
# READER
###############################################################################

def parse_file(filename):
    """parse_file(filename, abstract_content=None) parse file. Use abstract
    content (if available) instead of file content."""
    lexer.filename = filename
    if os.access(filename, os.R_OK):
        f = open(filename)
        content = f.read()
        f.close()
        yacc.parse(content)
    else:
        raise IOError('could not read %s' % filename)

if __name__ == "__main__":
    if len(sys.argv)>1:
        for file_arg in sys.argv[1:]:
            # build the lexer
            lexer = lex.lex()
            # initialize public variables
            DOMimplement = getDOMImplementation()
            xml_document = DOMimplement.createDocument(None, "vhdl", None)
            top_element = xml_document.documentElement
            top_element.setAttribute('file', file_arg)
            top_element.setAttribute('xmlns:xsi',
                    'http://www.w3.org/2001/XMLSchema-instance') 
            top_element.setAttribute('xsi:noNamespaceSchemaLocation',
                    'http://www.liberouter.org/formal_verification/tools/vhd2xml/vhdl.xsd')
            #debug = True
            print file_arg
            parse_file(file_arg)
            filename = file_arg+'.xml'
            xml_file = open(filename, 'w')
            xml_file.write(xml_document.toprettyxml("  "))
            xml_file.close()
            print '------------ done'
    else:
        print >>sys.stderr, 'syntax: %s file.vhd' % sys.argv[0]

