from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from rich.console import Console
from rich.table import Table

import argparse
import fileinput
import holidays
import json
import math
import numpy as np
import re

@dataclass(unsafe_hash=True)
class TimesheetReport:
    date_format: str = ''
    timeframe: str = ''
    timeframe_start: datetime = datetime.now()
    timeframe_end: datetime = datetime.now()

    total_hours_reported: float = 0
    """The total hours worked, as reported in the timesheet"""

    work_from_home: float = 0
    work_from_office: float = 0
    target_work_from_home_quota: float = 0
    daily_work_hours: float = 0
    weekly_work_hours: float = 0
    remaining_working_days: int = 0
    vacation_input: str = ''
    vacation_days: str = ''
    holidays_current_month: list[str] = field(default_factory = lambda: ([]))

    def work_from_office_calculated(self) -> float:
        return self.total_hours_reported - self.work_from_home

    # def total_hours_calculated(self) -> float:
    #     """The total hours worked, as calculated by the worked from home and worked from office hours"""
    #     return self.work_from_home + self.work_from_office

    def target_work_from_home_hours(self) -> float:
        return round(self.total_hours_reported * self.target_work_from_home_quota / 100, 2)

    def actual_work_from_home_quota(self) -> float:
        if (self.work_from_home != 0):
            return round(self.work_from_home / self.total_hours_reported * 100, 2)
        else:
            return 0

    def target_work_from_home_hours_delta(self) -> float:
        """The number of hours working from home, that are more (positive number) or less (negative number) than the target quota."""
        return round(self.work_from_home - self.target_work_from_home_hours(), 2)

    def required_work_from_office_hours_to_match_quota(self) -> float:
        """The required number of hours working from the office, to match the set 'work from home' quota."""
        factor = (100 - self.target_work_from_home_quota) / self.target_work_from_home_quota

        return round((factor * self.work_from_home) - self.work_from_office_calculated(), 2)

    def expected_working_hours_per_day(self) -> float:
        return self.weekly_work_hours / 5

    def maximum_work_from_home_hours_left(self) -> float:
        remainingExpectedHoursThisMonth = self.expected_working_hours_per_day() * self.remaining_working_days
        totalWorkFromHomePossibleThisMonth = (self.total_hours_reported + remainingExpectedHoursThisMonth) * self.target_work_from_home_quota / 100
        return round(totalWorkFromHomePossibleThisMonth - self.work_from_home, 2)


    def projected_required_work_from_office_hours(self) -> float:
        """The projected required number of hours working from the office, assuming set daily work hours and remaining days of the month, to match the set 'work from home' quota."""
        remainingExpectedHoursThisMonth = self.expected_working_hours_per_day() * self.remaining_working_days
        totalWorkFromOfficePossibleThisMonth = (self.total_hours_reported + remainingExpectedHoursThisMonth) * (100 - self.target_work_from_home_quota) / 100
        return round(totalWorkFromOfficePossibleThisMonth - self.work_from_office_calculated(), 2)

class TimesheetProcessor:
    regex_timeframe = re.compile(r'(\d{2}.\d{2}.\d{4}) bis (\d{2}.\d{2}.\d{4})')
    regex_daily_work_hours = re.compile(r'.*IRTAZ:\s*([\d.,]{4,5})')
    regex_weekly_work_hours = re.compile(r'.*IRWAZ:\s*([\d.,]{4,5})')
    regex_total_hours_reported = re.compile(r'Leistungsstunden\s+([\d.,]{4,7})')
    regex_reported_day = re.compile(r'^((?P<day>[0-9]{2})\s[A-Z]{2})')

    regex_wfh = [
        r'ganz.+Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)', # full day working from home
        r'anteilige Mobilarbeit:\s+(?P<actualWorkTime>[\d.,]+)', # partial day working from home
        r'Wochenerfassung Mobilarbeit\s+(?P<actualWorkTime>[\d.,]+)', # weekly working from home time not covered by the other checks
    ]

    regex_wfo = [
        r'(?P<dayOfMonth>\d{2}) (?P<dayOfWeek>\w{2})((?!Dienstr/).)*(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5}).*(?P<overTime>[\d.,]{4,5})', # work from office
        r'Weiterbildung\s+(?P<startTime>\d{2}:\d{2}).*(?P<endTime>\d{2}:\d{2}).*(?P<break>[\d.,]{4,5}).*(?P<actualWorkTime>[\d.,]{4,5}).*(?P<expectedWorkTime>[\d.,]{4,5})', # training
        r'\s+anger. Arbeitszeit\s+(?P<actualWorkTime>[\d.,]{4,5})',
    ]

    def __init__(self, input_source, quota, date_format, vacation):
        # Compile the regex patterns
        self.compiled_regex_wfh = [re.compile(pattern) for pattern in self.regex_wfh]
        self.compiled_regex_wfo = [re.compile(pattern) for pattern in self.regex_wfo]

        self.input_source = input_source
        self.report = TimesheetReport(target_work_from_home_quota=quota, date_format=date_format, vacation_input=vacation)
        self._load_data(self.report)

    def _load_data(self, data: TimesheetReport) -> TimesheetReport:
        # Logic to load data from input_file

        last_reported_day: str = '0'
        with fileinput.input(files=self.input_source if self.input_source else ('-',)) as file:
            for line in file:
                if (match := self.regex_reported_day.search(line)):
                    last_reported_day = match.group('day')

                if (match := self.regex_timeframe.search(line)):
                    data.timeframe = match.groups()[0] + " - " + match.groups()[1]
                    data.timeframe_start = datetime.strptime(match.groups()[0], data.date_format)
                    data.timeframe_end = datetime.strptime(match.groups()[1], data.date_format)
                elif (match := self.regex_daily_work_hours.search(line)):
                    data.daily_work_hours = float(match.groups()[0].replace(',', '.'))
                elif (match := self.regex_weekly_work_hours.search(line)):
                    data.weekly_work_hours = float(match.groups()[0].replace(',', '.'))
                elif (match := self.regex_total_hours_reported.search(line)):
                    data.total_hours_reported = float(match.groups()[0].replace(',', '.'))
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

        data.timeframe_end = data.timeframe_end.replace(day=int(last_reported_day))
        data.timeframe = data.timeframe_start.strftime("%d.%m.%Y") + " - " + data.timeframe_end.strftime("%d.%m.%Y")
        self._calculate_remaining_working_days(data)
        return data

    def _get_hours_worked(self, match):
        return float(match.group('actualWorkTime').replace(',', '.'))

    def _parse_vacation_days(self, input: str, last_day_of_month: datetime) -> list[date]:
        if not input:
            return []
        
        vacations = input.split(',')
        result = []

        for vacation in vacations:
            # Handle single date
            if "-" not in vacation:
                day = int(vacation)
                result.append(datetime(last_day_of_month.year, last_day_of_month.month, day).date())
            
            # Handle ranges
            elif "-" in vacation:
                parts = vacation.split("-")
                start_day = int(parts[0])
                end_day = int(parts[1]) if parts[1] else last_day_of_month.day
                
                # Generate the range of dates
                for day in range(start_day, end_day + 1):
                    result.append(datetime(last_day_of_month.year, last_day_of_month.month, day).date())
        
        return result

    def _calculate_remaining_working_days(self, data: TimesheetReport):
        # Get the last day of the month
        date = data.timeframe_end
        next_month = date.replace(day=28) + timedelta(days=4)
        last_day_of_month = next_month - timedelta(days=next_month.day)

        # Calculate the vacation days
        vacation_group_size = 7 # for the output: how many vacation days per row
        vacation_days = self._parse_vacation_days(data.vacation_input, last_day_of_month)
        only_vacation_days_date = [v.strftime('%-d.') for v in vacation_days] # create a list of days only with the date part: e.g. "[3., 4., 5.]"
        # join the list into a single string, adding a newline every vacation_group_size's item: e.g. "1., 2., 3., 4., 5., 6., 7.,\n8."
        vacation_days_formatted = "\n".join(", ".join(only_vacation_days_date[i:i + vacation_group_size]) for i in range(0, len(only_vacation_days_date), vacation_group_size))
        data.vacation_days = vacation_days_formatted

        # Create an array of all remaining days in the month
        remaining_days = np.arange(date + timedelta(days=1), last_day_of_month + timedelta(days=1), dtype='datetime64[D]')

        # Get the holidays in Bavaria for the current month
        holidays_by = holidays.country_holidays('DE', subdiv='BY', years=date.year)
        holidays_current_month = {k: v for k, v in holidays_by.items() if k.month == date.month}
        holidays_current_month_only_dates = [*holidays_current_month]

        vacation_and_holidays = vacation_days + holidays_current_month_only_dates

        # Filter out weekends (Saturday=5, Sunday=6) and holidays
        working_days = np.is_busday(remaining_days, holidays=vacation_and_holidays)

        data.remaining_working_days = int(np.sum(working_days))
        data.holidays_current_month = [str(k)+ ": " + v for k, v in holidays_current_month.items()]


    def output_as_text(self):
        is_above_target_quota = self.report.actual_work_from_home_quota() > self.report.target_work_from_home_quota
        maxHomeOfficeLeft = self.report.maximum_work_from_home_hours_left()
        minOfficeLeft = self.report.projected_required_work_from_office_hours()

        quota_color = "[red]" if is_above_target_quota else "[green]"
        table = Table(title=self.report.timeframe)
        table.add_column("")
        table.add_column("Value", justify="right")
        # table.add_column("Description")

        table.add_row("Home Hours", "{:.2f} h".format(self.report.work_from_home))
        table.add_row("Office Hours", "{:.2f} h".format(self.report.work_from_office_calculated()))
        table.add_row("Total Hours", "{:.2f} h".format(self.report.total_hours_reported))
        table.add_row("Home office quota", quota_color + "{:.2f}".format(self.report.actual_work_from_home_quota()) + " %", end_section=True)

        if (is_above_target_quota):
            table.add_row("Exceeded home office hours", "{:.2f} h".format(self.report.target_work_from_home_hours_delta()))
            table.add_row("Required office hours ({:.2f} % quota)".format(self.report.target_work_from_home_quota), "{:.2f} h".format(self.report.required_work_from_office_hours_to_match_quota()), end_section=True)

        table.add_row("Working days left", "{}".format(self.report.remaining_working_days))
        table.add_row("Vacation days considered", self.report.vacation_days)

        holiday_table = Table(show_header=False)
        holiday_table.add_column()
        for x in self.report.holidays_current_month:
            holiday_table.add_row(x)

        table.add_row("Public holidays considered", holiday_table if holiday_table.rows else "-")
        table.add_row("Working hours per day", "{:.2f}".format(self.report.daily_work_hours))

        table.add_row("Maximum Home Office hours left", "{:.2f}".format(maxHomeOfficeLeft) + " ({}".format(math.floor(maxHomeOfficeLeft / self.report.daily_work_hours)) + " days)")
        table.add_row("Minimum Office hours needed", "{:.2f}".format(minOfficeLeft) + " ({}".format(math.ceil(minOfficeLeft / self.report.daily_work_hours)) + " days)", end_section=True)

        console = Console()
        console.print(table)

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
    parser.add_argument('-v', '--vacation', type=str, nargs='?', default=None, help='Your personal holidays, comma-separated. e.g. 12,15-19,22- (day 12 and 15 to 19 and 22 until the end of the month)')
    return parser.parse_args()

def main():
    args = parse_arguments()

    processor = TimesheetProcessor(args.input_source, args.quota, args.dateformat, args.vacation)

    if args.format == 'text':
        processor.output_as_text()
    elif args.format == 'csv':
        processor.output_as_csv()
    elif args.format == 'json':
        processor.output_as_json()

if __name__ == '__main__':
    main()
