# FILES
from db import connect, cr #, next_id
# import db automatically runs the db file and create database is called
from books import add_books, currentBorrower, generic_search, query_books_by_name #, is_available
from members import add_members, active_members, is_active_member, pay_membership #, no_of_books_issued_to
from constants import intro_message, cellstyle #, fines, loan_period, max_books, tier_prices, membership_duration
from transactions import issue_book, settle_fines, return_book
from graphing import top_ten_books, top_ten_members, membership_chart, genre_chart
# from dates import is_late, add_date

# MODULES
from tabulate import tabulate

print(intro_message)
run=True
while run:
    print("""
Choose an option
$ Actions
1. Add books
2. Add members
3. Issue book
4. Return book
5. Settle Fines
6. Pay Membership

$ Information
7. Generic Search - Search books by book, author or genre      
8. Book Info - Information about the book, current borrower and its transaction history
9. Member Info - Information about the member, membership status and their transaction history
10. Membership Info - Information about all members and their membership status
11. Pending Fines - List of all pending fines
12. Issued Books - List of all books out of the library
13. Overdue Books - List all books overdue
14. Top 10 Books - Top 10 list of most issued books
15. Top 10 Members - Top 10 list of members who issue books most
16. Membership Chart - See a pie chart of what memberships members have
17. Genre Chart - See a pie chart of the genre's available

18. Custom Query - Enter your own custom SELECT query          
19. See Database Schema                  
20. Exit
""")
    choice=input("Enter the number: ")

    # Handles stray values that are not integers or that are not within the valid ranges
    try:
        choice=int(choice)
    except ValueError:
        print("Try Again!")
        continue # forces the next iteration of the loop
    if choice not in range(1,21):
        print("Try again!")

    elif choice==1:
        add_books()

    elif choice==2:
        add_members()

    elif choice==3:
        issue_book()

    elif choice==4:
        return_book()

    elif choice==5:
        settle_fines()

    elif choice == 6:
        pay_membership()

    elif choice==7:
        generic_search()

    # Book Info    
    elif choice==8:
        book_id=int(input("Enter the book id: "))
        # name
        cr.execute("select book_name from books where book_id=%s",(book_id,))
        name=cr.fetchone()[0]

        # current borrower
        result=currentBorrower(book_id)
        if result:
            print(f"""
Current Borrower
Member id: {result[0]}
Member name: {result[1]}
""")
        else:
            print("The book is not currently borrowed.")

        print()

        # transaction history
        cr.execute("select transaction_id, members.member_id, member_name, issue_date, return_date from transactions, members where members.member_id=transactions.member_id and book_id=%s order by issue_date", (book_id,))
        transaction_history=cr.fetchall()
        headers=["Transaction ID", "Member Id", "Member Name", "Issue Date", "Return Date"]

        print("Transaction History:")
        print(tabulate(transaction_history, headers=headers, tablefmt=cellstyle))

    # Member Info
    elif choice==9:
        member_id=int(input("Enter the member id: "))

        # name
        cr.execute("select member_name from members where member_id=%s",(member_id,))
        name=cr.fetchone()[0]
        print("Name:", name)
        print("Current Tier:", is_active_member(member_id))

        print()

        print("Transaction History: ")
        cr.execute("select transaction_id, books.book_id, book_name, issue_date, return_date from transactions, books where books.book_id=transactions.book_id and member_id=%s order by issue_date", (member_id, ))
        transaction_history=cr.fetchall()
        headers=["Transaction ID", "Book ID", "Book Name", "Issue Date", "Return Date"]
        print(tabulate(transaction_history, headers=headers, tablefmt=cellstyle))
        
        print()

        print("Membership History: ")
        cr.execute("select payment_id, tier, payment_date, coverage_start, expiry_date from membership_payments where member_id=%s", (member_id, ))
        membership_history=cr.fetchall()
        headers=["Payment ID", "Tier", "Payment Date", "Coverage Start", "Expiry Date"]
        print(tabulate(membership_history, headers=headers, tablefmt=cellstyle))

    # Membership Info
    elif choice==10:
        active_membership_info = active_members() # returns list of all (member_id, tier, expiry_date)
        active_member_ids=[]
        if not active_membership_info:
            print("No members currently have an active membership.")
        else:
            rows = []
            for member_id, tier, expiry_date in active_membership_info:
                cr.execute("select member_name from members where member_id=%s", (member_id,))
                member_name = cr.fetchone()[0]
                rows.append([member_id, member_name, tier, expiry_date])
                active_member_ids.append(member_id)

            headers = ["Member ID", "Member Name", "Tier", "Membership Expiry Date"]
            print("Active members:")
            print(tabulate(rows, headers=headers, tablefmt="grid"))

        cr.execute("select member_id, member_name from members")
        all_members=cr.fetchall()
        inactive_members=[]
        for member_id, member_name in all_members:
            if member_id not in active_member_ids: # member doesn't have a membership
                inactive_members.append([member_id, member_name])

        print("Members without membership:")
        if inactive_members:
            print(tabulate(inactive_members, headers=["Member ID", "Member Name"], tablefmt=cellstyle))
        else:
            print("All members have an active membership.")

    # Pending Fines
    elif choice==11:
        # condition paid=0 indicates unpaid fines
        cr.execute("select fine_id, member_name, book_name, fine_type, amount from fines, transactions, members, books where paid=0 and members.member_id=transactions.member_id and transactions.transaction_id=fines.transaction_id and transactions.book_id=books.book_id")
        pending_fines=cr.fetchall()
        headers=["Fine ID", "Member Name", "Book Name", "Fine Type", "Amount (Rs.)"]
        if not pending_fines:
            print("No fines are currently pending.")
        else:
            print("Pending fines:")
            print(tabulate(pending_fines, headers=headers, tablefmt=cellstyle))

    # Issued Books
    elif choice==12:
        cr.execute("select transaction_id, book_name, member_name, issue_date, due_date from books, members, transactions where return_date is null and transactions.book_id=books.book_id and transactions.member_id=members.member_id")
        issued_books=cr.fetchall()
        headers=["Transaction ID", "Book Name", "Member Name", "Issue Date", "Due Date"]
        if not issued_books:
            print("No books are currently issued.")
        else:
            print("Issued books:")
            print(tabulate(issued_books, headers=headers, tablefmt=cellstyle))

    # Overdue Books
    elif choice==13:
        cr.execute("select transaction_id, book_name, member_name, due_date from books, members, transactions where return_date is null and due_date < curdate() and transactions.member_id=members.member_id and transactions.book_id=books.book_id")
        overdue_books=cr.fetchall()

        cr.execute("select curdate()")
        print("Today:", cr.fetchone()[0].strftime("%Y-%m-%d"))

        headers=["Transaction ID", "Book Name", "Member Name", "Due Date"]
        if not overdue_books:
            print("No books are currently overdue.")
        else:
            print("Overdue books:")
            print(tabulate(overdue_books, headers=headers, tablefmt=cellstyle))

    elif choice==14:
        top_ten_books()

    elif choice==15:
        top_ten_members()

    elif choice==16:
        membership_chart()

    elif choice==17:
        genre_chart()

    # Custom Query (depreciate)
    elif choice==18:
        query=input("Enter your custom SELECT query: ")
        if query.strip().lower().startswith("select"):
            try:
                cr.execute(query)
                rows = cr.fetchall()
                for record in rows: # row is a tuple and str(item) for each item in that tuple automatically converts NULL to None and datetime objects to readable strings
                    formatted_values=[]
                    for item in record:
                        formatted_values.append(str(item))
                    line=" | ".join(formatted_values)
                    print(line)
            except Exception as e:
                print(e)
        else:
            print("Only SELECT statements are allowed for safety.")

    # Database Schema (depreciate)
    elif choice==19:
        cr.execute("show tables")
        tables = cr.fetchall()
                
        for table in tables:
            table_name = table[0]
            print()
            print(f"--- {table_name} ---")
            cr.execute(f"desc {table_name}")
            columns = cr.fetchall()
            for col in columns:
                print(f" {col[0]} ({col[1]})")

    # Exits program closes the cursor, connection and breaks the loop
    elif choice==20:
        print("Exiting program...")
        cr.close()
        connect.close()
        run=False
        break

    # A break before the loop continues to ensure readability in the CLI 
    if choice != 20:
        input("\nPress Enter to continue...")

"""
TO DO:
1. Remove membership pie chart from seperate menu options and change to y/n would you like to see pie chart from within membership info menu
2. Query to list books due today
3. Comment out custom options and database schema
4. Add credits option
"""