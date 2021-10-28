
import time
import lsm.lsm as lsm
import csv


class CSVReader:
    """
    Class for reading CSV files: https://www.w3schools.com/python/python_iterators.asp.
    Example of use:

        csv =  CSVReader('file.csv', converter)
        for event in csv:
            ...
    """
    def __init__(self, file, converter, skip=0):
        """
        The file is the csv file to read, assumed to consist of lines,
        each comma separated.

        :param file: the csv file.
        :param converter: a function that converts one line into an event
        processed by the monitor.
        :param skip: number of lines in CSV file to skip initially (headers usually).

        line_count: the number of lines read from CSV file.
        """
        self.file = file
        self.csv_file = open(file)
        self.csv_reader = csv.reader(self.csv_file)
        self.converter = converter
        self.line_count = 0
        for x in range(skip):
            self.next()

    def __iter__(self):
        return self

    def next(self):
        self.line_count += 1
        next = self.csv_reader.next()
        return self.converter(next)

    def close(self):
        self.csv_file.close()


def converter(line):
    if line[0] == "command":
        return {'OBJ_TYPE': "COMMAND", 'cmd': line[1], 'nr': line[2], 'kind': line[3]}
    else:
        return {'OBJ_TYPE': "EVR", 'name': line[0], 'cmd': line[1], 'nr': line[2]}


"""
log-1-50000.csv
log-50-1000.csv
log-100-500.csv
log-500-100.csv

log-1-125000.csv
log-50-2500.csv
log-100-1250.csv
log-500-250.csv
"""
file = 'log-1-50000.csv'


if __name__ == '__main__':
    lsm.setResultDir("results")
    observer = lsm.Observer("spec")
    csv_reader = CSVReader(file, converter)
    begin_time = time.time()
    observer.begin()
    for event in csv_reader:
        observer.eventNr = observer.eventNr + 1
        if observer.eventNr % 1000 == 0:
            print '---> ', observer.eventNr
        observer.next(event)
    observer.end()
    csv_reader.close()
    end_time = time.time()
    observer.reportResults(observer.eventNr, begin_time, end_time)
