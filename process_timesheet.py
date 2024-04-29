#!/bin/python

import re
import fileinput

# regular expressions
regex_timeframe = re.compile(r'(\d{2}.\d{2}.\d{4}) bis (\d{2}.\d{2}.\d{4})')
regexWfH = re.compile(r'ganz.+Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)')
regexWfHpartial = re.compile(r'anteilige Mobilarbeit:\s+(?P<actualWorkTime>[\d.,]+)')
regexWfO = re.compile(r'(?P<dayOfMonth>\d{2}) (?P<dayOfWeek>\w{2}).*(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5}).*(?P<overTime>[\d.,]{4,5})')

def get_hours_worked(match):
    return float(match.group('actualWorkTime').replace(',', '.'))

# variables to store the results
timeframe = ""
resultWfH = 0
resultWfO = 0

# Process each line from input, whether from stdin or files
for line in fileinput.input():
    line = line.strip()
    if (match := regex_timeframe.search(line)):
        timeframe = match.groups()[0] + "-" + match.groups()[1]
    elif (match := regexWfH.search(line)):
        resultWfH += get_hours_worked(match)
    elif (match := regexWfO.search(line)):
        resultWfO += get_hours_worked(match)
    elif (match := regexWfHpartial.search(line)):
        resultWfH += get_hours_worked(match)
    # else:
    #     print("No match found for line:", line)

# Print out the results
# print("Result of WfH:", resultWfH)
# print("Result of WfO:", resultWfO)

# Calculate the percentage relation between WfH and WfO
if resultWfO != 0:
    percent_of_work_from_home =  resultWfH / (resultWfH + resultWfO) * 100
    print(timeframe, "Work from Home:", "{:.2f}".format(percent_of_work_from_home) + "%")
elif resultWfH > 0:
    print(timeframe, "Work from Home: 100%")
else:
    print("Unable to calculate percentage because neither WorkFromHome nor WorkFromOffice seem to have a value > 0")
