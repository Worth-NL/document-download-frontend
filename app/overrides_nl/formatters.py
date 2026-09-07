"""Dutch date formatting for document-download-frontend.

`strftime("%A")`/`strftime("%B")` render English weekday/month names under
the C locale that this app runs in (no locale.setlocale anywhere) -- this is
the same systemic bug already fixed app-wide in notifynl-admin
(app/overrides_nl/formatters.py). DUTCH_WEEKDAYS/DUTCH_MONTHS and
_translate_weekday_and_month are copied from there so both apps translate
identically.
"""

from datetime import date, timedelta

from dateutil import parser

DUTCH_WEEKDAYS = {
    "Monday": "maandag",
    "Tuesday": "dinsdag",
    "Wednesday": "woensdag",
    "Thursday": "donderdag",
    "Friday": "vrijdag",
    "Saturday": "zaterdag",
    "Sunday": "zondag",
}

DUTCH_MONTHS = {
    "January": "januari",
    "February": "februari",
    "March": "maart",
    "April": "april",
    "May": "mei",
    "June": "juni",
    "July": "juli",
    "August": "augustus",
    "September": "september",
    "October": "oktober",
    "November": "november",
    "December": "december",
}


def _translate_weekday_and_month(formatted):
    for english, dutch in {**DUTCH_WEEKDAYS, **DUTCH_MONTHS}.items():
        formatted = formatted.replace(english, dutch)
    return formatted


def format_file_expiry_date(available_until: str) -> str:
    file_expiry_date = parser.parse(available_until).date()

    formatted_date = _translate_weekday_and_month(file_expiry_date.strftime("%d %B %Y").lstrip("0"))
    day_of_week = DUTCH_WEEKDAYS[file_expiry_date.strftime("%A")]

    # only show day of the week if file expiry date within a month from today
    if file_expiry_date - date.today() <= timedelta(days=30):
        return f"{day_of_week} {formatted_date}"

    return formatted_date
