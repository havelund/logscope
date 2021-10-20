class EventList(object):
    '''Simply holds the event list for export.'''

    def __init__(self, event_list):
        self.event_list = event_list

    def pretty_print_event(self, event):
        print (event["OBJ_TYPE"] + ": {")
        for field,val in event.iteritems():
            print ("  " + str(field) + " := " + str(val))
        print "}"