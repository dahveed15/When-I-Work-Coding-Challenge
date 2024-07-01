import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ShiftID is a unique numeric identifier for
# the shift. This is a 64-bit value. (e.g. "ShiftID": 2442377529)

# EmployeeID is the numeric identifier of
# the employee who worked the shift.
# This is a 64-bit value. (e.g. "EmployeeID": 36172477)
# employee id is not unique. The same employee could have multiple shifts

# StartTime is an RFC3339 formatted date time string indicating the start of the shift.
# (e.g. 1985-04-12T23:20:50.52Z)

# EndTime is an n RFC3339 formatted date time string indicating the end of the shift.
# This must be greater than the StartTime.
# (e.g. 1985-04-13T07:19:14.03Z)


# Note: A week is defined as starting on midnight on Sunday in Central Time, and ends on
# the following Sunday at midnight.

# Using the dataset provided, calculate the following:
# ● The total number of regular hours worked per employee in a given week. Regular
# hours are the number of hours worked up to 40 hours.
# ● The total number of overtime hours worked per employee in a given week.
# Overtime hours are the number of hours worked beyond 40 hours in a given
# week.
# ● If a shift crosses midnight of Sunday, its calculations should be split between the
# two weeks.

# You should also determine what shifts are "invalid" for a user. Invalid shifts are shifts for
# a single Employee that overlap with each other. For example; if you have two shifts, one
# begins at 8am and ends at 4pm and the other begins at 9am and ends at 5pm for the
# same employee. Both of these shifts would be considered invalid as they overlap.
# Invalid shifts should not be included in an employee's totals
# Your program should output a json in the following format:
# [
#     {
#         "EmployeeID": 456,
#         "StartOfWeek": "2021-08-22",
#         "RegularHours": 20.56,
#         "OvertimeHours": 0,
#         "InvalidShifts": [
#             123,
#             234
#         ]
#     }
# ]

# EmployeeID, the ID of the employee for this particular summary object.
# StartOfWeek, the date that this week began on in the following format: "YYYY-MM-DD"
# RegularHours, the total number of regular hours for this employee during this week excluding invalid shifts.
# OvertimeHours, the total number of overtime hours for this employee during this week excluding invalid shifts.
# InvalidShifts, an array of Shift IDs that overlap for this employee during this week.

# Read/parse the JSON file
with open('dataset_(1).json', 'r', encoding='utf-8') as file:
    shift_data = json.load(file)

sunday_start_of_week_offsets = {}


def convert_rfc3339_to_central_datetime_object(date_string):
    utc_datetime = datetime.fromisoformat(date_string.replace("Z", "+00:00"))

    central_timezone = ZoneInfo("America/Chicago")
    central_datetime = utc_datetime.astimezone(central_timezone)

    return central_datetime


def get_start_of_week_sunday(date_string):
    converted_date = convert_rfc3339_to_central_datetime_object(date_string)

    # Calculate the previous Sunday or the same Sunday if the date is Sunday
    # Weekday() returns 0 for Monday, 1 for Tuesday, ..., 6 for Sunday
    days_since_sunday = (converted_date.weekday() + 1) % 7
    start_of_week_sunday = converted_date - timedelta(days=days_since_sunday)

    # Format datetime object to YYYY-MM-DD string
    formatted_date = start_of_week_sunday.strftime("%Y-%m-%d")
    return formatted_date


def get_shift_hours_difference(start, end):
    startTime = convert_rfc3339_to_central_datetime_object(start)
    endTime = convert_rfc3339_to_central_datetime_object(end)

    time_difference = endTime - startTime
    hours_difference = time_difference.total_seconds() / 3600

    return hours_difference


def calculate_week_regular_hours(shifts):
    total = 0

    for shift in shifts:

        # compare the beginning sunday of the week for the shift's start and end time
        # if the sundays are the same, you know that both dates fall in the same week
        # if the sundays are different, you know that it's a saturday to sunday shift
        shift_start_time_beginning_of_week = get_start_of_week_sunday(
            shift["StartTime"])
        shift_end_time_beginning_of_week = get_start_of_week_sunday(
            shift["EndTime"])
        is_saturday_to_sunday_shift = shift_start_time_beginning_of_week != shift_end_time_beginning_of_week

        # if there is a sat/sun shift
        # add the offset of 12-current saturday hour to total hours
        # check if a dict with key of start of sunday exists
        # if it does not, create a key/value pair of EmployeeID-shift_end_time_beginning_of_week with its value being
        # #the endtime hours
        # create an add offset hours method
        # go through each employee's shifts again and add the offset hours for that week if it exists

        if is_saturday_to_sunday_shift:
            # add saturday offset to total
            saturday_to_sunday_shift_start_time = convert_rfc3339_to_central_datetime_object(
                shift["StartTime"])
            saturday_to_sunday_shift_start_offset_value = saturday_to_sunday_shift_start_time.hour + \
                saturday_to_sunday_shift_start_time.minute / 60.0
            # hours is in military time, so we need to do 24 (midnight) - hour
            # added absolute value in case there's some weird negative number by chance
            total += abs(24 - saturday_to_sunday_shift_start_offset_value)

            saturday_to_sunday_shift_end_time = convert_rfc3339_to_central_datetime_object(
                shift["EndTime"])
            saturday_to_sunday_shift_start_end_offset = saturday_to_sunday_shift_end_time.hour + \
                saturday_to_sunday_shift_end_time.minute / 60.0

            # identifier to find offsets later
            beginning_of_week_sunday_with_employee_id = f"{
                shift["EmployeeID"]}-{shift_end_time_beginning_of_week}"

            # store the sunday offset time to be added later
            # we don't need to do any subtraction becuase hours in military time will be after 0 on Sunday
            sunday_start_of_week_offsets[beginning_of_week_sunday_with_employee_id] = saturday_to_sunday_shift_start_end_offset
        else:
            # add hours as normal
            total += get_shift_hours_difference(
                shift["StartTime"], shift["EndTime"])

    return total


def add_sunday_offset_hours_to_regular_hours(employee_id, sunday_date, hours):

    total = 0

    beginning_of_week_sunday_with_employee_id = f"{
        employee_id}-{sunday_date}"

    if beginning_of_week_sunday_with_employee_id in sunday_start_of_week_offsets:
        total += sunday_start_of_week_offsets[beginning_of_week_sunday_with_employee_id]

    total += hours

    return total


def calculate_week_overtime_hours(reg_hours):
    return reg_hours - 40 if reg_hours > 40 else 0


def get_all_employee_shifts(employee_id):
    return list(filter(lambda shift: shift["EmployeeID"] == employee_id, shift_data))


def separate_shift_weeks_by_start_of_week_sunday(shifts):
    start_of_week_sundays = {}

    for shift in shifts:
        start_of_week_sunday = get_start_of_week_sunday(shift["StartTime"])
        if start_of_week_sunday not in start_of_week_sundays:
            start_of_week_sundays[start_of_week_sunday] = []

        start_of_week_sundays[start_of_week_sunday].append(shift)

    # ['2021-08-29', [{'ShiftID': 2442377796, 'EmployeeID': 36172660, 'StartTime': '2021-08-31T11:30:00.000000Z', 'EndTime': '2021-08-31T15:30:00.000000Z'}, {'ShiftID': 2442377778, 'EmployeeID': 36172660, 'StartTime': '2021-08-30T11:30:00.000000Z', 'EndTime': '2021-08-30T15:30:00.000000Z'}]]
    return [[starting_sunday, shifts_in_week] for starting_sunday, shifts_in_week in start_of_week_sundays.items()]


def get_invalid_shifts(shifts):
    # check to see if there is any start time that is between
    # a start time and end time of another shift
    invalid_shifts = []

    for i in range(len(shifts)):
        current_shift = shifts[i]
        current_shift_start_time = convert_rfc3339_to_central_datetime_object(
            current_shift["StartTime"])
        current_shift_end_time = convert_rfc3339_to_central_datetime_object(
            current_shift["EndTime"])

        for j in range(i + 1, len(shifts)):
            other_shift = shifts[j]
            other_shift_start_time = convert_rfc3339_to_central_datetime_object(
                other_shift["StartTime"])
            other_shift_end_time = convert_rfc3339_to_central_datetime_object(
                other_shift["EndTime"])

            is_other_shift_between_current_shift = current_shift_start_time < other_shift_start_time < current_shift_end_time
            is_current_shift_between_other_shift = other_shift_end_time < current_shift_start_time < other_shift_end_time

            if is_other_shift_between_current_shift or is_current_shift_between_other_shift:
                invalid_shifts.extend(
                    [current_shift["ShiftID"], other_shift["ShiftID"]])

    return invalid_shifts

    # Steps:
    # Load up the JSON file and store the variable in shift_data
    # find all employee ids for shift data
    # iterate through employee ids and have a result array
    # get all shifts for employee id
    # convert all dates and determine if dates go into the next week
    # if they do, split them up and group them by start of week (Sunday CST). Saturday at 11:59 is the end of that week
    # for each group, get the start of week sunday
    # find invalid shifts for them
    # filter each shift week group to remove the invalid shifts
    # add up the hours for each shift in the week, determining if any offset hours need to be removed

    # if they total over 40 for that week group, determine overtime hours by hours - 40
    # create a new dictionary for each of the categories in line 40 for each group
    # push dictionary to result array
    # once complete, write the data to a new JSON file


def employee_shift_output():
    # Ensure getting unique ids by using a set
    employee_ids = set([item["EmployeeID"] for item in shift_data])
    result = []

    for employee_id in employee_ids:
        employee_shifts = get_all_employee_shifts(employee_id)
        employee_shifts_grouped_by_start_of_week_sunday = separate_shift_weeks_by_start_of_week_sunday(
            employee_shifts)
        for all_shifts_per_week in employee_shifts_grouped_by_start_of_week_sunday:
            invalid_shift_ids = get_invalid_shifts(all_shifts_per_week[1])
            starting_sunday = all_shifts_per_week[0]

            # get all shifts that don't have invalid ids
            valid_shifts_per_week = [
                shift for shift in all_shifts_per_week[1] if shift['ShiftID'] not in invalid_shift_ids]

            # find shifts that go from saturday to next Sunday and determine splitting total hours added
            regular_hours_plus_saturday_offset = calculate_week_regular_hours(
                valid_shifts_per_week)
            total_hours_plus_sunday_offset_hours = add_sunday_offset_hours_to_regular_hours(
                employee_id, starting_sunday, regular_hours_plus_saturday_offset)

            overtime_hours = calculate_week_overtime_hours(
                total_hours_plus_sunday_offset_hours)

            regular_hours_value = total_hours_plus_sunday_offset_hours if total_hours_plus_sunday_offset_hours < 40 else 40

            employee_shift_info = {
                "EmployeeID": employee_id,
                "StartOfWeek": starting_sunday,
                "RegularHours": regular_hours_value,
                "OvertimeHours": overtime_hours,
                "InvalidShifts": invalid_shift_ids
            }

            result.append(employee_shift_info)

    return result


employee_data = employee_shift_output()


# create new JSON file with the updated data called output.json
# Write the JSON data to that file
with open('output.json', 'w', encoding='utf-8') as file:
    json.dump(employee_data, file, ensure_ascii=False, indent=2)
