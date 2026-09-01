# FILES
from db import connect, cr, next_id
from constants import tier_prices, membership_duration, cellstyle
from dates import add_date

def add_members():
    member_id=next_id("members")
    member_name=input("Enter the name of the member: ")
    address=input("Enter the members' address: ")

    cr.execute("insert into members values(%s, %s, %s)", (member_id, member_name, address))
    connect.commit()
    print("New member added without membership. Pay membership separately.")

def active_members():
    cr.execute("""
        select member_id, tier, expiry_date from membership_payments
        where coverage_start <= curdate() and expiry_date >= curdate()
    """)
    return cr.fetchall()

def is_active_member(member_id):
    for active_member_id, tier, expiry_date in active_members():
        if active_member_id == member_id:
            return tier
    return None

def pay_membership():
    member_id=int(input("Enter the member id: "))

    while True:
        tier = input("Enter tier (bronze/silver/gold/student): ").lower()
        if tier in tier_prices:
            break
        else:
            print("Invalid tier. Choose from: bronze, silver, gold, student.")

    amount = tier_prices[tier]
    cr.execute("select curdate()")
    today = cr.fetchone()[0].strftime("%Y-%m-%d")

    cr.execute("select expiry_date from membership_payments where member_id=%s order by expiry_date desc limit 1", (member_id,))
    result = cr.fetchone()

    if result is None:
        start_date = today
    else:
        existing_expiry = result[0].strftime("%Y-%m-%d")
        if existing_expiry > today: #expires in the future, meaning new membership will be active in future
            start_date = existing_expiry
        else: #expires before today, meaning new membership is instantly available
            start_date = today

    expiry_date = add_date(start_date, membership_duration)
    payment_id = next_id("membership_payments")

    cr.execute("insert into membership_payments values (%s, %s, %s, %s, %s, %s, %s)",
               (payment_id, member_id, tier, amount, today, start_date, expiry_date))
    connect.commit()

    print(f"Membership ({tier}) recorded. Amount: Rs.{amount}. Valid until: {expiry_date}.")

def no_of_books_issued_to(member_id):
    cr.execute("select count(*) from transactions where member_id=%s and return_date is null", (member_id,))
    return cr.fetchone()[0]
