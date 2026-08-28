from db import connect, cr #, next_id
# import db automatically runs the db file and create database is called

from books import add_books, currentBorrower, search_books #, is_available
from members import add_members, active_members, is_active_member, pay_membership #, no_of_books_issued_to
# from dates import is_late, add_date
from constants import intro_message #, fines, loan_period, max_books, tier_prices, membership_duration
from transactions import issue_book, settle_fines, return_book
from graphing import top_ten_books, top_ten_members, membership_chart, genre_chart

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
16. Membership Split - See a pie chart of what memberships members have
17. Genre Diagram - See a pie chart of the genre's available
18. Custom Query - Enter your own custom SELECT query
          
19. See Database Schema                  
20. Exit
""")
    choice=input("Enter the number: ")
    try:
        choice=int(choice)
    except ValueError:
        print("Try Again!")
        continue

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
        search_books()
        
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
        print("Transaction History:")
        for record in transaction_history: # row is a tuple and str(item) for each item in that tuple automatically converts NULL to None and datetime objects to readable strings
            print(f"transaction id: {record[0]} | member id: {record[1]} | {record[2]} | loan period: {record[3]} -> {record[4]}")

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
        for record in transaction_history: # row is a tuple and str(item) for each item in that tuple automatically converts NULL to None and datetime objects to readable strings
            print(f"transaction id: {record[0]} | book id: {record[1]} | {record[2]} | loan period: {record[3]} -> {record[4]}")
        
        print()

        print("Membership History: ")
        cr.execute("select payment_id, tier, payment_date, coverage_start, expiry_date from membership_payments where member_id=%s", (member_id, ))
        membership_history=cr.fetchall()

        for record in membership_history:
            print(f"payment id: {record[0]} | {record[1]} | paid on: {record[2]} | validity: {record[3]} -> {record[4]}")
    
    elif choice==10:
        active_membership_info = active_members() # returns list of all (member_id, tier, expiry_date)
        active_member_ids=[]
        if not active_membership_info:
            print("No members currently have an active membership.")
        else:
            print("Active members:")
            for member_id, tier, expiry_date in active_membership_info:
                cr.execute("select member_name from members where member_id=%s", (member_id,))
                member_name = cr.fetchone()[0]
                print(f"member id: {member_id} | {member_name} | {tier} | expires: {expiry_date}")
                active_member_ids.append(member_id)
        
        cr.execute("select member_id, member_name from members")
        all_members=cr.fetchall()
        
        print("Members without membership:")
        for member_id, member_name in all_members:
            if member_id not in active_member_ids: # member doesn't have a membership
                print(f"member id: {member_id} | {member_name}")
        
    elif choice==11:
        cr.execute("select fine_id, member_name, book_name, fine_type, amount from fines, transactions, members, books where paid=0 and members.member_id=transactions.member_id and transactions.transaction_id=fines.transaction_id and transactions.book_id=books.book_id")
        pending_fines=cr.fetchall()

        if not pending_fines:
            print("No fines are currently pending.")
        else:
            print("Pending fines:")
            for fine in pending_fines:
                print(f"fine id: {fine[0]} | {fine[1]} | {fine[2]} | {fine[3]} | Rs.{fine[4]}")

    elif choice==12:
        cr.execute("select transaction_id, book_name, member_name, issue_date, due_date from books, members, transactions where return_date is null and transactions.book_id=books.book_id and transactions.member_id=members.member_id")
        issued_books=cr.fetchall()

        if not issued_books:
            print("No books are currently issued.")
        else:
            print("Issued books:")
            for book in issued_books:
                print(f"transaction id: {book[0]} | {book[1]} | {book[2]} | loan period: {book[3]} -> {book[4]}")

    elif choice==13:
        cr.execute("select transaction_id, book_name, member_name, due_date from books, members, transactions where return_date is null and due_date < curdate() and transactions.member_id=members.member_id and transactions.book_id=books.book_id")
        overdue_books=cr.fetchall()

        if not overdue_books:
            print("No books are currently overdue.")
        else:
            print("Overdue books:")
            for book in overdue_books:
                print(f"transaction id: {book[0]} | {book[1]} | {book[2]} | due date: {book[3]}")

    elif choice==14:
        top_ten_books()

    elif choice==15:
        top_ten_members()

    elif choice==16:
        membership_chart()

    elif choice==17:
        genre_chart()

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
            except Exception:
                print(Exception)
        else:
            print("Only SELECT statements are allowed for safety.")

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

    elif choice==20:
        print("Exiting program...")
        cr.close()
        connect.close()
        run=False
        break
    
    if choice != 20:
        input("\nPress Enter to continue...")