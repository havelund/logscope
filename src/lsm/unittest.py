
from lsm import *

### event generating functions: ###

def COMMAND(dict):
    '''Creates a COMMAND event'''
    dict["OBJ_TYPE"] = "COMMAND"
    return dict

def EVR(dict):
    '''Creates an EVR event'''
    dict["OBJ_TYPE"] = "EVR"
    return dict

def CHANNEL(dict):
    '''Creates a CHANNEL event'''
    dict["OBJ_TYPE"] = "CHANNEL"
    return dict

def CHANGE(dict):
    '''Creates a CHANGE event'''
    dict["OBJ_TYPE"] = "CHANGE"
    return dict

def PRODUCT(dict):
    '''Creates a PRODUCT event'''
    dict["OBJ_TYPE"] = "PRODUCT"
    return dict


### error count checking functions: ###

def checkErrorCount_(results,count):
    '''Counts the total number of errors in all results for all properties'''
    counter = 0
    for result in results:
        counter += len(result.getErrors())
    assert counter == count

def checkErrorCounts_(results,resultmap):
    '''Checks that the error count for each property is the expected one.
    
    @param @c results : list[Results], list of verification results to check
    @param @c resulmap : map[string,int], expected error counts for each property
    @result @c void
    '''
    map = resultmap.copy()
    for result in results:
        specname = result.getSpecName()
        errors = result.getErrors()
        assert specname in map and map[specname] == len(errors) , specname
        del map[specname]
    assert map == {}

def checkErrorKindCounts_(results,resultmap,checktotal=True):
    ''' 
    Checks that verification results match expected error counts.
    The expected results is provided as a dictionary mapping property names to
    pairs (safetycount,livenesscount).  

    @param @c results : list[Results], list of verification results to check
    @param @c resultmap : map[string,int*int], expected safety and liveness counts
    @param @c checktotal : bool, True of numbers in resultmap should match total
    @result @c void
    '''    
    actualTotal = 0
    expectedTotal = 0
    for result in results:
        name = result.getSpecName()
        numberOfErrors = len(result.getErrors())
        actualTotal += numberOfErrors
        if name in resultmap:
            actualSafetyCount = len([error for error in result.getErrors() if isinstance(error,SafetyError)])
            actualLivenessCount = len([error for error in result.getErrors() if isinstance(error,LivenessError)])
            assert numberOfErrors == (actualSafetyCount + actualLivenessCount)
            (expectedSafetyCount,expectedLivenessCount) = resultmap[name]
            expectedTotal += expectedSafetyCount + expectedLivenessCount
            assert expectedSafetyCount == actualSafetyCount and expectedLivenessCount == actualLivenessCount
    if checktotal:
        assert expectedTotal == actualTotal


### main error spec checking function ###

def checkErrors_(results,errorSpecs):
    '''Checks monitoring results against specification. The specification consists of a dictionary
    for each result (for a monitor), mapping names of specific characteristics to their expected
    values. 
    
    @param @c results : list[Results], list of verification results to check
    @param @c errorSpecs : list[map[string,value]], list of specs, one for each @c Results object
    @return @c void
    '''
    errorSpecs = rewriteErrorSpecs_(errorSpecs)
    wfErrorSpecs_(errorSpecs)
    errors = []
    for result in results:
        errors += result.getErrors()
    assert len(errors) == len(errorSpecs) , "errors detected: " + str(len(errors)) + ", errors expected: " + str(len(errorSpecs))
    for index in range(len(errors)):
        error = errors[index]
        errorSpec = errorSpecs[index]
        checkError_(error,errorSpec)

def rewriteErrorSpecs_(errorSpecs):
    return [rewriteErrorSpec_(spec) for spec in errorSpecs]

def rewriteErrorSpec_(errorSpec):            
    return dict([(rewriteErrorKey_(key),value) for key,value in errorSpec.iteritems()])        

def rewriteErrorKey_(key):
    map = {
                "K" : "kind", 
                "P" : "property", 
                "M" :"message", 
                "S" : "state", 
                "B" : "bindings",
                "H" : "history",
                "N" : "eventnr", 
                "E" : "event", 
                "T" : "transitionnr"
           }
    return map.get(key,key)

def wfErrorSpecs_(errorSpecs):
    assert isinstance(errorSpecs,list)
    for errorSpec in errorSpecs:
        wfErrorSpec_(errorSpec)

def wfErrorSpec_(errorSpec):
    assert isinstance(errorSpec,dict)
    assert "kind" in errorSpec and errorSpec["kind"] in ["safety","liveness"]
    specfields = {
            "kind"       : lambda s : isinstance(s,str),
            "property" : lambda s : isinstance(s,str),
            "message" : lambda s : isinstance(s,str) or isinstance(s,list),
            "state" : lambda s : isinstance(s,str),
            "bindings" : lambda s : isinstance(s,dict),
            "historylength" : lambda s : isinstance(s,int),
            "history" : lambda s : isinstance(s,list)
          }
    if errorSpec["kind"] == "safety":
        specfields.update({
            "eventnr" : lambda s : isinstance(s,int),
            "event" : lambda s : isinstance(s,dict),
            "transitionnr" : lambda s : isinstance(s,int)
        })
    assert set(errorSpec.keys()).issubset(specfields.keys()) , str(errorSpec.keys()) + str(specfields.keys())
    for field,value in errorSpec.iteritems():
        assert specfields[field](value)             

def checkError_(error,errorSpec):
    if errorSpec["kind"] == "safety":
        checkSafetyError_(error,errorSpec)
    if errorSpec["kind"] == "liveness":
        checkLiveNessError_(error,errorSpec)
    
def checkBasics_(error,errorSpec):
    # --- assertions:
    if "property" in errorSpec:
        assert errorSpec["property"] == error.getLocation() , errorSpec["property"] + "=/="+ error.getLocation()
    if "message" in errorSpec:
        messageSpec = errorSpec["message"]
        if isinstance(messageSpec,str):
            assert error.getMessage().find(messageSpec) >= 0 , error.getMessage() + "  does not contain " + messageSpec
        else: # it is a list of messages
            previousPosition = 0
            for submessage in messageSpec:
                position = error.getMessage().find(submessage,previousPosition)
                assert position >= previousPosition , error.getMessage() + "  does not contain " + submessage
                previousPosition = position
    state = error.getState()
    if state == None:
        assert set(["state","bindings","history","historylength"]).intersection(errorSpec.keys()) == set([]) , str(errorSpec)
    else:
        if "state" in errorSpec:
            assert errorSpec["state"] == state.getStateDecl().getName() , errorSpec["state"] + " =/= " + state.getStateDecl().getName()
        if "bindings" in errorSpec:
            bindings = state.getBindings()
            for field,value in errorSpec["bindings"].iteritems():
                assert field in bindings and bindings[field] == value , field + " not in " + str(bindings) +" or =/=" + str(value)
        historychain = state.getHistory()
        if historychain == None:
            history = []
        else:
            history = historychain.getLog()
        if "historylength" in errorSpec:
            assert errorSpec["historylength"] == len(history)
        if "history" in errorSpec:
            historySpec = errorSpec["history"]
            assert len(historySpec) == len(history) , str(historySpec) + "\n=/=\n" + str(history)
            for index in range(len(historySpec)):
                eventSpec = historySpec[index] 
                event = history[index]
                for field,value in eventSpec.iteritems():
                    assert field in event
                    assert eventSpec[field] == event[field]

def checkSafetyError_(error,errorSpec):
    checkBasics_(error,errorSpec)
    if "eventnr" in errorSpec:
        assert errorSpec["eventnr"] == error.getEventNr()
    if "event" in errorSpec:
        event = error.getEvent()
        for field,value in errorSpec["event"].iteritems():
            assert field in event and event[field] == value , str(field) + " not mapped to " + str(value)
    if "transitionnr" in errorSpec:
        assert errorSpec["transitionnr"] == error.getTransitionNr()
    
def checkLiveNessError_(error,errorSpec):
    checkBasics_(error,errorSpec)

