import argparse
import re
import json
from dataclasses import dataclass

@dataclass(unsafe_hash=True)
class TimesheetReport:
    timeframe: str
    work_from_home: float
    work_from_office: float
    target_work_from_home_quota: float

    def total_hours_worked(self) -> float:
        return self.work_from_home + self.work_from_office
    
    def actual_work_from_home_quota(self) -> float:
        if (self.work_from_home != 0):
            return self.work_from_home / self.total_hours_worked() * 100
        else:
            return 100
        
class TimesheetProcessor:
    # Define regex lists as class attributes
    regex_timeframe = re.compile(r'(\d{2}.\d{2}.\d{4}) bis (\d{2}.\d{2}.\d{4})')

    regex_wfh = [
        r'ganz.+Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)', # full day working from home
        r'anteilige Mobilarbeit:\s+(?P<actualWorkTime>[\d.,]+)', # partial day working from home
        r'Wochenerfassung Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)', # weekly working from home time not covered by the other checks
    ]

    regex_wfo = [
        r'(?P<dayOfMonth>\d{2}) (?P<dayOfWeek>\w{2}).*(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5}).*(?P<overTime>[\d.,]{4,5})', # work from office
        r'Weiterbildung\s+(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5})', # training
    ]

    def __init__(self, input_file):
        # Compile the regex patterns
        self.compiled_regex_wfh = [re.compile(pattern) for pattern in self.regex_wfh]
        self.compiled_regex_wfo = [re.compile(pattern) for pattern in self.regex_wfo]

        self.input_file = input_file
        self.report = self._load_data()

    def _load_data(self) -> TimesheetReport:
        # Logic to load data from input_file
        data = TimesheetReport()
        with open(self.input_file, 'r') as file:
            for line in file:
                if (match := self.regex_timeframe.search(line)):
                    data.timeframe = match.groups()[0] + "-" + match.groups()[1]
                else:
                    matched = False
                    for regex in self.compiled_regex_wfh:
                        if (match := regex.search(line)):
                            data.work_from_home += self._get_hours_worked(match)
                            matched = True
                            break
                        
                    if not matched:
                        for regex in self.compiled_regex_wfo:
                            if (match := regex.search(line)):
                                data.work_from_office += self._get_hours_worked(match)
                                break
        return data

    def _get_hours_worked(match):
        return float(match.group('actualWorkTime').replace(',', '.'))

    def output_as_text(self):
        print(self.report.timeframe, ":")
        print("Work from Home:", "{:.2f}".format(self.report.actual_work_from_home_quota()) + "%")
        print("Hours Home:\t", "{:.2f}".format(self.report.work_from_home))
        print("Hours Office:\t", "{:.2f}".format(self.report.work_from_office))
        print("Hours total:\t", "{:.2f}".format(self.report.total_hours_worked()))
        print("-----")

    def output_as_csv(self):
        print("TODO: csv")

    def output_as_json(self):
        print("TODO: json")


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process timesheet data and calculate the work from home quota")
    parser.add_argument('input_file', help='Path to the input file')
    parser.add_argument('target_quota', help='Target work from home quota. default=70 (%)')
    parser.add_argument('output_format', choices=['text', 'csv', 'json'], help='Desired output format')
    return parser.parse_args()

def main():
    args = parse_arguments()

    processor = TimesheetProcessor(args.input_file)
    processor.transform_data()

    if args.output_format == 'text':
        processor.output_as_text()
    elif args.output_format == 'csv':
        processor.output_as_csv()
    elif args.output_format == 'json':
        processor.output_as_json()

if __name__ == '__main__':
    main()
