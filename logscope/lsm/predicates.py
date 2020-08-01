

### built-in predicates: ###

def less(x,y):
    return x < y

def equal(x,y):
    return x == y 

def less_equal(x,y):
    return x <= y

def greater(x,y):
    return x > y

def greater_equal(x,y):
    return x >= y

def contains(s,t):
    return s.find(t) != -1

### shorter versions: ###

lt = less
eq = equal
le = less_equal
gt = greater
ge = greater_equal
