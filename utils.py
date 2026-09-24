# MODULES
from datetime import datetime, timedelta
import sys # Allows access to Python interpreter level settings and the system the interpreter runs on
import time

# A buffer before next print statements to prevent the CLI overflowing with text
def buffer():
    input("\nPress Enter to continue...")

# Prints in a typewriter style; usage limited to single line print statements such as intro and outro
def fancy_print(text, delay=0.01):
    for char in text:

        # All programs have 3 standard I/O streams: stdin (standard input), stdout (standard output), stderr (standard error)
        # stdout is a file-like object that supports file-like methods like .write() and .flush()
        sys.stdout.write(char)

        # For efficiency, Python collects text to be printed on CLI and dumps them together. To prevent this, .flush() is used after every iteration of the loop (i.e. after every charcter is printed) so that characters appear one-by-one for a typewriter effect
        sys.stdout.flush()
        time.sleep(delay) # Suspends the executiong for a given number of seconds

# Returns a new date in YYYY-MM-DD format after converting the original date to a date time object and incrementing it by a particular amount
def add_date(original_date, increment):
    new_date_obj = datetime.strptime(original_date, "%Y-%m-%d") + timedelta(days=increment)
    return new_date_obj.strftime("%Y-%m-%d")

# Returns number of days date2 is after date1, or 0 if date2 is not after date1
def is_late(date1, date2):
    if datetime.strptime(date2, "%Y-%m-%d") > datetime.strptime(date1, "%Y-%m-%d"):
        return (datetime.strptime(date2, "%Y-%m-%d") - datetime.strptime(date1, "%Y-%m-%d")).days
    else:
        return 0
