

# -----------------------------------------------------------------------------
# parser.py                           
#                                                         
# PLY lexer and parser for the LogScope specification language                          
# ----------------------------------------------------------------------------- 

import ply.lex as lex
import ply.yacc as yacc
 
from ast import *

__errors__ = False

#############
### Lexer ###
#############

tokens = (
    'AUTOMATON',
    'PATTERN',
    'PYTHON',
    'EXPRESSION',
    'IGNORE',
    'ALWAYS',
    'HOT',
    'STATE',
    'STEP',
    'INITIAL',
    'DONE',
    'ERROR',
    'SUCCESS',
    'COMMAND',
    'EVR',
    'CHANNEL',
    'CHANGE',
    'PRODUCT',
    'WHERE',
    'AND',
    'OR',
    'NOT',
    'NAME',
    'NUMBER',  
    'STRING',  
    'TRANS'
    )

literals = [':',';',',','(',')','{', '}','[',']','!','=']

RESERVED = {
  "automaton" : "AUTOMATON" ,
  "pattern" : "PATTERN"   ,
  "ignore" : "IGNORE"    ,
  "always" : "ALWAYS"    ,
  "hot" : "HOT"       ,
  "forbidden" : "HOT"       , # RuleR terminology
  "state" : "STATE"     ,
  "step" : "STEP"      ,
  "initial" : "INITIAL"   ,
  "success" : "SUCCESS"   ,
  "done" : "DONE"      ,
  "error" : "ERROR"     ,
  "COMMAND" : "COMMAND"   ,
  "EVR" : "EVR"       ,
  "CHANNEL" : "CHANNEL"   , 
  "CHANGE" : "CHANGE"    ,
  "PRODUCT" : "PRODUCT",
  "where" : "WHERE",
  "and" : "AND",
  "or" : "OR",
  "not" : "NOT"   
  }

def t_PYTHON(t):
    r':::(.|\n)*?:::'
    t.lexer.lineno += t.value.count('\n')
    t.value = t.value.strip(':')
    return t

def t_EXPRESSION(t):
    r'\|(.|\n)*?\|'
    t.lexer.lineno += t.value.count('\n')
    t.value = t.value.strip('|')
    return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_\.]*'
    t.type = RESERVED.get(t.value, "NAME")
    return t

def t_NUMBER(t):
    r'\d+'
    assert isinstance(t.value,str)
    t.value = int(t.value)
    assert isinstance(t.value,int)
    return t

#t_NUMBER      = r'\d+'
t_STRING      = r'\"([^\\\n]|(\\.))*?\"'
t_TRANS       = r'=>'

def t_comment_1(t):
    r'/\*(.|\n)*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_comment_2(t):
    r"[ ]*\043[^\n]*"  # \043 is '#'
    pass

t_ignore = " \t"

def t_newline(t):
    r'\n+'
    t.lexer.lineno += t.value.count("\n")

def find_column(input,token):
    i = token.lexpos
    while i > 0:
        if input[i] == '\n': break
        i -= 1
    column = (token.lexpos - i)+1
    return column

def t_error(t):
    global __errors__
    __errors__ = True
    lexpos = find_column(t.lexer.lexdata,t)
    print "lexer error, illegal character '%s', line '%s', pos '%s'" % (t.value[0],t.lineno,lexpos)
    t.lexer.skip(1)

# Build the lexer                                                                                                                 

lex.lex()


##############
### Parser ###
##############

### specifications ###

def p_specification_1(p):
    "specification : monitors"
    global __errors__
    if __errors__:
        p[0] = None
    else:
        p[0] = Specification(p[1])

def p_specification_2(p):
    "specification : PYTHON monitors"
    global __errors__
    if __errors__:
        p[0] = None
    else:
        p[0] = Specification(p[2],p[1])

def p_monitors_1(p):
    "monitors : monitor"
    p[0] = p[1]
    
def p_monitors_2(p):
    "monitors : monitors monitor"
    p[0] = p[1] + p[2]
    
def p_monitor_1(p):
    "monitor : IGNORE monitorspec"
    p[0] = []
    
def p_monitor_2(p):
    "monitor : monitorspec"
    p[0] = [p[1]]

def p_monitorspec_1(p):
    "monitorspec : automaton"
    p[0] = p[1]

def p_monitorspec_2(p):
    "monitorspec : pattern"
    p[0] = p[1]

### automata ###

def p_automaton(p):
    "automaton : AUTOMATON NAME '{' states initial forbidden success '}'"
    p[0] = Automaton(name=p[2],states=p[4],initial=p[5],forbidden=p[6],success=p[7])

def p_states_1(p):
    "states :"
    p[0] = []

def p_states_2(p):
    "states : state"
    p[0] = [p[1]]

def p_states_3(p):
    "states : states state"
    p[0] = p[1]
    p[0].append(p[2])

def p_state_1(p):
    "state : modifiers statekind NAME '{' rules '}'"
    p[0] = State(modifiers=p[1],mode=p[2],name=p[3],formals=[],rules=p[5])

def p_state_2(p):
    "state : modifiers statekind NAME '(' formals ')' '{' rules '}'"
    p[0] = State(modifiers=p[1],mode=p[2],name=p[3],formals=p[5],rules=p[8])

def p_modifiers_1(p):
    "modifiers :"
    p[0] = []

def p_modifiers_2(p):
    "modifiers : modifiers modifier"
    p[0] = p[1]
    p[0].append(p[2])

def p_modifiers_3(p):
    "modifiers : modifier"
    p[0] = [p[1]]

def p_modifier(p):
    '''modifier : HOT
                | INITIAL'''
    p[0] = p[1]

def p_formals(p):
    "formals : names"
    p[0] = p[1]
    
def p_statekind(p):
    '''statekind : ALWAYS
                 | STATE
                 | STEP'''
    p[0] = p[1]

def p_rules_1(p):
    "rules :"
    p[0] = []

def p_rules_2(p):
    "rules : rule"
    p[0] = [p[1]]

def p_rules_3(p):
    "rules : rules rule"
    p[0] = p[1]
    p[0].append(p[2])

def p_rule(p):
    "rule : conditions TRANS actions"
    p[0] = Rule(p[1],p[3])

def p_conditions(p):
    "conditions : event" # only one for now
    p[0] = [p[1]]
  
def p_event_1(p):
    "event : type '{' constraints '}'"
    p[0] = Event(p[1],p[3])

def p_event_2(p):
    "event : type '{' constraints '}' WHERE predicate" 
    p[0] = Event(p[1],p[3],p[6])

def p_type(p):
    '''type : COMMAND 
            | EVR 
            | CHANNEL 
            | CHANGE
            | PRODUCT'''
    p[0] = p[1]

def p_constraints_1(p):
    "constraints :"
    p[0] = []
    
def p_constraints_2(p):
    "constraints : constraint"
    p[0] = [p[1]]

def p_constraints_3(p):
    "constraints : constraints ',' constraint"
    p[0] = p[1]
    p[0].append(p[3])

def p_constraint(p):
    "constraint : NAME ':' range"
    p[0] = Constraint(p[1],p[3])

def p_range_1(p):
    "range : NUMBER"
    p[0] = p[1]
    assert isinstance(p[1],int)

def p_range_2(p):
    "range : STRING"
    p[0] = p[1].replace("\"","")

def p_range_3(p):
    "range : '[' NUMBER ',' NUMBER ']'"
    p[0] = Interval(p[2],p[4])

def p_range_4(p):
    "range : '{' bitvalues '}'"
    p[0] = BitValues(p[2])

def p_range_5(p):
    "range : NAME"
    p[0] = Name(p[1]) 
 
def p_bitvalues_1(p):
    "bitvalues :"
    p[0] = {}

def p_bitvalues_2(p):
    "bitvalues : bitvalue"
    p[0] = p[1]

def p_bitvalues_3(p):
    "bitvalues : bitvalues ',' bitvalue"
    p[0] = p[1]
    p[0].update(p[3])

def p_bitvalue(p) :
    "bitvalue : value ':' range"
    p[0] = {p[1] : p[3]}

def p_value_1(p) :
    "value : NUMBER"
    p[0] = p[1]
    assert isinstance(p[1],int)

def p_value_2(p):
    "value : STRING"
    p[0] = p[1].replace("\"","")

def p_predicate_1(p):
    "predicate : NAME '(' arguments ')'"
    p[0] = AtomicPredicate(p[1],p[3])

def p_predicate_2(p):
    "predicate : EXPRESSION"
    p[0] = ExpressionPredicate(p[1])

def p_predicate_3(p):
    "predicate : predicate AND predicate"
    p[0] = AndPredicate(p[1],p[3])

def p_predicate_4(p):
    "predicate : predicate OR predicate"
    p[0] = OrPredicate(p[1],p[3])

def p_predicate_5(p):
    "predicate : NOT predicate"
    p[0] = NotPredicate(p[2])

def p_predicate_6(p):
    "predicate : '(' predicate ')'"
    p[0] = BracketedPredicate(p[2])

precedence = (
    ('left' , 'OR'),
    ('left' , 'AND'),
    ('right', 'NOT')
)

def p_actions_1(p):
    "actions : action"
    p[0] = [p[1]]

def p_actions_2(p):
    "actions : actions ',' action"
    p[0] = p[1]
    p[0].append(p[3])

def p_action_1(p):
    "action : NAME"
    p[0] = Action(p[1])

def p_action_2(p):
    "action : NAME '(' arguments ')'"
    p[0] = Action(p[1],p[3])

def p_action_3(p):
    "action : DONE"
    p[0] = Action(p[1])

def p_action_4(p):
    "action : ERROR"
    p[0] = Action(p[1])

def p_arguments_1(p):
    "arguments : argument"
    p[0] = [p[1]]

def p_arguments_2(p):
    "arguments : arguments ',' argument"
    p[0] = p[1]
    p[0].append(p[3])

def p_argument_1(p):
    "argument : NUMBER"
    p[0] = p[1]

def p_argument_2(p):
    "argument : STRING"
    p[0] = p[1].replace("\"","")

def p_argument_3(p):
    "argument : NAME"
    p[0] = Name(p[1])

def p_initial_1(p):
    "initial :"
    p[0] = []

def p_initial_2(p):
    "initial : INITIAL actions"
    p[0] = p[2]

def p_forbidden_1(p):
    "forbidden :"
    p[0] = []

def p_forbidden_2(p):
    "forbidden : HOT names"
    p[0] = p[2]

def p_names_1(p):
    "names : NAME"
    p[0] = [p[1]]

def p_names_2(p):
    "names : names ',' NAME"
    p[0] = p[1]
    p[0].append(p[3])
    
def p_success_1(p):
    "success :" 
    p[0] = []

def p_success_2(p):
    "success : SUCCESS names"
    p[0] = p[2]


### patterns ###

def p_pattern(p):
    "pattern : PATTERN NAME ':' event TRANS consequence"
    p[0] = Pattern(name=p[2],event=p[4],consequence=p[6])

def p_consequence_1(p):
    "consequence : event"
    p[0] = p[1]

def p_consequence_2(p):
    "consequence : '!' event"
    p[0] = NegatedEvent(p[2])

def p_consequence_3(p):
    "consequence : '[' consequencelist ']'"
    p[0] = ConsequenceSequence(p[2])
    
def p_consequence_4(p):
    "consequence : '{' consequencelist '}'"
    p[0] = ConsequenceSet(p[2])

def p_consequencelist_1(p):
    "consequencelist : consequence"
    p[0] = [p[1]]

def p_eventlist_2(p):
    "consequencelist : consequencelist ',' consequence"
    p[0] = p[1]
    p[0].append(p[3])

def p_error(p):
    global __errors__
    __errors__ = True
    if p:
        print "Syntax error at '%s' in line '%s'" % (p.value , p.lineno)
    else:
        print "Syntax error at EOF"


##########################
### Running the parser ###
##########################

yacc.yacc()

def parse(file):
    data = open(file).read()
    spec = yacc.parse(data)
    return spec


