

import lsm.lsm as lsm

# create an event log, in this case hand-made, but can also be extracted with log file extractor:

log = [
          {"OBJ_TYPE" : "COMMAND", "Type" : "FSW", "Stem" : "PICT", "Number" : 231},
          {"OBJ_TYPE" : "EVR", "Dispatch" : "PICT", "Number" : 231},
          {"OBJ_TYPE" : "CHANNEL", "DataNumber" : 5},
          {"OBJ_TYPE" : "EVR", "Success" : "PICT", "Number" : 231},
          {"OBJ_TYPE" : "PRODUCT", "ImageSize" : 1200}
       ]


# specify path of where results should be stored (.dot files and RESULT file):
           
lsm.setResultDir("results")   


# instantiate the Observer class providing a path name of specification file:

observer = lsm.Observer("spec")


# call the observer's monitor function on the log:

observer.monitor(log)
        
