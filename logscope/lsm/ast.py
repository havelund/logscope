

# -----------------------------------------------------------------------------
# ast.py                           
#                                                         
# PLY abstract syntax (AST nodes) for the LogScope specification language                
# ----------------------------------------------------------------------------- 

###########################
### auxiliary functions ###
###########################

INDENT = 0

def indent():
    global INDENT
    INDENT = INDENT + 1

def dedent():
    global INDENT
    INDENT = INDENT - 1

def spaces():
    global INDENT
    spaces = ""
    for x in range(0,INDENT):
        spaces += "  "
    return spaces

def stringOf(elem):
    if isinstance(elem,str):
        return "\"" + str(elem) + "\""
    else:
        return str(elem)

def list2string(list):
    comma = False
    text = ""
    for elem in list:
        if comma:
            text += ", "
        else:
            comma = True
        text += str(elem)
    return text

def list2stringQuoted(list):
    comma = False
    text = ""
    for elem in list:
        if comma:
            text += ", "
        else:
            comma = True
        text += stringOf(elem)
    return text


#################
### AST Nodes ###
#################

class Specification:
    def __init__(self,monitors,python=None):
        self.monitors = monitors
        self.python = python

    def getSpecUnit(self,unitName):
        assert isinstance(unitName,str)
        for monitor in self.monitors:
            if unitName == monitor.name:
                return monitor
        return None

    def __repr__(self):
        text = "\n"
        if self.python != None:
            text += self.python + "\n\n"
        for monitor in self.monitors:
            text += str(monitor) + "\n\n"
        return text

class Automaton:
    def __init__(self,name,states,initial,forbidden,success):
        self.name = name
        self.states = states
        self.initial = initial
        self.forbidden = forbidden
        self.success = success

    def __repr__(self):
        text = ""
        text = "automaton " + self.name + " {\n\n"
        indent()
        for state in self.states:
            text += str(state)
        if self.initial != []:
            text += "  initial " + list2string(self.initial) + "\n"
        if self.forbidden != []:
            text += "  hot " + list2string(self.forbidden) + "\n"
        if self.success != []:
            text += "  success " + list2string(self.success) + "\n"
        dedent()
        text += "}"
        return text

class State:
    def __init__(self,modifiers,mode,name,formals,rules):
        self.modifiers = modifiers
        self.mode = mode
        self.name = name
        self.formals = formals
        self.rules = rules

    def __repr__(self):
        modifiertext = ""
        if "initial" in self.modifiers:
            modifiertext = "initial "
        for modifier in self.modifiers:
            if modifier != "initial":
                modifiertext += modifier + " "
        if self.formals != []:
            formalstext = "(" + list2string(self.formals) + ")"
        else:
            formalstext = ""
        text = spaces() + modifiertext + self.mode + " " + self.name + formalstext + " {\n"
        indent()
        for rule in self.rules:
            text += str(rule)
        dedent()
        text += spaces() + "}\n\n"
        return text

class Rule:
    def __init__(self,conditions,actions):
        self.conditions = conditions
        self.actions = actions

    def __repr__(self):
        return spaces() + list2string(self.conditions) + " => " + list2string(self.actions) + "\n"

class Event:
    def __init__(self,type,constraints,predicate=None):
        self.type = type
        self.constraints = constraints
        self.predicate = predicate

    def __repr__(self):
        if self.predicate == None:
            predicatetext = ""
        else:
            predicatetext = " where " + str(self.predicate)
        return self.type + "{" + list2string(self.constraints) + "}" + predicatetext

class Constraint:
    def __init__(self,name,range):
        self.name = name
        self.range = range

    def __repr__(self):
        return self.name + " : " + stringOf(self.range)

class Name:
    def __init__(self,name):
        self.name = name
        
    def __repr__(self):
        return self.name

class Interval:
    def __init__(self,left,right):
        self.left = left
        self.right = right

    def __repr__(self):
        return "[" + str(self.left) + "," + str(self.right) + "]"

class BitValues:
    def __init__(self,dict):
        self.dict = dict

    def __repr__(self):
        text = "{"
        maybecomma = ""
        for bit in sorted(self.dict.keys()):
            value = self.dict[bit]
            text += maybecomma + str(bit) + ":" + stringOf(value)
            maybecomma = ","
        text += "}"
        return text

class AtomicPredicate:
    def __init__(self,funname,arguments):
        self.funname = funname
        self.arguments = arguments

    def evaluate(self,localbinding,globalbinding,environment):
        actuals = []
        for argument in self.arguments:
            if isinstance(argument,int) or isinstance(argument,str):
                actuals.append(argument)
            elif isinstance(argument,Name):
                name = argument.name
                if name in localbinding:
                    value = localbinding[name]
                elif name in globalbinding:
                    value = globalbinding[name]
                else:
                    assert False , "predicate argument not defined: " + str(name) + " in: " + str(self) 
                actuals.append(value)
            else:
                assert False , "argument not an int, string or name: " + str(argument)
        function = eval(self.funname,environment)
        return apply(function,actuals)

    def __repr__(self):
        return self.funname + "(" + list2stringQuoted(self.arguments) + ")"

class ExpressionPredicate:
    def __init__(self,expression):
        self.expression = expression

    def evaluate(self,localbinding,globalbinding,environment):
        env = {}
        env.update(environment)
        env.update(globalbinding)
        env.update(localbinding)
        return eval(self.expression,env)

    def __repr__(self):
        return "|" + self.expression + "|"

class AndPredicate:
    def __init__(self,predicate1,predicate2):
        self.predicate1 = predicate1
        self.predicate2 = predicate2

    def evaluate(self,localbinding,globalbinding,environment):
        return self.predicate1.evaluate(localbinding,globalbinding,environment) and self.predicate2.evaluate(localbinding,globalbinding,environment)
        
    def __repr__(self):
        return str(self.predicate1) + " and " + str(self.predicate2)

class OrPredicate:
    def __init__(self,predicate1,predicate2):
        self.predicate1 = predicate1
        self.predicate2 = predicate2

    def evaluate(self,localbinding,globalbinding,environment):
        return self.predicate1.evaluate(localbinding,globalbinding,environment) or self.predicate2.evaluate(localbinding,globalbinding,environment)

    def __repr__(self):
        return str(self.predicate1) + " or " + str(self.predicate2)

class NotPredicate:
    def __init__(self,predicate):
        self.predicate = predicate

    def evaluate(self,localbinding,globalbinding,environment):
        return not self.predicate.evaluate(localbinding,globalbinding,environment)

    def __repr__(self):
        return "not " + str(self.predicate)

class BracketedPredicate:
    def __init__(self,predicate):
        self.predicate = predicate

    def evaluate(self,localbinding,globalbinding,environment):
        return self.predicate.evaluate(localbinding,globalbinding,environment)

    def __repr__(self):
        return "(" + str(self.predicate) + ")"

class Action:
    def __init__(self,name,actuals=[]):
        self.name = name
        self.actuals = actuals

    def __repr__(self):
        text = self.name
        if self.actuals != []:
            text += "(" + list2stringQuoted(self.actuals) + ")"
        return text

class Pattern:
    def __init__(self,name,event,consequence):
        self.name = name
        self.event = event
        self.consequence = consequence

    def __repr__(self):
        text = "pattern " + self.name + " :\n"
        indent()
        text += spaces() + str(self.event) + " =>\n"
        indent()
        text += spaces() + str(self.consequence)
        dedent()
        dedent()
        return text
    
class NegatedEvent:
    def __init__(self,event):
        self.event = event

    def __repr__(self):
        return "!" + str(self.event)

def  consequences2string(consequencelist,begin,end):
    text = begin + "\n"
    indent()
    length = len(consequencelist)
    for index in range(0,length-1): # goes from 0 to (length-1)-1
        text += spaces() + str(consequencelist[index]) + ",\n"
    text += spaces() + str(consequencelist[length-1]) + "\n"
    dedent()
    text += spaces() + end
    return text

class ConsequenceSequence:
    def __init__(self,consequencelist):
        self.consequencelist = consequencelist

    def __repr__(self):
        return consequences2string(self.consequencelist,"[","]")

class ConsequenceSet:
    def __init__(self,consequencelist):
        self.consequencelist = consequencelist

    def __repr__(self):
        return consequences2string(self.consequencelist,"{","}")

