
########### OPTIONS: ###########

class Options:
    resultdir = "."
    debug = False
    inform = True
    once = False # not needed to be True for the moment
    filter = True
    statistics = True
    printstatistics = True
    history = True
    dumplog = True
    showtypes = True
    showprogress = True
    freqprogress = 100

LearningFields = {
      "COMMAND" : ["Stem"],
      "EVR"     : ["EventId","Module","Message","EventNumber"],
      "CHANNEL" : ["ChannelId","Module","DataNumber"],
      "CHANGE"  : ["ChannelId","Module","DataNumber"],
      "PRODUCT" : ["Name"]
      }

################################
### option setting functions ###
################################

def fieldsCOMMAND(fields):
    global LearningFields
    LearningFields["COMMAND"] = fields

def fieldsEVR(fields):
    global LearningFields
    LearningFields["EVR"] = fields

def fieldsCHANNEL(fields):
    global LearningFields
    LearningFields["CHANNEL"] = fields

def fieldsCHANGE(fields):
    global LearningFields
    LearningFields["CHANGE"] = fields

def fieldsPRODUCT(fields):
    global LearningFields
    LearningFields["PRODUCT"] = fields


### imports ###

import os
import sys
import time
import string
import re
import pickle
import event_list
from parser import yacc
import ast
 

### events ###

def mkEvent(kind,fields):
    event = fields.copy()
    event["OBJ_TYPE"] = kind
    return event

def strCmd(cmd):
    return "COMMAND(" + str(cmd) + ")"

def strDpr(dpr):
    return "PRODUCT(" + str(dpr) + ")"

def strEvr(evr):
    return "EVR(" + str(evr) + ")"

def strChannel(channel):
    return "CHANNEL(" + str(channel) + ")"

def strChange(change):
    return "CHANGE(" + str(change) + ")"
        
def strEvent(event):
    if isCmd(event):
        return strCmd(event)
    if isDpr(event):
        return strDpr(event)
    if isEvr(event):
        return strEvr(event)
    if isChannel(event):
        return strChannel(event)
    if isChange(event):
        return strChange(event)
    print str(event)
    assert False

def isCmd(event):
    return eventKind(event) == "COMMAND"

def isEvr(event):
    return eventKind(event) == "EVR"

def isChannel(event):
    return eventKind(event) == "CHANNEL"

def isChange(event):
    return eventKind(event) == "CHANGE"

def isDpr(event):
    return eventKind(event) == "PRODUCT"

def getScet(event):
    assert "SCET" in event
    return event["SCET"]

def compare(event1,event2):
    scet1 = getScet(event1)
    scet2 = getScet(event2)
    if scet1 < scet2:
        return -1
    if scet1 == scet2:
        return 0
    if scet1 > scet2:
        return 1  


### auxiliary functions and classes ###

def setResultDir(dir):
    print "results will be stored in the directory :" , dir
    Options.resultdir = dir

setDotDir = setResultDir # to be backwards compatible with naming

def borderline(l):
    line = ""
    for x in range(0,l+7):
        line += "="
    return line

def headlineString(string):
    length = len(string)
    text = "\n"
    text += borderline(length) + "\n"
    text += "   " + string + ":\n" 
    text += borderline(length) + "\n"
    text += "\n"
    return text

def headline(string):
    print headlineString(string)

def progressBar(x,y):
    size = 10
    fraction = float(x)/float(y)
    if fraction >=0.99:
        fraction = 1
    percentage = fraction*100
    count = int(float(size)*fraction)
    rest = size-count
    text = "%3d"  % percentage
    text += "% ["
    for x in range(count):
        text += "="
    for x in range(rest):
        text += "."
    text += "]"
    return text

def progress(x,y):
    percentage = int((float(x)*float(100))/float(y))
    if percentage == 0:
        percentage = 1
    elif percentage == 99:
        percentage = 100
    text = "%3d"  % percentage
    text += "%"
    return text

def debug(str):
    if Options.debug:
        print "--" , str

def inform(str):
    if Options.inform:
        print "--" , str 

def insight(string):
    print "@@@@@@\\\n" + str(string) + "\n@@@@@@/"

def min(x,y):
    if x <= y:
        return x
    else:
        return y
    
def max(x,y):
    if x >= y:
        return x
    else:
        return y

def sum(numberlist):
    total = 0
    for x in numberlist:
        total += x
    return total

def exists(list,predicate):
    for element in list:
        if predicate(element):
            return True
    return False

def overlaps(list1,list2):
    for element in list1:
        if element in list2:
            return True
    return False
          
def createRules(conditions,target):
    rules = []
    for condition in conditions:    
        rules.append(Rule([condition],[target]))
    return rules

def eventKind(event):
    assert isinstance(event,dict) , "*** event is not a dictionary: " + str(event) 
    return event.get("OBJ_TYPE",None)

def startswith(str1,str2):
    return string.count(str1,str2,0,len(str2)) > 0

def containsError(states):
    for state in states:
        if state.isErrorState():
            return True
    return False

def list2string(list,sep=","):
    text = ""
    separator = False
    for element in list:
        if separator:
            text += sep
        else:
            separator = True
        text += str(element)
    return text

def listonlines(list):
    text = ""
    for e in list:
        text += str(e) + "\n"
    return text
            
def aFuture(states):
    for state in states:
        if not (state.isErrorState() or state.isDoneState()):
            return True
    return False

def typeOf(v):
    if Options.showtypes:
        if isinstance(v,str):
            return " - str"
        elif isinstance(v,unicode):
            return " - unicode"
        elif isinstance(v,int):
            return " - int"
        elif isinstance(v,long):
            return " - long"
        elif isinstance(v,list):
            return " - list"
    return ""

def eventString(event,counter=""):
    if counter == "":
        eventnr = " "
    else:
        eventnr = " " + str(counter) + " "
    text = event["OBJ_TYPE"] + eventnr + "{\n"
    for field,val in event.iteritems():
        text += "  " + str(field) + " := " + ast.stringOf(val) + typeOf(val) + "\n"
    text += "}\n"
    return text

def isInt(s):
    '''
    Tests whether a string contains an integer.
    For example:
    - isInt("2") == True
    - isInt("two") == False
    '''
    try:
        int(s)
        return True
    except:
        return False


### bit and index operations ###

def getBitValue(n, p):
    '''
    get the bitvalue of denary (base 10) number n at the equivalent binary
    position p (binary count starts at position 0 from the right)
    '''
    return (int(n) >> int(p)) & 1

def indexMatches(source,index,range,bindings):
    if isinstance(source,int) or isinstance(source,long):
        if index <= 15: 
            return range.matches(getBitValue(source,index),bindings)
    elif (isinstance(source,str) or isinstance(source,unicode)) and isInt(source):
        sourceint = int(source)
        if index <= 15: 
            return range.matches(getBitValue(sourceint,index),bindings)        
    elif isinstance(source,list) or isinstance(source,str) or isinstance(source,unicode):
        if index < len(source):
            return range.matches(source[index],bindings)
    elif isinstance(source,dict):
        if index in source:
            return range.matches(source[index],bindings)
    # did not match
    return None


### exceptions and errors ###

class Bug(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Error:
    def __init__(self,location,message):
        self.location = location
        self.message = message

    def getLocation(self):
        return self.location

    def getMessage(self):
        return "*** violated: " + self.message
        
    def __repr__(self):
        return "\n*** " + str(self.location) + " violated: " + self.message

class SafetyError(Error):
    def __init__(self,location,message,state=None,eventnr=None,event=None,transitionnr=None):
        Error.__init__(self, location, message)
        self.state = state
        self.eventnr = eventnr
        self.event = event
        self.transitionnr = transitionnr

    def getState(self):
        return self.state
    
    def getEventNr(self):
        return self.eventnr
    
    def getEvent(self):
        return self.event
    
    def getTransitionNr(self):
        return self.transitionnr

class LivenessError(Error):
    def __init__(self,location,message,state=None):
        Error.__init__(self, location, message)
        self.state = state

    def getState(self):
        return self.state

def error(message):
    print "***" , message
    os._exit(1)


### filtering ###

class Filter:
    def __init__(self):
        self.filter = {} # OBJ_TYPE -> (Key-set)-list
        
    def update(self,kind,conditionkeys):
        if not kind in self.filter:
            self.filter[kind] = []
        keysetlist = self.filter[kind]
        conditionkeyset = set(conditionkeys)
        for keyset in keysetlist:
            if keyset == conditionkeyset:
                return
        keysetlist.append(conditionkeyset)
    
    def relevant(self,event):
        kind = eventKind(event)
        if not kind in self.filter:
            return False
        else:
            eventkeys = set(event.keys())
            for keyset in self.filter[kind]:
                if keyset.issubset(eventkeys):
                    return True
            return False


### statistics ###

class Statistics:
    def __init__(self,dostatistics):
        self.dostatistics = dostatistics
        self.counts = {} # OBJ_TYPE -> ((Field -> Value) * int)-list
              
    def getCounts(self):
        return self.counts
              
    def __record__(self,kind,dictionary):
        if not kind in self.counts:
            self.counts[kind] = []
        counts = self.counts[kind]
        for index in range(0,len(counts)):
            (dict,count) = counts[index]
            if dict == dictionary:
                counts[index] = (dict,count+1)
                return
        counts.append((dictionary,1)) 

    def execute(self,condition,event,binding,newbinding):
        if self.dostatistics:
            debug("=========================")
            debug(str(condition) +"\n"  + eventString(event) + "\n" + str(binding) + str(newbinding))
            debug("=========================")
            kind = condition.getKind()
            constraints = condition.getConstraints()
            dictionary = dict([(key,event[key]) for key in constraints])
            self.__record__(kind,dictionary)

    def __repr__(self):
        text = "Statistics {\n"
        for eventkind in sorted(self.counts.keys()):
            pairlist = self.counts[eventkind]
            text += "  " + str(eventkind) + " :\n"
            for (dict,count) in pairlist:
                text += "      " + str(dict) + " -> " + str(count) + "\n"
        text += "}\n"
        return text 


### states ###

class StateMode:
    STEP = 1
    STATE = 2
    ALWAYS = 3

class StateDecl:
    def __init__(self,name,formals=[],mode=StateMode.STATE):
        self.name = name
        if isinstance(formals,list):
            self.formals = formals
        else: # one argument
            self.formals = [formals]
        self.mode = mode
        self.rules = []

    def getFullName(self):
        return self.name

    def getName(self):
        if startswith(self.name,"error"):
            return "error"
        if startswith(self.name,"done"):
            return"done"
        return self.name

    def getFormals(self):
        return self.formals

    def addRule(self,rule):
        self.rules.append(rule)

    def addRules(self,rules):
        for rule in rules:
            self.addRule(rule)

    def getRules(self):
        return self.rules

    def getMode(self):
        return self.mode

    def isErrorState(self):
        return self.getName() == "error"

    def isDoneState(self):
        return self.getName() == "done"

    def shortRepr(self):
        text = self.getName() 
        if self.formals != []:
            text += "(" + list2string(self.formals) + ")"   
        return text

    def shortReprWithBindings(self,bindings):
        text = self.getName() 
        if self.formals != []:
            actuals = [bindings[formal.getName()] for formal in self.formals]
            text += "(" + list2string(actuals) + ")"   
        return text

    def __repr__(self):
        if self.mode == StateMode.STEP:
            mode = "  step "
        else:
            if self.mode == StateMode.STATE:
                mode = "  state "
            else:
                mode = "  always "
        text = mode + self.name 
        if self.formals != []:
            text += "(" + list2string(self.formals) + ")"   
        text += " {"
        if self.rules == []:
            text += "}"
        else:
            text += "\n"
            for rule in self.rules:
                text += "    " + str(rule) + "\n"
            text += "  }"
        return text
          
class Rule:
    def __init__(self,guard,action,operation=None):
        self.guard = guard # Condition-list
        self.action = action # Target-list
        self.operation = operation # event -> unit

    def getGuard(self):
        return self.guard
    
    def getAction(self):
        return self.action

    def executeOperation(self,event):
        if self.operation != None:
            self.operation(event)

    def updateFilter(self,filter):
        for condition in self.guard:
            condition.updateFilter(filter)

    def __repr__(self):
        text = ""
        text += list2string(self.guard)
        text += " => "
        text += list2string(self.action)
        return text   

    def reprWithBindings(self,bindings):
        text = ""
        text += list2string([condition.reprWithBindings(bindings) for condition in self.guard])
        text += " => "
        text += list2string(self.action) # we don't instantiate with bindings since it is an error transition (we should do)
        return text  
            

class Condition:
    def __init__(self,kind,constraints,predicate=None):
        self.kind = kind # string
        self.constraints = constraints # FieldName -m> VAL | IVL | BIT | PAR
        self.predicate = predicate

    def getKind(self):
        return self.kind

    def getConstraints(self):
        return self.constraints     

    def getPredicate(self):
        return self.predicate

    def thisKind(self,event):
        return eventKind(event) == self.kind

    def matches(self,event,binding,environment):
        if not self.thisKind(event):
            return None
        accumbinding = {}
        for field,constraint in self.constraints.iteritems():
            debug("checking constraint " + str(field) + " : " + str(constraint) + " in binding " + str(binding))
            if field in event:
                localbinding = constraint.matches(event[field],binding) 
            else:
                localbinding = None
            if localbinding == None:
                return None
            accumbinding.update(localbinding)
        if self.predicate != None and not self.predicate.evaluate(accumbinding,binding,environment):
            return None
        else:
            return accumbinding

    def widen(self,field,value):
        assert field in self.constraints
        constraint = self.constraints[field]
        assert isinstance(constraint,IVL)
        constraint.widen(value)

    def updateFilter(self,filter):
        filter.update(self.kind,self.constraints.keys())

    def __repr__(self):
        text = self.kind + "{"
        comma = ""
        for field,constraint in self.constraints.iteritems():
            text += comma + str(field) + " : " + str(constraint)
            comma = ","
        text += "}"
        if self.predicate != None:
            text += " where " + str(self.predicate)
        return text

    def reprWithBindings(self,bindings):
        groundedConstraints = dict([(field,range.ground(bindings)) for field,range in self.constraints.iteritems()])
        return self.kind + str(groundedConstraints)


### range constraints ###

class Range:
    pass

class VAL(Range):
    def __init__(self,value):
        self.value = value
    
    def getValue(self):
        return self.value
    
    def matches(self,value,binding):
        if value == self.value: # TEST
            return {}
        else:
            return None

    def ground(self,bindings):
        return self

    def __repr__(self): 
        if isinstance(self.value,str) or isinstance(self.value,unicode):
            return "\"" + str(self.value) + "\""
        else:
            return str(self.value)

class IVL(Range):
    def __init__(self,low,high):
        self.low = low
        self.high = high
        
    def matches(self,value,binding):
        if self.low <= value <= self.high:
            return {}
        else:
            return None
    
    def widen(self,value):
        self.low = min(self.low,value)
        self.high  = max(self.high,value)

    def ground(self,bindings):
        return self

    def __repr__(self):
        return "[" + str(self.low) + "," + str(self.high) + "]"

class BIT(Range):
    def __init__(self,dict):
        self.dict = dict # fieldName -> Range
 
    def matches(self,value,bindings):
        resultingbindings = {}
        for index,range in self.dict.iteritems(): 
            newbindings = indexMatches(value,index,range,bindings)
            if newbindings == None:
                return None
            else:
                resultingbindings.update(newbindings)
        # success: it matches all index constraints
        # resultingbindings may be empty ({}) though
        return resultingbindings 

    def ground(self,bindings):
        return dict([(field,range.ground(bindings)) for field,range in self.dict.iteritems()])

    def __repr__(self):
        text = "{"
        comma = ""
        for index in sorted(self.dict.keys()):
            range = self.dict[index]
            assert isinstance(range,Range)
            text += comma + str(index) + ":" + ast.stringOf(range)
            comma = ","
        text += "}"
        return text

class PAR(Range):
    def __init__(self,name):
        self.name = name

    def getName(self):
        return self.name

    def matches(self,value,bindings):
        debug("matching " + str(value) + " against name " + self.name + " with binding " + str(bindings))
        if self.name in bindings:
            if value == bindings[self.name]: # TEST
                return {} # success but no binding is generated
            else:
                return None # no match
        else:
            return {self.name : value} # match and binding is generated

    def ground(self,bindings):
        return bindings.get(self.getName(),self) 

    def __repr__(self):
        return self.name


### target ###

class Target:
    def __init__(self,statedecl,actuals=[]):
        self.statedecl = statedecl
        self.actuals = actuals

    def getStateDecl(self):
        return self.statedecl

    def instantiate(self,bindings={},history=None):
        localbindings = self.instantiateBindings(self.statedecl.getFormals(),self.actuals,bindings)      
        return State(self.statedecl,localbindings,history)

    def instantiateBindings(self,formals,actuals,bindings):
        assert len(formals) == len(actuals)
        localbindings = {}
        for index in range(0,len(formals)):
            formal = formals[index] # PAR("x") 
            actual = actuals[index]   # either a PAR("y") or a normal value
            if isinstance(actual,PAR):
                actualname = actual.getName()
                assert actualname in bindings
                localbindings[formal.getName()] = bindings[actualname]
            else:
                localbindings[formal.getName()] = actual
        return localbindings

    def __repr__(self):
        text = self.statedecl.getName()
        if self.actuals != []:
            text += "("  + list2string(self.actuals) + ")"
        return text      
        
        
### specification ###

class StateKind:
    INITIAL = 1
    NORMAL = 2
    SUCCESS = 3
    FORBIDDEN = 4
    ERROR = 5
    DONE = 6

class NameGenerator:
    def __init__(self,stem):
        self.stem = stem
        self.number = 0
                        
    def next(self):
        self.number = self.number + 1
        return self.stem + "_" + str(self.number)

class Specification:
    def __init__(self,name):
        self.name = name
        self.statedecls = []
        self.initial = []
        self.forbidden = []
        self.success = []
        self.stem = "L0" 
        self.changed = False
        self.stategenerator = NameGenerator(self.stem)
        self.errorgenetor = NameGenerator("error")
        self.donegenerator = NameGenerator("done")

    def getName(self):
        return self.name

    def setChanged(self):
        self.changed = True

    def setStem(self):
        names = [statedecl.getName() for statedecl in self.statedecls]
        count = 1
        while count <= 100000:
            stem = "L" + str(count)
            if not exists(names,lambda name : name.startswith(stem)):
                # we found a new stem
                self.stategenerator = NameGenerator(stem)
                self.stem = stem
                return
            # we did not find a new stem, try the successor
            count = count + 1
        error("searching for a new state name-stem count has gone beyond 100000, something is wrong")
        
    def addStateDecl(self,statedecl):
        self.statedecls.append(statedecl)
    
    def addInitial(self,target):
        self.initial.append(target)
    
    def getInitial(self):
        return self.initial
        
    def addForbidden(self,statedecl):
        self.forbidden.append(statedecl)
    
    def getForbidden(self):
        return self.forbidden
        
    def addSuccess(self,statedecl):
        self.success.append(statedecl)
                       
    def getSuccess(self):
        return self.success
                       
    def nextName(self):
        return self.stategenerator.next()                       
        
    def error(self):
        errorStateDecl = StateDecl(self.errorgenetor.next(),mode=StateMode.STEP)
        self.addStateDecl(errorStateDecl)
        return errorStateDecl
                       
    def done(self):
        doneStateDecl = StateDecl(self.donegenerator.next(),mode=StateMode.STEP)
        self.addStateDecl(doneStateDecl)
        return doneStateDecl
                       
    def wellformed(self):
        return True
             
    def getFilter(self):
        filter = Filter()
        for statedecl in self.statedecls:
            for rule in statedecl.getRules():
                rule.updateFilter(filter)
        return filter
  
    def __repr__(self):
        text = "\n\nautomaton " + self.name + " {\n"
        for statedecl in self.statedecls:
            if not statedecl.isErrorState() and not statedecl.isDoneState():
                text += str(statedecl) + "\n\n"
        text += "  initial "
        comma = ""
        for init in self.initial:
            text += comma + str(init)
            comma = ","
        text += "\n"
        if self.forbidden != []:
            text +=  "  hot "
            comma = ""
            for forbid in self.forbidden:
                text += comma + forbid.getName()
                comma = ","
            text += "\n"
        if self.success != []:
            text +=  "  success "
            comma = ""
            for success in self.success:
                text += comma + success.getName()
                comma = ","
            text += "\n"
        text += "}\n"
        return text

    def nodeDecl(self,statedecl):    
        kind = self.getKind(statedecl)
        mode = statedecl.getMode()
        modetxt = ""
        if mode == StateMode.ALWAYS:
            modetxt = "@ "
        if mode == StateMode.STEP:
            modetxt = "# "
        format = "label=\"" + modetxt + statedecl.shortRepr() + "\""
        if kind == StateKind.INITIAL:
            format += ",style=filled,color=lightgrey"
        if kind == StateKind.NORMAL:
            if self.changed and statedecl.getName().startswith(self.stem):
                format += ",color=red"
        if kind == StateKind.SUCCESS:
            format += ",shape=doublecircle,color=green"
        if kind == StateKind.FORBIDDEN:
            format += ",shape=invhouse,color=red"
        if kind == StateKind.ERROR:
            format += ",style=filled,color=black,fontcolor=white"
        if kind == StateKind.DONE:
            pass
        decl = "node_" + statedecl.getFullName() + "[" + format + "];"
        return decl
    
    def getKind(self,statedecl):
        if statedecl in [target.getStateDecl() for target in self.initial]:
            return StateKind.INITIAL
        if statedecl in self.success:
            return StateKind.SUCCESS
        if statedecl in self.forbidden:
            return StateKind.FORBIDDEN
        if statedecl.isErrorState():
            return StateKind.ERROR
        if statedecl.isDoneState():
            return StateKind.DONE
        return StateKind.NORMAL

    def dumpDot(self,filename=None):
        if filename == None:
            fileToOpen = Options.resultdir + "/" + self.name + ".dot"
        else:
            fileToOpen = filename
        dot = open(fileToOpen,'w')
        pointcount = 0
        dot.write("digraph states {\n")
        dot.write("node [shape = circle];\n")
        for statedecl in self.statedecls:
            dot.write("    " + self.nodeDecl(statedecl) + "\n")
        for statedecl in self.statedecls:
            sourcenode = "node_" + statedecl.getFullName()
            for rule in statedecl.getRules():
                guard = list2string(rule.getGuard())
                label = "[label=\"" + guard.replace("\"","\\\"") + "\"]"
                if len(rule.getAction()) > 1:
                    pointcount = pointcount + 1
                    targetnode = "node_P" + str(pointcount)
                    dot.write("    " + targetnode + "[label=\"\",shape=triangle,color=blue]\n")
                    dot.write("    " + sourcenode + " -> " + targetnode + label + ";\n")
                    sourcenode = targetnode
                    label = "[color=blue,style=dotted]" # the nodes leading out of the AND-node are unlabelled
                for target in rule.getAction():
                    targetnode = "node_" + target.getStateDecl().getFullName()
                    dot.write("    " + sourcenode + " -> " + targetnode + label + ";\n")
        dot.write("}\n");
        dot.close()

    def write(self):
        print str(self)
        self.dumpDot()

def calcNewestStem(names):
    count = 0
    for name in names:
        match = re.match("L(\d+)\\_",name)
        if match != None:
            thiscount = int(match.group(1))
            count = max(count,thiscount)
    return "L" + str(count) + "_"


### monitor ###

class History:
    def __init__(self,history,event,number):
        self.history = history
        self.event = event
        self.number = number

    def getLog(self):
        if self.event == None:
            return []
        elif self.history == None:
            return [self.event]
        else:
            return self.history.getLog() + [self.event]

    def __repr__(self):
        text = ""
        if self.history != None:
            text += str(self.history)
        if self.event != None:
            text += eventString(self.event,self.number)
        text += "\n"
        return text

def makeHistory(history,event,number):
    if Options.history:
        return History(history,event,number)
    else:
        return None

def history2string(history):
    if history == None:
        return ""
    else:
        return "--- error trace: ---\n\n" + str(history)


### monitor ###

class Results:
    def __init__(self,specname,errors,counts):
        self.specname = specname
        self.errors = errors   # Error-list
        self.counts = counts # OBJ_TYPE -> ((Field -> Value) * int)-list
    
    def getSpecName(self):
        return self.specname
    
    def getErrors(self):
        return self.errors
        
    def getCounts(self):
        return self.counts
    
    def __repr__(self):
        text = "\n"
        text += "============================\n"
        text += "       RESULTS FOR " + self.specname + ": \n"
        text += "============================\n\n"
        if self.errors == []:
            text += "No errors detected!\n"
        else:
            text += "Errors: " + str(len(self.errors)) + "\n\n"
            for error in self.errors: 
                text += error.getMessage() + "\n"
        text += "\n"
        if self.counts != {}:
            text += "Statistics {\n"
            for eventkind in sorted(self.counts.keys()):
                pairlist = self.counts[eventkind]
                text += "  " + str(eventkind) + " :\n"
                for (dict,count) in pairlist:
                    text += "      " + str(dict) + " -> " + str(count) + "\n"
            text += "}\n"
        return text

class State:
    def __init__(self,statedecl,bindings,history):
        self.statedecl = statedecl
        self.bindings = bindings
        self.history = history

    def getStateDecl(self):
        return self.statedecl

    def getBindings(self):
        return self.bindings

    def getHistory(self):
        return self.history

    def isErrorState(self):
        return self.statedecl.isErrorState()
    
    def isDoneState(self):
        return self.statedecl.isDoneState()

    def __repr__(self):
        return str(self.statedecl) + "\n  with bindings: " + str(self.bindings)
    
    def shortRepr(self):
        return self.statedecl.shortRepr() + " with bindings: " + str(self.bindings)
    
    def shortReprWithBindings(self):
        return self.statedecl.shortReprWithBindings(self.bindings)
    
class Monitor:
    def __init__(self,specification,learning=False,dostatistics=Options.statistics,environment={}):
        if isinstance(specification,Specification):
            self.specification = specification
        else:
            self.specification = specification.getSpec()
        assert self.specification.wellformed()
        self.observations = []
        self.states = specification.initial
        self.learning = learning
        self.error = False
        self.errors = []
        if Options.filter and not self.learning:
            self.filter = self.specification.getFilter()
        else:
            self.filter = None
        self.dostatistics = dostatistics
        self.statistics = Statistics(dostatistics)
        self.environment = environment
        self.eventnumber = 0
        self.specification.write()
       
    def addObservation(self,obs):
        self.observations.append(obs)

    def getEvent(self):
        return self.observations[0] # assuming there is exactly one

    def addState(self,state):
        self.states.append(state)

    def getStates(self):
        return self.states

    def getResults(self,includeStatistics=True): 
        if includeStatistics:
            statCounts = self.statistics.getCounts()
        else:
            statCounts = {}
        return Results(self.specification.getName(),self.errors,statCounts)

    def trueCondition(self,condition,binding):
        for observation in self.observations:
            debug("examining observation: " + strEvent(observation))
            newbinding = condition.matches(observation,binding,self.environment)
            if newbinding != None:
                self.statistics.execute(condition, observation, binding, newbinding)
                return newbinding
        return None
        
    def trueGuard(self,guard,binding):  
        accumbinding = {}
        for condition in guard:
            debug("testing condition " + str(condition))
            localbinding = self.trueCondition(condition,binding)
            if localbinding == None:
                debug("condition is false")
                return None
            debug("generating binding: " + str(localbinding))
            accumbinding.update(localbinding)
            debug("condition is true")
        return accumbinding

    def apply(self):
        errors = []
        states = []
        moveon = True
        for state in self.states:
            debug("checking state : " + state.shortRepr())
            statedecl = state.getStateDecl()
            fired = False
            if moveon:
                ruleNumber = 0
                for rule in statedecl.getRules():
                    ruleNumber = ruleNumber + 1
                    debug("testing rule: " + str(rule))
                    localbindings = self.trueGuard(rule.getGuard(),state.getBindings()) 
                    if localbindings != None:
                        debug("guard satisfied, adding actions") 
                        bindings = state.getBindings().copy()
                        bindings.update(localbindings)
                        history = makeHistory(state.getHistory(), self.getEvent(),self.eventnumber)
                        newstates = [target.instantiate(bindings,history) for target in rule.getAction()]
                        states += newstates
                        fired = True
                        moveon = not Options.once
                        rule.executeOperation(self.getEvent()) # will execute if provided
                        if containsError(newstates):
                            location = self.specification.getName()
                            event = eventString(self.getEvent(),self.eventnumber)
                            historytext = history2string(history)
                            message = \
                                 "by event " + str(self.eventnumber) + " in state:\n\n" + \
                                 str(state) + "\n\nby transition " + str(ruleNumber) + " : " + rule.reprWithBindings(bindings) + "\n\n" + \
                                 "violating event:\n\n" + event + "\n" + historytext
                            error = SafetyError(location,message,state,self.eventnumber,self.getEvent(),ruleNumber)
                            errors += [error]
                            self.errormsg(str(error))
            if statedecl.mode == StateMode.ALWAYS or ((not fired) and statedecl.mode == StateMode.STATE):
                states += [state]
        debug("---> new set of states: \n" + listonlines(states))
        if not aFuture(states) and self.specification.getSuccess() != []:
            location = self.specification.getName()
            previousstates = [state.shortReprWithBindings() for state in self.states]
            event = eventString(self.getEvent(),self.eventnumber)
            historytext = ""
            if Options.history:
                for state in self.states:
                    historytext += "reached state: " + state.shortReprWithBindings() + ".\n\n" + history2string(state.getHistory()) + "\n"
            error = LivenessError(location, "event " + str(self.eventnumber) + 
                          " terminates monitor in non-success state.\n\nviolating event:\n\n" + event + "\n" + historytext)
            errors += [error]
            self.errormsg(str(error))
        self.observations = []     
        self.states = states   
        self.error = not aFuture(self.states)
        return errors

    def begin(self):
        self.observations = []
        self.states = [target.instantiate() for target in self.specification.getInitial()]
        self.error = False
        self.errors = []
        self.eventnumber = 0
        self.statistics = Statistics(self.dostatistics)

    def next(self,event):
        self.eventnumber = self.eventnumber + 1
        if (self.learning or not Options.filter or self.filter.relevant(event)) and (not self.error or self.learning):
            debug("checking automaton: " + self.specification.getName())
            self.observations = [event]
            self.errors += self.apply()

    def end(self):
        location = self.specification.getName()
        if self.specification.forbidden != []:
            forbidden = [state for state in self.states if state.getStateDecl() in self.specification.forbidden]
            for state in forbidden:
                history = state.getHistory()
                historytext = history2string(history)
                error = LivenessError(location,"in hot end state:\n\n" + str(state) + "\n\n" + historytext,state)
                self.errors += [error]
        if self.specification.success != []:
            if not overlaps(self.specification.success,[state.getStateDecl() for state in self.states]):
                errortext = ""
                for state in self.states:
                    historytext = history2string(state.getHistory())
                    errortext += "reached state:\n\n" + str(state) + "\n\n" + historytext + "\n"
                error = LivenessError(location,"none of the success states have been reached.\n\n" + errortext)
                self.errors += [error]

    def monitor(self,log):
        print "\n===== monitoring new log: =====\n"
        self.begin()
        for event in log:
            self.next(event)
        self.end()
        return self.getResults()

    def errormsg(self,str):
        if not self.learning:
            print str


### observer ###

class Observer:
    def __init__(self,monitorThis=[]):
        '''@param monitorThis is either a string or a list of strings, each
          representing an absolute path name to a file containing
          a specification in the LogScope specificiation language.
        '''
        self.eventNr = 0
        if not isinstance(monitorThis,list):
            # it's a Specification, a specWriter, a Monitor or a file name
            requirements = [monitorThis]
        else:
            # it's a list of such
            requirements = monitorThis
        self.monitors = []
        for requirement in requirements:
            if isinstance(requirement,Monitor):
                self.monitors.append(requirement)
            elif isinstance(requirement,SpecWriter) or isinstance(requirement,Specification):
                # if it is a SpecWriter the Monitor will turn it into a Specification
                self.monitors.append(Monitor(requirement))
            else: # it must be a file name
                assert isinstance(requirement,str) or isinstance(requirement,unicode) , str(requirement)
                specs = parse(requirement)
                if specs == None:
                    error("Monitoring terminated due to syntax error in specification")
                headline("parsed specification units")    
                print str(specs)
                specWriters = internalSpec(specs)
                environment = self.computeEnvironment(specs.python)
                headline("translated specification units")    
                for specWriter in specWriters:
                    self.monitors.append(Monitor(specWriter,environment=environment))                

    def computeEnvironment(self,python):
        environment = {} 
        exec("from lsm.predicates import *") in environment # built-in predicates
        if python != None:
            exec(python) in environment # add what the user defined
        return environment

    def addMonitor(self,monitor):
        self.monitors.appened(monitor)
        
    def addSpec(self,specification):
        monitor = Monitor(specification)
        self.monitors.append(monitor)    

    def getResults(self):
        return [monitor.getResults(Options.printstatistics) for monitor in self.monitors]

    def begin(self):
        self.eventNr = 0
        for monitor in self.monitors:
            monitor.begin()

    def next(self,event):
        for monitor in self.monitors:
            monitor.next(event)

    def end(self):
        for monitor in self.monitors:
            monitor.end()

    def monitor(self,log):
        length = len(log)
        headline("monitoring new log of length " + str(length))
        time1 = time.time()
        self.begin()
        for event in log:
            self.eventNr = self.eventNr + 1
            self.next(event)
            if Options.showprogress and ((self.eventNr % Options.freqprogress) == 0):
                inform(" %7d/%7d : %3.2f"  % (self.eventNr , length , float(self.eventNr*100)/float(length)) + "%") 
        self.end()
        time2 = time.time()
        self.reportResults(length,time1,time2)
        dump_log(log)
        return self.getResults()

    def reportResults(self,length,time1,time2):
        # --- prepare for collecting summary results:
        summary = {} # AutomataName -> number of errors
        maxlength = 0 # of spec unit names, used to format summary error table
        # --- print individual results to std output:
        results = self.getResults()
        text = ""
        for result in results:
            summary[result.getSpecName()] = len(result.getErrors())
            text += str(result)
            maxlength = max(maxlength,len(result.getSpecName()))
        # ---add summary of results to std output:
        text += headlineString("Summary of Errors")
        errors = 0 
        format = "%(property)-" + str(maxlength + 1) + "s : %(number)2d %(marker)s \n" 
        for key in sorted(summary.keys()):
            value = summary[key]
            errors += value
            if value > 1:
                marker = "errors"
            elif value == 1:
                marker = "error"
            else:
                marker = ""
            text += format  % {'property': key, "number": value, "marker" : marker}
        text += "\n"
        if errors > 0:
            text += "specification was violated " + str(errors) + " times"
        else:
            text += "specification was satisfied"
        text += "\n"
        # --- collect efficiency information 
        timedelta = time2-time1
        minutes = timedelta/60
        seconds = timedelta%60
        text += "\n%-d events processed in %d minutes and %.5f seconds (%d events/sec)" % (length,minutes,seconds,length/timedelta)
        # --- print results to std output
        print text
        print "\n"
        # --- write results to file:
        fileName = Options.resultdir + "/RESULTS"
        print "Results are now being written to the file:\n" , fileName
        file = open(Options.resultdir + "/RESULTS",'w')
        file.write(text)
        file.close()
        print "\nEnd of session!"


### concrete learner ###

class ConcreteLearner:
    def __init__(self,automatonName,fileName=None):
        '''Offers a method for learning a specification from one or more log files and offers a method for
        storing the learned specification to a file.
        
        The constructor is called with one or two arguments, both of which are strings. 
        The first argument is the name of the automaton to be learned. In case only
        the first argument is provided, a new automaton will be learned from scratch. In
        case the second argument (a file name) is provided, the named automaton will be extracted
        from this file and refined during learning.
        
        @param @c automatonName : string, name of automaton to be learned
        @param @c fileName : [string], optional file name, reads automaton from file and refines it
        '''
        assert isinstance(automatonName,str) and (fileName == None or isinstance(fileName,str))
        if fileName == None:
            # a new automaton is being learned
            self.spec = Specification(automatonName) 
        else:
            # an exisiting automaton on file is being refined
            astSpec = parse(fileName)
            if astSpec == None:
                error("Learning terminated due to syntax error in specification in file: " + fileName)
            unit = astSpec.getSpecUnit(automatonName)
            if unit == None:
                error("Learning terminated due to non-existent specification unit: " + automatonName + " in file: " + fileName)
            print "\nLearner will now refine existing specification unit stored on file:"
            specWriter = internalMonitor(unit)
            self.spec = specWriter.getSpec()
            self.spec.setStem()
        self.monitor = Monitor(self.spec,learning=True,dostatistics=False)

    def getSpec(self):
        return self.spec
    
    def newStateDecl(self):
        return StateDecl(self.spec.nextName(),mode=StateMode.STEP)
    
    def begin(self):
        if self.spec.getInitial() == []:
            statedecl = self.newStateDecl()
            self.spec.addStateDecl(statedecl)
            self.spec.addInitial(Target(statedecl))
        self.monitor.begin()
             
    def next(self,event):
        debug("next event: " + strEvent(event))
        pre_states = self.monitor.getStates()
        self.monitor.next(event)
        post_states = self.monitor.getStates()
        if post_states == []:
            debug("no new states ... now learning")
            inform("learning: " + eventKind(event))
            condition = self.createCondition(event)
            targetstatedecl = self.newStateDecl()
            target = Target(targetstatedecl)
            for sourcestate in pre_states:
                sourcestatedecl = sourcestate.getStateDecl()
                rule = Rule([condition],[target])
                sourcestatedecl.addRule(rule)
                debug("adding rule " + sourcestatedecl.getName() + " :" + str(rule))
            self.monitor.addState(target.instantiate())
            self.spec.addStateDecl(targetstatedecl)
            self.spec.setChanged()

    def createCondition(self,event):
        kind = eventKind(event)
        fields = LearningFields[kind]
        fieldsThatMatter = [field for field in fields if field in event]
        constraints = dict([(field,VAL(event[field])) for field in fieldsThatMatter])
        return Condition(kind,constraints)

    def end(self):
        for state in self.monitor.states:
            self.spec.addSuccess(state.getStateDecl())
         
    def learnlog(self,log):
        '''
         Learn specification from log. The learning will refine the automaton currently stored in the
         ConcreteLearner object.
         
         @param @c log : list[dict], the log to be learned from
         @result @c void
        '''
        inform("learning from new log")
        self.begin()
        for event in log:
            self.next(event)
        self.end()

    def dumpSpec(self,filename):
        '''Write the current learned specification to a file.
        
        @param @c filename : string, total pathname of file to which specification is written.
        @result @c void
        '''
        f = open(filename,'w')
        spec = self.getSpec()
        f.write(str(spec))
        f.close()
        spec.dumpDot(filename + ".dot")


### abstract learner ###

class AbstractLearner:
    pass


### MSL statistics ###

class Row:
    def __init__(self):
        self.sent = 0
        self.vc1_dispatched = 0
        self.vc1_validation_failed = 0
        self.completed = 0
        self.failed = 0
        self.vc0_dispatched = 0

    def incr_sent(self,count):
        self.sent = self.sent + count

    def incr_vc1_dispatched(self,count):
        self.vc1_dispatched = self.vc1_dispatched+ count
        
    def incr_vc1_validation_failed(self,count):
        self.vc1_validation_failed = self.vc1_validation_failed + count
        
    def incr_completed(self,count):
        self.completed = self.completed + count
        
    def incr_failed(self,count):
        self.failed = self.failed + count
        
    def incr_vc0_dispatched(self,count):
        self.vc0_dispatched = self.vc0_dispatched + count

class Spreadsheet:    
    def __init__(self,results,file):
        self.counts = results.getCounts() # OBJ_TYPE -> ((Field -> Value) * int)-list
        self.spreadsheet = {} # Command -> Row
        open(file,'w').write(self.getSpreadsheet())
        
    def __getRow__(self,command):
        if command in self.spreadsheet:
            row = self.spreadsheet[command]
        else:
            row = Row()
            self.spreadsheet[command] = row
        return row
    
    def __extractCounts__(self):
        for obj_type in self.counts:
            pairlist = self.counts[obj_type]
            for (dict,count) in pairlist:
                if obj_type == "COMMAND":
                    command = dict["Stem"]
                    self.__getRow__(command).incr_sent(count)
                if obj_type == "EVR" :
                    if "VC1Dispatch" in dict:
                        command = dict["VC1Dispatch"]
                        self.__getRow__(command).incr_vc1_dispatched(count)
                    if  "DispatchFailure" in dict:
                        command = dict["DispatchFailure"]
                        self.__getRow__(command).incr_vc1_validation_failed(count)
                    if "Success" in dict:
                        command = dict["Success"]
                        self.__getRow__(command).incr_completed(count)
                    if "Failure" in dict:
                        command = dict["Failure"]
                        self.__getRow__(command).incr_failed(count)
                    if "VC0Dispatch" in dict:
                        command = dict["VC0Dispatch" ]
                        self.__getRow__(command).incr_vc0_dispatched(count)

    
    def getSpreadsheet(self):
        self.__extractCounts__()
        text = "\nCommand, Sent, VC1Dispatch, Validation Failure, Completed, Failed, VC0Dispatch\n"
        for command in sorted(self.spreadsheet.keys()):
            row = self.spreadsheet[command]
            text += str(command) + ", " +  str(row.sent) + ", " + str(row.vc1_dispatched) + ", " + str(row.vc1_validation_failed) + "," 
            text += str(row.completed) + ", " + str(row.failed) + ", " + str(row.vc0_dispatched) + "\n"
        return text


### spec writer ###

class V:
    def __getattr__(self,name):
        par = PAR(name)
        return par

v = V()

def target(statewriter,actuals):
    return Target(statewriter.getStateDecl(),listify(actuals))

class SpecWriter:
    def __init__(self,name):
        self.spec = Specification(name)

    def __getattr__(self,name):
        assert name in ["error","done"]
        if name == "error":
            return self.spec.error() 
        else:
            return self.spec.done()

    def getSpec(self):
        return self.spec

    def addState(self,name,formals=[],mode=StateMode.STATE):
        statedecl = StateDecl(name,formals,mode)
        self.spec.addStateDecl(statedecl)
        return StateWriter(statedecl)

    def initial(self,statewriters):
        for target in [Target(statewriter.getStateDecl()) for statewriter in listify(statewriters)]:
            self.spec.addInitial(target)

    def forbidden(self,statewriters):
        for statedecl in [statewriter.getStateDecl() for statewriter in listify(statewriters)]:
            self.spec.addForbidden(statedecl)

    def success(self,statewriters):
        for statedecl in [statewriter.getStateDecl() for statewriter in listify(statewriters)]:
            self.spec.addSuccess(statedecl)      

    def write(self):
        self.spec.write()

class StateWriter:
    def __init__(self,statedecl):
        self.statedecl = statedecl
    
    def getStateDecl(self):
        return self.statedecl
    
    def rule(self,conditions,action,operation=None):
        self.statedecl.addRule(Rule(purifyConditions(conditions),purifyAction(action),operation))
        
def listify(x):
    if isinstance(x,list):
        return x
    else:
        return [x]

def purifyConditions(conditions):
    return listify(conditions)

def purifyAction(action):
    pureaction = []
    for x in listify(action):
        if isinstance(x,StateWriter):
            target = Target(x.getStateDecl())
        else:
            if isinstance(x,StateDecl):
                target = Target(x)
            else:
                if isinstance(x,Target):
                    target = x
                else:
                    assert False
        pureaction.append(target)
    return pureaction


ALWAYS = StateMode.ALWAYS
STATE = StateMode.STATE
STEP = StateMode.STEP

 
### reading on log files ###

def dump_log(log):
    if Options.dumplog:
        filename = Options.resultdir + "/LOG"
        out = open(filename,'w')
        counter = 0
        for event in log:
            counter = counter + 1
            out.write(eventString(event,counter))
            out.write("\n")
        out.close()

def unpickle_logfile(filename,printit=False):
    file = open(filename)
    pic = pickle.Unpickler(file)
    events = pic.load()
    out = open(filename + ".formatted",'w')
    counter = 0
    for event in events.event_list:
        counter = counter + 1
        evtxt = eventString(event,counter)
        if printit:
            print evtxt
        out.write(evtxt)
    out.close()
    return events.event_list    

def parse(file):
    data = open(file).read()
    spec = yacc.parse(data)
    return spec

### internalizing parsed specification ###

statewritermap = {}

def internalSpec(astSpec):
    monitors = []
    for astMonitor in astSpec.monitors:
        monitors.append(internalMonitor(astMonitor))
    return monitors

def internalMonitor(astMonitor):
    if isinstance(astMonitor,ast.Automaton):
        return internalAutomaton(astMonitor)
    else:
        return internalPattern(astMonitor)

def modeof(astMode):
    if astMode == "always":
        return ALWAYS
    elif astMode == "state":
        return STATE
    else:
        return STEP

def mkRange(astRange):
    if isinstance(astRange,int) or isinstance(astRange,str):
        return VAL(astRange)
    elif isinstance(astRange,ast.Interval):
        return IVL(astRange.left,astRange.right)
    elif isinstance(astRange,ast.BitValues):
        newdict = dict([(field,mkRange(range)) for field,range in astRange.dict.iteritems()])
        return BIT(newdict)
    elif isinstance(astRange,ast.Name):
        return PAR(astRange.name)
    assert False

def mkConstraints(astConstraints):
    constraints = {}
    for astConstraint in astConstraints:
        constraints[astConstraint.name] = mkRange(astConstraint.range)
    return constraints

def mkCondition(astCondition):
    return Condition(astCondition.type,mkConstraints(astCondition.constraints),astCondition.predicate)

def mkActuals(astActuals):
    actuals = []
    for astActual in astActuals:
        if isinstance(astActual,int) or isinstance(astActual,str):
            actuals.append(astActual)
        elif isinstance(astActual,ast.Name):
            actuals.append(PAR(astActual.name))
        else:
            assert False
    return actuals

def mkAction(specwriter,astAction):
    global statewritermap
    if astAction.name == "done":
        target = specwriter.done
    elif astAction.name == "error":
        target = specwriter.error
    else:
        target = statewritermap[astAction.name].getStateDecl()
    return Target(target,mkActuals(astAction.actuals))

def guardOf(astRule):
    return  [mkCondition(astCondition) for astCondition in astRule.conditions]

def actionOf(specwriter,astRule):
    return  [mkAction(specwriter,astAction) for astAction in astRule.actions]

def initialStates(astAutomaton):
    initial = [astAction.name for astAction in astAutomaton.initial]
    for astState in astAutomaton.states:
        if "initial" in astState.modifiers:
            initial.append(astState.name)
    if initial == []:
        assert astAutomaton.states != []
        initial = [astAutomaton.states[0].name]
    return initial

def hotStates(astAutomaton):
    hot = []
    for astState in astAutomaton.states:
        if "hot" in astState.modifiers:
            hot.append(astState.name)
    return hot

def internalAutomaton(astAutomaton):
    global statewritermap
    statewritermap = {} # initialized for each new automaton
    specwriter = SpecWriter(astAutomaton.name)
    for astState in astAutomaton.states:
        stateWriter = specwriter.addState(astState.name, [PAR(formal) for formal in astState.formals], modeof(astState.mode))
        statewritermap[astState.name] = stateWriter
    specwriter.initial([statewritermap[name] for name in initialStates(astAutomaton)])
    specwriter.forbidden([statewritermap[astName] for astName in (astAutomaton.forbidden + hotStates(astAutomaton))])
    specwriter.success([statewritermap[astName] for astName in astAutomaton.success])
    for astState in astAutomaton.states:
        statewriter = statewritermap[astState.name]
        for astRule in astState.rules:
            statewriter.rule(guardOf(astRule),actionOf(specwriter,astRule))
    return specwriter
            
def internalPattern(astPattern):
    astAutomaton = pattern2automaton(astPattern)
    return internalAutomaton(astAutomaton)


### translating patterns into automata ###

__statecounter__ = 0

def resetStateNames():
    global __statecounter__
    __statecounter__ = 0

def nextStateName():
    global __statecounter__
    __statecounter__ = __statecounter__ + 1
    return "S" + str(__statecounter__)

def extractVariablesFromEvent(event):
    variables = []
    for constraint in event.constraints:
        variables += extractVariablesFromRange(constraint.range)
    return variables

def extractVariablesFromRange(range):
    variables = []
    if isinstance(range,ast.Name):
        variables.append(range.name)
    elif isinstance(range,ast.BitValues):
        for subrange in range.dict.values():
            variables += extractVariablesFromRange(subrange)
    else:
        pass
    return variables

def augmentVariables(oldVariables,event): 
    newVariables = extractVariablesFromEvent(event)
    return oldVariables + [variable for variable in newVariables if not (variable in oldVariables)]

def namesOf(variables): 
    return [ast.Name(variable) for variable in variables]

def pattern2automaton(astPattern):
    resetStateNames()
    automaton = ast.Automaton(name=astPattern.name,states=[],initial=[],forbidden=[],success=[])
    variables = extractVariablesFromEvent(astPattern.event)
    stateName1 = nextStateName()
    stateName2 = nextStateName()
    state1 = ast.State(modifiers=[],mode="always", name=stateName1, formals=[], rules=[])
    state2 = ast.State(modifiers=[],mode="state", name=stateName2, formals=variables, rules=[])
    automaton.states.append(state1)
    automaton.states.append(state2)
    automaton.initial.append(ast.Action(stateName1)) 
    rule = mkRule(astPattern.event,stateName2,namesOf(variables))
    state1.rules.append(rule)
    consequence2automaton(automaton,astPattern.consequence,variables,rule.actions,state2)
    return automaton

def mkRule(event,stateName,names):
    return ast.Rule([event],[ast.Action(stateName,names)])
 
def consequence2automaton(automaton,astConsequence,variables,actions,state):
    if isinstance(astConsequence,ast.Event):
        newStateName = nextStateName()
        newVariables = augmentVariables(variables,astConsequence)
        newState = ast.State(modifiers=[],mode="state", name=newStateName, formals=newVariables, rules=[])
        automaton.states.append(newState)
        rule = mkRule(astConsequence,newStateName,namesOf(newVariables))
        state.rules.append(rule)
        automaton.forbidden.append(state.name)
        return (rule.actions,newState,newVariables)
    elif isinstance(astConsequence,ast.NegatedEvent):
        state.rules.append(mkRule(astConsequence.event,"error",[]))
        return (actions,state,variables)
    elif isinstance(astConsequence,ast.ConsequenceSequence):
        for consequence in astConsequence.consequencelist:
            (newActions,newState,newVariables) = consequence2automaton(automaton,consequence,variables,actions,state)
            actions = newActions
            state = newState
            variables = newVariables
        return (actions,state,variables)
    else:
        firstTime = True
        for consequence in astConsequence.consequencelist:
            if firstTime:
                (newActions,newState,newVariables) = consequence2automaton(automaton,consequence,variables,actions,state)
                firstTime = False
            else:
                newStateName = nextStateName()
                newState = ast.State(modifiers=[],mode="state", name=newStateName, formals=variables, rules=[])
                actions.append(ast.Action(newStateName,namesOf(variables)))
                automaton.states.append(newState)
                (newActions,newState,newVariables) = consequence2automaton(automaton,consequence,variables,actions,newState)
        return (newActions,newState,newVariables)
        



    
    
