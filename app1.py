import sys
import json
import math
import itertools
import functools
import collections.abc


def count_up(downstream):
    """ Emit integer values, starting from zero. """
    try:
        i = None
        while downstream.send(i):  
            i = 0 if i is None else i + 1
    except StopIteration:pass

def flatmap(downstream, mapper=None):
    """ Call 'mapper' with each item, emitting each result, or the item if None.
        Mapper may be a function, the string name of a builtin, or None, in which
        case it is treated as the identity function.
    """
    # Default to named Python builtin if mapper is a string.
    try:
        if isinstance(mapper, str):
            mapper = getattr(builtins, mapper)
        mapper = mapper or (lambda x: x)
        status = downstream.send(None)
        while True:
            value = yield status
            status = True
            mapped = mapper(value)
            value = value if mapped is None else mapped
            if not isinstance(value, collections.abc.Iterable):
                value = [value]
            for emittee in value:
                status &= downstream.send(emittee)
    except StopIteration:pass
        
def linear(downstream, scale, offset):
    """ Emit 'scale * x + offset' for each item 'x' in the stream. """
    mapper  = lambda x: x * scale + offset
    return flatmap(downstream, mapper=mapper)


def filter_out(downstream, above=float('inf'), below=-float('inf')):  
    """ Drop items larger than 'above' and less than 'below' from the stream. """
    mapper  = lambda x: x if above >= x >= below else None
    status = downstream.send(None)
    while True:
        value = yield status
        # print(value)
        status = True
        mapped_value = mapper(value)
        # print(mapped_value)
        if not isinstance(mapped_value, collections.abc.Iterable):
            mapped_value = [mapped_value]
        for emittee in mapped_value:
            if not emittee and (value > above):
                status = False
            else:
                status &= downstream.send(emittee)

def repeat(downstream, times):
    """ Repeat each item 'times' times. """
    mapper  = lambda v: itertools.repeat(v, times)
    return flatmap(downstream, mapper=mapper)

def take_for(count):    
    """ Consume items until 'count' items have been consumed. """
    for i in itertools.count():
        value = yield i < count        
        print(value)

def window(downstream, size):
    """ Transform items into lists containing the last 'size' items in the stream. """
    state = []
    def _window(item):
        state.append(item)
        if len(state) > size:
            state.pop(0)
        return state

    mapper  = lambda x: [_window(x)]
    return flatmap(downstream, mapper=mapper)

def take_until(*, expected=None, threshold=None):
    """ Consume items until an item equal to 'expected' is encountered. """
    status = True
    while status:
        value = yield status
        status = True
        print(value)
        if isinstance(value, list):
            if expected in value:
                status = False
            for element in value:
                if threshold and (element > threshold):
                    status = False
                if expected and (element > expected):
                    status = False
        else:
            if expected == math.sqrt(value):
                status = False
            if threshold and (math.sqrt(value) > threshold):
                status = False
            if expected and (math.sqrt(value) > expected):
                    status = False

def square(downstream):
    """ Square each item. """
    try:
        status = downstream.send(None)
        while True:
            value = yield status
            status = downstream.send(value*value)
    except StopIteration:pass

    

def run(stream):
    """ Run a stream made up of a sequence of operations to completion. """
    # count_up(linear(filter_out(repeat(take_for(count=3), times=3), below=0), offset=-3, scale=2))
    # count_up(linear(filter_out(take_for(count=10), above=0), offset=-10, scale=2))
    # count_up(linear(window(take_until(threshold=100), size=3), offset=-5, scale=2))
    # count_up(window(take_for(count=10), size=3))
    # count_up(square(take_until(expected=28)))
    
    functools.reduce(
        lambda built, step: [step[0](*built, **step[1])],
        reversed([(globals()[key], args) for key, args in stream]),
        []
    )

if __name__ == "__main__":
    received = sys.stdin.read()  ## to be executed by 'cat stream.json | py app1.py'. Comment 
    data = json.loads(received)  ## this section and uncomment below lines (only one with statement at a time) 
    run(data)                    ## if you want to run by reading from json file
    
    # with open('stream.json') as json_data:
    # with open('stream10.json') as json_data:
    # with open('stream20.json') as json_data:
    # with open('stream30.json') as json_data:
    # with open('stream40.json') as json_data:
    #    data = json.load(json_data)
    # run(data)
