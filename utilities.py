from datetime import datetime

def capitalize(text):
    return text[0].upper() + text[1:]

def to_date(string):
    """
    Use strptime to try to parse the date. If it's not a date in that specified
    format, strptime will throw an exception.

    Documentation on format: https://www.journaldev.com/23365/python-string-to-datetime-strptime
    """
    string = string.replace(',', '').replace(':', '')
    date = None
    try:
        date = datetime.strptime(string, "%B %d %H%M")
    except ValueError:
        # Not a date
        pass
    try:
        date = datetime.strptime(string, "%b %d %H%M")
    except ValueError:
        # Not a date
        pass
    return date