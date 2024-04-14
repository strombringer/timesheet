#!/bin/python

import re
import fileinput

# regular expressions
regex_timeframe = re.compile(r'(\d{2}.\d{2}.\d{4}) bis (\d{2}.\d{2}.\d{4})')
regexWfH = re.compile(r'ganz.+Mobilarbeit\s+([\d.,]+)')
regexWfHpartial = re.compile(r'anteilige Mobilarbeit:\s+([\d.,]+)')
regexWfO = re.compile(r'\d{2} \w{2}\s+\d{2}:\d{2}\s+\d{2}:\d{2}\s+[\d.,]+\s+([\d.,]+)')

def get_hours_worked(groups):
    return float(groups[0].replace(',', '.'))

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
        resultWfH += get_hours_worked(match.groups())
    elif (match := regexWfO.search(line)):
        resultWfO += get_hours_worked(match.groups())
    elif (match := regexWfHpartial.search(line)):
        resultWfH += get_hours_worked(match.groups())
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
