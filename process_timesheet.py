from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta

import argparse
import fileinput
import holidays
import json
import numpy as np
import re

@dataclass(unsafe_hash=True)
class TimesheetReport:
    date_format: str = ''
    timeframe: str = ''
    timeframe_start: datetime = datetime.now()
    timeframe_end: datetime = datetime.now()
    work_from_home: float = 0
    work_from_office: float = 0
    target_work_from_home_quota: float = 0
    daily_work_hours: float = 0
    remaining_working_days: int = 0
    holidays_current_month: list[str] = field(default_factory = lambda: ([]))

    def total_hours_worked(self) -> float:
        return self.work_from_home + self.work_from_office
    
    def target_work_from_home_hours(self) -> float:
        return round(self.total_hours_worked() * self.target_work_from_home_quota / 100, 2)

    def actual_work_from_home_quota(self) -> float:
        if (self.work_from_home != 0):
            return round(self.work_from_home / self.total_hours_worked() * 100, 2)
        else:
            return 100
    
    def target_work_from_home_hours_delta(self) -> float:
        """The number of hours working from home, that are more (positive number) or less (negative number) than the target quota."""
        return round(self.work_from_home - self.target_work_from_home_hours(), 2)
    
    def required_work_from_office_hours_to_match_quota(self) -> float:
        """The required number of hours working from the office, to match the set 'work from home' quota."""
        return round(self.target_work_from_home_hours_delta() * self.target_work_from_home_quota / 100, 2)

class TimesheetProcessor:
    regex_timeframe = re.compile(r'(\d{2}.\d{2}.\d{4}) bis (\d{2}.\d{2}.\d{4})')
    regex_daily_work_hours = re.compile(r'.*IRTAZ:.*([\d.,]{4,5})')

    regex_wfh = [
        r'ganz.+Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)', # full day working from home
        r'anteilige Mobilarbeit:\s+(?P<actualWorkTime>[\d.,]+)', # partial day working from home
        r'Wochenerfassung Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)', # weekly working from home time not covered by the other checks
    ]

    regex_wfo = [
        r'(?P<dayOfMonth>\d{2}) (?P<dayOfWeek>\w{2}).*(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5}).*(?P<overTime>[\d.,]{4,5})', # work from office
        r'Weiterbildung\s+(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5})', # training
    ]

    def __init__(self, input_source, quota, date_format):
        # Compile the regex patterns
        self.compiled_regex_wfh = [re.compile(pattern) for pattern in self.regex_wfh]
        self.compiled_regex_wfo = [re.compile(pattern) for pattern in self.regex_wfo]

        self.input_source = input_source
        self.report = TimesheetReport(target_work_from_home_quota=quota, date_format=date_format)
        self._load_data(self.report)

    def _load_data(self, data: TimesheetReport) -> TimesheetReport:
        # Logic to load data from input_file
        with fileinput.input(files=self.input_source if self.input_source else ('-',)) as file:
            for line in file:
                if (match := self.regex_timeframe.search(line)):
                    data.timeframe = match.groups()[0] + " - " + match.groups()[1]
                    data.timeframe_start = datetime.strptime(match.groups()[0], data.date_format)
                    data.timeframe_end = datetime.strptime(match.groups()[1], data.date_format)
                elif (match := self.regex_daily_work_hours.search(line)):
                    data.daily_work_hours = float(match.groups()[0].replace(',', '.'))
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

        self._calculate_remaining_working_days(data)
        return data

    def _get_hours_worked(self, match):
        return float(match.group('actualWorkTime').replace(',', '.'))
    
    def _calculate_remaining_working_days(self, data: TimesheetReport):        
        # Get the last day of the month
        date = data.timeframe_end
        next_month = date.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)
        
        # Create an array of all remaining days in the month
        remaining_days = np.arange(date + timedelta(days=1), last_day_of_month + timedelta(days=1), dtype='datetime64[D]')

        # Get the holidays in Bavaria for the current month
        holidays_by = holidays.country_holidays('DE', subdiv='BY', years=date.year)
        holidays_current_month = {k: v for k, v in holidays_by.items() if k.month == date.month}
        holidays_current_month_only_dates = [*holidays_current_month]

        # Filter out weekends (Saturday=5, Sunday=6) and holidays
        working_days = np.is_busday(remaining_days, holidays=holidays_current_month_only_dates)
        
        data.remaining_working_days = int(np.sum(working_days))
        data.holidays_current_month = [str(k)+ ": " + v for k, v in holidays_current_month.items()]


    def output_as_text(self):
        # terminal colors
        RED = '\033[31m'
        GREEN = '\033[32m'
        RESET = '\033[0m' # called to return to standard terminal text color

        is_above_target_quota = self.report.actual_work_from_home_quota() > self.report.target_work_from_home_quota
        color = RED if is_above_target_quota else GREEN
        print(self.report.timeframe, ":")        
        print("Work from Home:", color, "{:.2f}".format(self.report.actual_work_from_home_quota()) + " %", RESET)
        print("Hours Home:\t", "{:.2f}".format(self.report.work_from_home))
        print("Hours Office:\t", "{:.2f}".format(self.report.work_from_office))
        print("Hours total:\t", "{:.2f}".format(self.report.total_hours_worked()))
        if (is_above_target_quota):
            print()
            print("Exceeded home office hours:", "{:.2f}".format(self.report.target_work_from_home_hours_delta()))
            print("Required hours in office to match quota:", "{:.2f}".format(self.report.required_work_from_office_hours_to_match_quota()))
        
        print()
        print("Remaining working days this month:", self.report.remaining_working_days)
        print("Public holidays considered:", self.report.holidays_current_month)
        print("Target working hours per day:", self.report.daily_work_hours)
        print("-----")

    def output_as_csv(self):
        print("TODO: csv")

    def output_as_json(self):
        instance = self.report

        data = asdict(instance) # get all fields of the report object
        for name in dir(instance): # get all methods of the report object and their return values
            if callable(getattr(instance, name)) and not name.startswith("__"):
                data[name] = getattr(instance, name)()
        
        print(json.dumps(data, sort_keys=True, default=str))


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process timesheet data and calculate the work from home quota")
    parser.add_argument('input_source', nargs='?', default=None, help='Path to the input file or use stdin if not provided')
    parser.add_argument('-q', '--quota', help='Target work from home quota. default=70 (%)', type=float, default=70)
    parser.add_argument('-d', '--dateformat', help='The date format used in the timesheet. Required for parsing. default=%d.%m.%Y', type=str, default='%d.%m.%Y')
    parser.add_argument('-f', '--format', choices=['text', 'csv', 'json'], help='Desired output format. default=text', default='text')
    return parser.parse_args()

def main():
    args = parse_arguments()

    processor = TimesheetProcessor(args.input_source, args.quota, args.dateformat)

    if args.format == 'text':
        processor.output_as_text()
    elif args.format == 'csv':
        processor.output_as_csv()
    elif args.format == 'json':
        processor.output_as_json()

if __name__ == '__main__':
    main()
