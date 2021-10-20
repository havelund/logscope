
import lsm.lsm as lsm

# create an event log, in this case hand-made, but can also be extracted with log file extractor:

log = [
          {"OBJ_TYPE" : "COMMAND", "Type" : "FlightSoftWare", "Name" : "PICT", "Time" : 1900},
          {"OBJ_TYPE" : "EVR", "Name" : "PICT", "Status" : "dispatch"},
          {"OBJ_TYPE" : "EVR", "Name" : "PICT", "Status" : "success", "Time" : 2950}        
       ]


# specify path of where results should be stored (.dot files and RESULT file):

lsm.setResultDir("results")   


# instantiate the Observer class providing a path name of specification file:

observer = lsm.Observer("spec")


# call the observer's monitor function on the log:

observer.monitor(log)

