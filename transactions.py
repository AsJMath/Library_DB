# FILES
from db import connect, cr, next_id
from books import is_available, query_books_by_name
from members import is_active_member, no_of_books_issued_to
from dates import is_late, add_date
from constants import max_books, loan_period, fines, cellstyle

# MODULES
from tabulate import tabulate

def issue_book():
    transaction_id=next_id("transactions")

    # Allows the librarian to search for the book and identify which one to issue based on generic search
    while True:
        query_books_by_name()
        print()
        book_id = int(input("Enter the book id to issue or enter 0 to seach again: "))
        if book_id==0:
            continue
        if is_available(book_id):
            # book is available i.e. is in the library and can be issued (thus proceed)
            break
        else:
            print("This book is out of the library and cannot be issued.")

    member_id=int(input("Enter the member id: "))

    # Checks if the member has an active membership
    member_tier = is_active_member(member_id)
    if member_tier is None:
        print("No active membership on record. Please register or renew before issuing.")
        return
    else:
        print(f"Member has a active {member_tier} membership and has taken {no_of_books_issued_to(member_id)} out of the permitted {max_books[member_tier]}  books.")

    # If the member is has an active membership, check if the member has exceeded their limit on issuing books
    books_currently_issued = no_of_books_issued_to(member_id)
    if books_currently_issued >= max_books[member_tier]:
        print(f"This member has reached their {member_tier} tier limit of {max_books[member_tier]} books. Return a book before issuing another.")
        return

    # Updating the transactions table for new issue
    issue_date=input("Enter the date of issuing (YYYY-MM-DD): ")
    return_date=None #gets converted to NULL
    due_date=add_date(issue_date, loan_period[member_tier])

    cr.execute("insert into transactions values(%s, %s, %s, %s, %s, %s)", (transaction_id, book_id, member_id, issue_date, return_date, due_date))
    connect.commit()
    print("Book issued.")

def return_book():
    # Checks if the book is really out of the library
    while True:
        book_id = int(input("Enter the book id: "))
        if is_available(book_id)==False:
            #book is not available i.e. it is out of the library and thus can be returned (thus proceed)
            break
        else:
            print("This book is in  the library.")
            # Book is in the library, thus it cannot be returned, enter a book that is not in the library

    # Finds the transaction where that particular book was issued and not returned
    cr.execute("select due_date, transaction_id, issue_date from transactions where return_date is null and book_id=%s", (book_id,))
    result=cr.fetchone()
    due_date=result[0].strftime("%Y-%m-%d")
    transaction_id=result[1]
    issue_date=result[2].strftime("%Y-%m-%d")

    # Accepting return date and rejecting impossible case of issue date being after the return date to maintain data integrity
    while True:
        return_date=input("Enter the return date (YYYY-MM-DD): ")
        if is_late(return_date, issue_date):
            # returns a non zero value if issue date is after the return date
            print(f"Return date ({return_date}) cannot be before the issue date ({issue_date}). Try again.")
        else:
            break

    # From the previous select statement, goes to that particular record and sets a non null return date to indicate that it has been returned
    cr.execute("update transactions set return_date=%s where book_id=%s and return_date is null", (return_date, book_id))
    connect.commit()

    # Dynamically calculates lateness of the book and issues fines
    days_late=is_late(due_date, return_date)
    if days_late:
        late_amount = days_late * fines["late"]
        print(f"This book is {days_late} days late and Rs. {late_amount} has been charged.")
        is_late_paid=False
        fine_id=next_id("fines")

        cr.execute("insert into fines values(%s, %s, %s, %s, %s)", (fine_id, transaction_id, 'late', late_amount, is_late_paid))
        connect.commit()
    else:
        print("This book was returned on time.")

    # Asks if the book is damaged and issues the flat fines for the same
    while True:
        is_damaged=input("Is the book damaged (y/n): ").lower()
        if is_damaged=="y":
            damage_amount=fines["damage"]
            is_damage_paid=False
            fine_id=next_id("fines")

            cr.execute("insert into fines values(%s, %s, %s, %s, %s)", (fine_id, transaction_id, 'damage', damage_amount, is_damage_paid))
            connect.commit()
            print("Rs. 700 has been charged.")
            break
        elif is_damaged=="n":
            break
        else:
            print("Invalid input, enter (y/n) only.")

def settle_fines():

    # Finds all the pending fines for a particular member
    member_id=int(input("Enter member id: "))
    cr.execute("select fine_id, fine_type, amount, book_name, return_date from transactions, fines, books where books.book_id=transactions.book_id and fines.transaction_id=transactions.transaction_id and paid=0 and transactions.member_id=%s", (member_id,))
    pending_fines=cr.fetchall()

    # Safety check to prevent tabulate function receiving a none object to tabulate
    if not pending_fines:
        print("This member has no pending fines.")
        return

    # Lists all the fines for the particular member
    headers=["Fine ID", "Fine Type", "Amount", "Book Name", "Return Date"]
    print("Pending fines:")
    print(tabulate(pending_fines, headers=headers, tablefmt=cellstyle))

    # Asks the librarian to choose which of the fine to settle or 0 to settle all of the members fine
    fine_id = int(input("Enter the fine id for the fine you want to settle or press 0 for settling all fines: "))

    if fine_id == 0:
        cr.execute("update fines,transactions set fines.paid=1 where transactions.transaction_id=fines.transaction_id and transactions.member_id=%s and fines.paid=0", (member_id,))
        connect.commit()
        print("All fines settled.")
    else:
        cr.execute("update fines,transactions set fines.paid=1 where transactions.transaction_id=fines.transaction_id and fines.fine_id=%s and transactions.member_id=%s and fines.paid=0", (fine_id, member_id))
        connect.commit()

        if cr.rowcount == 0:
            print("Invalid fine ID for this member, or already paid.")
        else:
            print("Fine settled.")
