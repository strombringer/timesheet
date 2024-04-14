#!/bin/python

import re
import fileinput

# Define your regular expressions
regexWfH = re.compile(r'ganz.+Mobilarbeit\s+([\d.,]+)')
regexWfO = re.compile(r'\d{2} \w{2}\s+\d{2}:\d{2}\s+\d{2}:\d{2}\s+[\d.,]+\s+([\d.,]+)')
regexWfHpartial = re.compile(r'anteilige Mobilarbeit:\s+([\d.,]+)')

# Define methods to process matched groups
def process_WfH(groups):
    # print("Matched regex WfH:")
    # print("First value:", groups[0].strip())  # Ensure stripping whitespace
    return float(groups[0].replace(',', '.'))

def process_WfO(groups):
    # print("Matched regex WfO:")
    # print("First value:", groups[0].strip())  # Ensure stripping whitespace
    return float(groups[0].replace(',', '.'))

def process_WfHpartial(groups):
    # print("Matched regex WfHpartial:")
    # print("First value:", groups[0].strip())  # Ensure stripping whitespace
    return float(groups[0].replace(',', '.'))

# def getHoursWorked(groups):
#     return float(groups[0].replace(',', '.'))

# Initialize variables to store the results
resultWfH = 0
resultWfHpartial = 0
resultWfO = 0

# Process each line from input, whether from stdin or files
for line in fileinput.input():
    line = line.strip()
    # Try matching against each regex, and call corresponding method if matched
    if (match1 := regexWfH.search(line)):
        resultWfH += process_WfH(match1.groups())
    elif (match2 := regexWfO.search(line)):
        resultWfO += process_WfO(match2.groups())
    elif (match3 := regexWfHpartial.search(line)):
        resultWfHpartial += process_WfHpartial(match3.groups())
    # else:
    #     print("No match found for line:", line)

# Print out the results
# print("Result of WfH:", resultWfH)
# print("Result of WfHpartial:", resultWfHpartial)
# print("Result of WfO:", resultWfO)

# Calculate the percentage relation between WfH and WfO
if resultWfO != 0:
    percent_of_work_from_home =  (resultWfH + resultWfHpartial) / (resultWfH + resultWfHpartial + resultWfO) * 100
    print("Work from Home:", "{:.2f}".format(percent_of_work_from_home) + "%")
elif (resultWfH + resultWfHpartial) > 0:
    print("Work from Home: 100%")
else:
    print("Unable to calculate percentage because neither WorkFromHome nor WorkFromOffice seem to have a value > 0")

