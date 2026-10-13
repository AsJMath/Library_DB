### members.py

# FILES
import db
import constants
import utils

# MODULES
from rapidfuzz import process, fuzz
from tabulate import tabulate

# HELPER FUNCTIONS

# Returns the list of all members with an active membership
def active_members():
    db.cr.execute("select member_id, tier, expiry_date from membership_payments where coverage_start <= curdate() and expiry_date >= curdate()")
    return db.cr.fetchall()
    # coverage_start <= curdate() ==> the membership has started on or before today
    # expiry_date >= curdate() ==> the membership expires on or after today
    # Meaning, coverage_start <= curdate() <= expiry_date; both above conditions satisfied indicates a currently ongoing membership

# Finds if a particular member has an active membership by iterating thorugh the active_members return for a particular member id
def is_active_member(member_id):
    for active_member_id, tier, expiry_date in active_members():
        if active_member_id == member_id:
            return tier
    return None

# Uses aggregate function count(*) to count the number of books that are issued and not returned to a particular member of known member id, i.e the number of books the member has at the moment
def no_of_books_issued_to(member_id):
    db.cr.execute("select count(*) from transactions where member_id=%s and return_date is null", (member_id,))
    return db.cr.fetchone()[0]

# USER FUNCTIONS

# Adding new members to the members table
def add_member():
    member_name=input("Enter the name of the member: ")
    email_address=input("Enter the members email address: ")

    db.cr.execute("insert into members (member_name, email_address) values (%s, %s)", (member_name, email_address))
    db.connect.commit()
    print("New member added without membership. Pay membership separately.")

# Allows to delete members that have no records of transactions
def delete_member():
    matches, choices, member_ids = query_by_member_name()
    print()

    if not matches:
        return

    member_id_input = input("Enter the member id to delete: ")
    try:
        member_id = int(member_id_input)
    except ValueError:
        print("Invalid input. No member was deleted.")
        return

    if member_id not in member_ids:
        print("Please enter a member id from the search results. No member was deleted.")
        return

    # If member id is fron the list as per the query...
    db.cr.execute("select 1 from transactions where member_id=%s and return_date is null limit 1", (member_id,))
    if db.cr.fetchone() is not None:
        print("This member currently has a book issued and cannot be deleted. Please process the return first.")
        # Prevents deleting if a member has a book issued
        return

    # Prevents errors due to refferential integrity in transactions and memberships table (fines table need not be checked since all fines are linked to transactions, if any)
    db.cr.execute("select 1 from transactions where member_id=%s limit 1", (member_id,))
    has_transaction_history = db.cr.fetchone() is not None

    db.cr.execute("select 1 from membership_payments where member_id=%s limit 1", (member_id,))
    has_membership_history = db.cr.fetchone() is not None

    if has_transaction_history or has_membership_history:
        print("This member has existing transaction or membership history and cannot be deleted.")
        return

    db.cr.execute("delete from members where member_id=%s", (member_id,))
    db.connect.commit()
    print("Member has been deleted.")

def edit_member():
    matches, choices, member_ids = query_by_member_name()
    print()

    if not matches:
        return  # query_by_member_name() already printed "No such members found."

    member_id_input = input("Enter the member id to edit: ")
    try:
        member_id = int(member_id_input)
    except ValueError:
        print("Invalid input. No member was edited.")
        return

    if member_id not in member_ids:
        print("Please enter a member id from the search results. No member was edited.")
        return

    # Fetches the current member details
    db.cr.execute("select member_name, email_address from members where member_id=%s",(member_id,))
    details = list(db.cr.fetchone())

    header = ["Member Name", "Email Address"]
    print(tabulate([details], headers=header, tablefmt=constants.cellstyle))

    # Accepts new details, allowing the old values to be retained
    new_member_name = input("Enter the new member name or press Enter to keep the old name: ")
    new_email_address = input("Enter the new email address or press Enter to keep the old email: ")

    entered_details = [new_member_name, new_email_address]

    for i in range(2):
        if entered_details[i] != "":
            details[i] = entered_details[i]

    # Updates the database
    db.cr.execute("update members set member_name=%s, email_address=%s where member_id=%s",(details[0], details[1], member_id))
    db.connect.commit()

    print("Member updated.")
    print(tabulate([details], headers=header, tablefmt=constants.cellstyle))

# Allows to pay for a membership, extending an old one or starting a new one afresh
def pay_membership():
    matches, choices, member_ids = query_by_member_name()
    print()

    if not matches:
        return  # query_by_member_name() already printed "No such members found."

    member_id_input = input("Enter the member id: ")
    try:
        member_id = int(member_id_input)
    except ValueError:
        print("Invalid input. No membership was recorded.")
        return

    if member_id not in member_ids:
        print("Please enter a member id from the search results. No membership was recorded.")
        return

    tier = input("Enter tier (bronze/silver/gold/student): ").lower()
    if tier not in constants.tier_prices:
        print("Invalid tier. Choose from: bronze, silver, gold, student. No membership was recorded.")
        return

    amount = constants.tier_prices[tier]
    db.cr.execute("select curdate()")
    today = db.cr.fetchone()[0].strftime("%Y-%m-%d")

    # To dynamically handle members with ongoing memberships and members starting memberships after their old memberships have expired
    db.cr.execute("select expiry_date from membership_payments where member_id=%s order by expiry_date desc limit 1", (member_id,))
    result = db.cr.fetchone()

    if result is None:
        # The member has no history of memberships with the library
        start_date = today
    else:
        # The member has a history of memberships with the library (dates ambiguous; deciphered below)
        existing_expiry = result[0].strftime("%Y-%m-%d")
        if existing_expiry > today: # expires in the future, later than today, meaning new membership will be active in future
            start_date = existing_expiry
        else: # expired in the past, before today, meaning new membership is instantly available
            start_date = today

    expiry_date = utils.add_date(start_date, constants.membership_duration)

    db.cr.execute("insert into membership_payments(member_id, tier, amount, payment_date, coverage_start, expiry_date) values (%s, %s, %s, %s, %s, %s)", (member_id, tier, amount, today, start_date, expiry_date))
    db.connect.commit()

    print(f"Membership ({tier}) recorded. Amount: Rs.{amount}. Valid until: {expiry_date}.")
    
def query_by_member_name():
    query=input("Enter the member name: ")

    if len(query) < 5:
        print("Please enter at least 5 characters to search.")
        return [], {}, [] # satisfies the return matches, choices for consistency irrespective of which return gets triggered.

    db.cr.execute("select member_id, member_name, email_address from members")
    all_members=db.cr.fetchall()

    choices={}    
    for record in all_members:
        member_name=record[1]
        choices[member_name]=record
        # choices is a dictionary of key value pairs with each key being the member name (what the rapidfuzz algorithm searches) and the corresponding value being a tuple (<member_id>, <member_name>, <email_address>)

        # each key that the rapidfuzz algorithm searches for (a string) is linked to the actual data from the database, the book (book_name) and its details (book_id and author_name)

    matches=process.extract(query, choices.keys(), limit=5, score_cutoff=60, scorer=fuzz.partial_ratio)
    # .extract(<the string to be searched for, <what to search in>, <how many results to show>, <requires a minimum match of how much %>, <the logic or scorer used for computation>)
    # scorer=fuzz.partial_ratio finds the best matching substring within each key, rather than comparing the full strings —

    # matches is a list of tuples, with each tuple of the format (<key from choices>, <likelihood of a match out of 100>, <index in the choices dictionary>)
    print()
    if not matches:
        print("No such members found.")
        return [], {}, []
    else:
        rows=[]
        member_ids=[]
        for match_str, score, index in matches:
            record=choices[match_str] # For each matched string, find the member information tuple that corresponds to the member_name
            member_id=record[0]
            rows.append(record)
            member_ids.append(member_id)

        print(tabulate(rows, headers=["Member ID", "Member Name", "Email Address"], tablefmt=constants.cellstyle))
        return matches, choices, member_ids