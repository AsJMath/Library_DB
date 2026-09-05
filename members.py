# FILES
from db import connect, cr, next_id
from constants import tier_prices, membership_duration, cellstyle
from dates import add_date

# Adding new members to the members table
def add_members():
    member_id=next_id("members")
    member_name=input("Enter the name of the member: ")
    email_address=input("Enter the members email address: ")

    cr.execute("insert into members values(%s, %s, %s)", (member_id, member_name, email_address))
    connect.commit()
    print("New member added without membership. Pay membership separately.")

# Returns the list of all members with an active membership
def active_members():
    cr.execute("select member_id, tier, expiry_date from membership_payments where coverage_start <= curdate() and expiry_date >= curdate()")
    return cr.fetchall()
    # coverage_start <= curdate() ==> the membership has started on or before today
    # expiry_date >= curdate() ==> the membership expires on or after today
    # Meaning, coverage_start <= curdate() <= expiry_date; both above conditions satisfied indicates a currently ongoing membership

# Finds if a particular member has an active membership by iterating thorugh the active_members return for a particular member id
def is_active_member(member_id):
    for active_member_id, tier, expiry_date in active_members():
        if active_member_id == member_id:
            return tier
    return None

# Allows to pay for a membership, extending an old one or starting a new one afresh
def pay_membership():
    member_id=int(input("Enter the member id: "))

    # Ensures that only the four valid tiers are selected
    while True:
        tier = input("Enter tier (bronze/silver/gold/student): ").lower()
        if tier in tier_prices:
            break
        else:
            print("Invalid tier. Choose from: bronze, silver, gold, student.")

    amount = tier_prices[tier]
    cr.execute("select curdate()")
    today = cr.fetchone()[0].strftime("%Y-%m-%d")

    # To dynamically handle members with ongoing memberships and members starting memberships after their old memberships have expired
    cr.execute("select expiry_date from membership_payments where member_id=%s order by expiry_date desc limit 1", (member_id,))
    result = cr.fetchone()

    if result is None:
        # The member has no history of memberships with the library
        start_date = today
    else:
        # The member has a history of memberships with the library
        existing_expiry = result[0].strftime("%Y-%m-%d")
        if existing_expiry > today: # expires in the future, later than today, meaning new membership will be active in future
            start_date = existing_expiry
        else: # expired in the past, before today, meaning new membership is instantly available
            start_date = today

    expiry_date = add_date(start_date, membership_duration)
    payment_id = next_id("membership_payments")

    cr.execute("insert into membership_payments values (%s, %s, %s, %s, %s, %s, %s)",
               (payment_id, member_id, tier, amount, today, start_date, expiry_date))
    connect.commit()

    print(f"Membership ({tier}) recorded. Amount: Rs.{amount}. Valid until: {expiry_date}.")

# Uses aggregate function count(*) to count the number of books that are issued and not returned to a particular member of known member id, i.e the number of books the member has at the moment
def no_of_books_issued_to(member_id):
    cr.execute("select count(*) from transactions where member_id=%s and return_date is null", (member_id,))
    return cr.fetchone()[0]
