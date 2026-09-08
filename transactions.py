# FILES
from db import connect, cr
from books import is_available, query_books_by_name, book_exists, current_borrower, issued_books
from members import is_active_member, no_of_books_issued_to, query_member_name
from dates import is_late, add_date
from constants import max_books, loan_period, fines, cellstyle

# MODULES
from tabulate import tabulate

def issue_book():
    # Allows the librarian to search for the book and identify which one to issue based on generic search
    while True:
        matches, choices, book_ids = query_books_by_name()
        print()
        book_id = int(input("Enter the book id to issue or enter 0 to seach again: "))
        if book_id==0:
            continue
        elif book_id not in book_ids:
            print("Please enter a book id from the above list.")
        elif not is_available(book_id):
            print("This book is out of the library and cannot be issued.")
        else:
            # book exists and is available (thus proceed)
            break

    while True:
        matches, choices, member_ids = query_member_name()
        print()
        member_id = int(input("Enter the member id or enter 0 to search again: "))
        if member_id==0:
            continue
        if member_id not in member_ids:
            print("Enter a member id from the search result.")
        else:
            break

    # Checks if the member has an active membership
    member_tier = is_active_member(member_id)
    if member_tier is None:
        print("No active membership on record. Please register or renew before issuing.")
        return
    else:
        print(f"Member has a active {member_tier} membership and has taken {no_of_books_issued_to(member_id)} out of the permitted {max_books[member_tier]} books.")

    # If the member is has an active membership, check if the member has exceeded their limit on issuing books
    books_currently_issued = no_of_books_issued_to(member_id)
    if books_currently_issued >= max_books[member_tier]:
        print(f"This member has reached their {member_tier} tier limit of {max_books[member_tier]} books. Return a book before issuing another.")
        return

    # Updating the transactions table for new issue
    issue_date=input("Enter the date of issuing (YYYY-MM-DD): ")
    return_date=None #gets converted to NULL
    due_date=add_date(issue_date, loan_period[member_tier])

    cr.execute("insert into transactions (book_id, member_id, issue_date, return_date, due_date) values (%s, %s, %s, %s, %s)", (book_id, member_id, issue_date, return_date, due_date))
    connect.commit()
    print("Book issued.")

def return_book():
    issued_books_list=issued_books()

    if not issued_books_list:
        print("No books are currently issued.")
        return

    transaction_ids=[]
    for record in issued_books_list:
        transaction_ids.append(record[0])

    headers=["Transaction ID", "Book Name", "Member Name", "Issue Date", "Due Date"]
    print("Issued books:")
    print(tabulate(issued_books_list, headers=headers, tablefmt=cellstyle))

    while True:
        print()
        transaction_id = int(input("Enter the transaction id to return: "))
        if transaction_id not in transaction_ids:
            print("Please enter a transaction id from the list above.")
        else:
            break         
           
    # Finds the transaction where that particular book was issued and not returned
    cr.execute("select due_date, issue_date, book_id from transactions where transaction_id=%s and return_date is null", (transaction_id,))
    result=cr.fetchone()
    if result:
        due_date=result[0].strftime("%Y-%m-%d")
        issue_date=result[1].strftime("%Y-%m-%d")

    # Accepting return date and rejecting impossible case of issue date being after the return date to maintain data integrity
    while True:
        return_date=input("Enter the return date (YYYY-MM-DD): ")
        if is_late(return_date, issue_date):
            # returns a non zero value if issue date is after the return date
            print(f"Return date ({return_date}) cannot be before the issue date ({issue_date}). Try again.")
        else: # Valid return date after the issue date
            break

    # From the previous select statement, goes to that particular record and sets a non null return date to indicate that it has been returned
    cr.execute("update transactions set return_date=%s where transaction_id=%s", (return_date, transaction_id))
    connect.commit()

    # Dynamically calculates lateness of the book and issues fines
    days_late=is_late(due_date, return_date)
    if days_late:
        late_amount = days_late * fines["late"]
        print(f"This book is {days_late} days late and Rs. {late_amount} has been charged.")
        is_late_paid=False
        cr.execute("insert into fines (transaction_id, fine_type, amount, paid) values(%s, %s, %s, %s)", (transaction_id, 'late', late_amount, is_late_paid))
        connect.commit()
    else:
        print("This book was returned on time.")

    # Asks if the book is damaged and issues the flat fines for the same
    while True:
        is_damaged=input("Is the book damaged (y/n): ").lower()
        if is_damaged=="y":
            damage_amount=fines["damage"]
            is_damage_paid=False

            cr.execute("insert into fines (transaction_id, fine_type, amount, paid) values(%s, %s, %s, %s)", (transaction_id, 'damage', damage_amount, is_damage_paid))
            connect.commit()
            print("Rs. 700 has been charged.")
            break
        elif is_damaged=="n":
            break
        else:
            print("Invalid input, enter (y/n) only.")

def settle_fines():
    while True:
        matches, choices, member_ids = query_member_name()
        print()
        member_id = int(input("Enter the member id or enter 0 to search again: "))
        if member_id==0:
            continue
        elif member_id not in member_ids:
            print("Please enter a member id from the list above.")
        else:
            break

    # Finds all the pending fines for a particular member
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
    fine_input = input("Enter the fine id for the fine you want to settle or press 0 for settling all fines: ")
    try:
        fine_id = int(fine_input)
    except ValueError:
        print("Invalid input. No fines were settled.")
        return

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

def pending_fines():
        cr.execute("select fine_id, member_name, book_name, fine_type, amount from fines, transactions, members, books where paid=0 and members.member_id=transactions.member_id and transactions.transaction_id=fines.transaction_id and transactions.book_id=books.book_id")
        pending_fines_list=cr.fetchall()
        return pending_fines_list # returns the result or []