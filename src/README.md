
# LogScope

This directory contains the LogScope log analysis tool.

## Introduction

LogScope is a Python program for analyzing logs by checking them against specifications consisting of temporal logic patterns or extended automata. The specification language is flexible, powerful and easy to use.

Logs can for example be generated from a running software system. LogScope assumes that logs are on a special form: Python sequences of events, where an event is a Python dictionary, mapping field names to values (a record, or a struct using C terminology). It should be easy to convert any log file format to this format by writing a log converter (in Python for example). 

See the examples and the manual for further details.

## Contents

- `README.md` : this file
- `logscope-manual.pdf` : user manual
- `example1` : small example from github website
- `example2` : large example from user manual
- `lsm` : LogScope source code
- `ply` : parser generator used to develop LogScope

## Running LogScope

The two example diretories (`examples/example1` and `examples/example2`) each contains a python script `script.py` and a specification `spec` that the script reads. The Python script creates a log file, reads in the spec, and checks the
log file against the spec.

To run an example, for example example 1, do the following:

```bash
$ cd examples/example1
$ python script.py
```

The results will be stored in the `results` directory local to each example, as well as being printed on std out.

See manual for further details.

