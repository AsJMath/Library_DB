# FILES
from db import connect, cr, quit
# import db automatically runs the db file and create database is called
from books import add_books, delete_book, current_borrower, query_books_by_genre, query_books_by_name, book_exists, issued_books, due_today_books, overdue_books
from members import add_members, active_members, is_active_member, pay_membership, query_by_member_name
from constants import intro_message, cellstyle, tier_info, credits_message
from transactions import issue_book, settle_fines, return_book, pending_fines
from graphing import top_ten_books, top_ten_members, membership_chart, genre_chart, revenue_source_chart
import mailer # for draft_group_email function

# MODULES
from tabulate import tabulate

cr.execute("select * from books")
is_books_present=cr.fetchall()
cr.execute("select * from members")
is_members_present=cr.fetchall()

print(intro_message)
run=True
try:
    while run:   
        # Indicator System
        pending_fines_list = pending_fines()
        issued_books_list = issued_books()
        due_today_list = due_today_books()
        overdue_books_list = overdue_books()

        indicator=" [!!]"
        pending_fines_indicator = indicator if pending_fines_list else ""
        issued_books_indicator = indicator if issued_books_list else ""
        due_today_books_indicator = indicator if due_today_list else ""
        overdue_books_indicator = indicator if overdue_books_list else ""

        print(f"""
Choose an option
$ Actions
1. Add books
2. Delete books
3. Add members
4. Issue book
5. Return book
6. Settle Fines
7. Pay Membership

$ Information
8. Generic Search - Search books by book, author or genre      
9. Book Info - Information about the book, current borrower and its transaction history
10. Member Info - Information about the member, membership status and their transaction history
11. Membership Info - Information about all members and their membership status
12. Pending Fines{pending_fines_indicator} - List of all pending fines
13. Issued Books{issued_books_indicator} - List of all books out of the library
14. Due Today{due_today_books_indicator} - List of all book due today
15. Overdue Books{overdue_books_indicator} - List all books overdue
16. Tier Info - List all the tiers and their benefits
17. Books - View the entire books list
18. Members - View the entire members list

$ Charts
19. Top 10 Books - Top 10 list of most issued books
20. Top 10 Members - Top 10 list of members who issue books most
21. Membership Chart - See a pie chart of what memberships members have
22. Genre Chart - See a pie chart of the genre's available
23. Revenue Source Chart - See a pie chart of the revenue the library generates from each source
24. Exit

$ Advanced
25. Custom Query - Enter your own custom SELECT query          
26. See Database Schema                  
""")
        
        num_choice=input("Enter the number: ")
        if num_choice=="credits":
            print(credits_message)
            input("\nPress Enter to continue...")
            continue

        # Handles stray values that are not integers or that are not within the valid ranges
        try:
            num_choice=int(num_choice)
        except ValueError:
            print("Try Again!")
            continue # forces the next iteration of the loop

        if num_choice not in range(1,27):
            print("Try again with a number from 1 to 24")

        elif num_choice==1:
            add_books()

        elif num_choice==2 and is_books_present:
            delete_book()

        elif num_choice==3:
            add_members()

        elif num_choice==4 and is_books_present and is_members_present:
            issue_book()

        elif num_choice==5 and is_books_present and is_members_present:
            return_book()

        elif num_choice==6 and is_books_present and is_members_present:
            settle_fines()

        elif num_choice == 7 and is_members_present:
            pay_membership()

        elif num_choice==8 and is_books_present:
            # while loop handles stray values for the method input
            while True:
                method=input("""
    Available Methods of Search
    1. Title/Author
    2. Genre
    Enter the method of search: """)
                try:
                    method=int(method)
                except ValueError:
                    print("Enter either 1 or 2.")
                    continue

                if method in range(1,3):
                    break
                else:
                    print("Enter either 1 or 2.")

            if method==1:
                query_books_by_name()

            elif method==2:
                target_genre=query_books_by_genre() # query_books_by_genre function gets executed and the return value gets stored in the target_genre
                show_chart=input("Would you like to see a piechart of the book genres (y/n): ").lower()
                if show_chart.startswith("y"):
                    genre_chart(target_genre)

        # Book Info    
        elif num_choice==9 and is_books_present:
            while True:
                matches, choices, book_ids = query_books_by_name(active_only=False)
                print()
                book_id = int(input("Enter the book id to view or enter 0 to search again: "))
                if book_id==0:
                    continue
                elif book_id not in book_ids:
                    print("Please enter a book id from the above list.")
                else:
                    break

            # name
            cr.execute("select book_name from books where book_id=%s",(book_id,))
            name=cr.fetchone()[0]

            # True by default but becomes optional if the book is found to be deleted
            show_info=True
            active=book_exists(book_id)
            if not active:
                deleted_choice=input(f"'{name}' is no longer part of the library catalog. Enter if you still want to see its information (y/n): ").lower()
                show_info = deleted_choice.startswith("y")

            if show_info:
                # current borrower
                result=current_borrower(book_id)
                if result:
                    print(f"""
    Current Borrower
    Member id: {result[0]}
    Member name: {result[1]}
    Due: {result[2]}""")
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
        elif num_choice==10 and is_members_present:
            while True:
                matches, choices, member_ids = query_by_member_name()
                print()
                member_id = int(input("Enter the member id to view or enter 0 to search again: "))
                if member_id==0:
                    continue
                elif member_id not in member_ids:
                    print("Please enter a member id frmo the above list.")
                else:
                    break
            
            # name
            cr.execute("select member_name from members where member_id=%s",(member_id,))
            name=cr.fetchone()[0]
            print("Name:", name)
            print("Current Tier:", is_active_member(member_id))

            print()

            cr.execute("select transaction_id, books.book_id, book_name, issue_date, return_date from transactions, books where books.book_id=transactions.book_id and member_id=%s order by issue_date", (member_id, ))
            transaction_history=cr.fetchall()
            if transaction_history:
                print("Transaction History: ")
                headers=["Transaction ID", "Book ID", "Book Name", "Issue Date", "Return Date"]
                print(tabulate(transaction_history, headers=headers, tablefmt=cellstyle))
            else:
                print("No existing transactions.")
            
            print()

            
            cr.execute("select payment_id, tier, payment_date, coverage_start, expiry_date from membership_payments where member_id=%s", (member_id, ))
            membership_history=cr.fetchall()
            if membership_history:
                print("Membership History: ")
                headers=["Payment ID", "Tier", "Payment Date", "Coverage Start", "Expiry Date"]
                print(tabulate(membership_history, headers=headers, tablefmt=cellstyle))
            else:
                print("No existing membership history.")
            
        # Membership Info
        elif num_choice==11 and is_members_present:
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
                print(tabulate(rows, headers=headers, tablefmt=cellstyle))

            cr.execute("select member_id, member_name from members")
            all_members=cr.fetchall()
            inactive_members=[]
            for member_id, member_name in all_members:
                if member_id not in active_member_ids: # member doesn't have a membership
                    inactive_members.append([member_id, member_name])
            print()
            print("Members without membership:")
            if inactive_members:
                print(tabulate(inactive_members, headers=["Member ID", "Member Name"], tablefmt=cellstyle))
            else:
                print("All members have an active membership.")

            chart_choice=input("Would you like to see a pie chart of the memberships (y/n): ").lower()
            if chart_choice.startswith("y"):
                membership_chart()

        # Pending Fines
        elif num_choice==12 and is_members_present and is_books_present:
            # condition paid=0 indicates unpaid fines
            if not pending_fines_list:
                print("No fines are currently pending.")
            else:
                headers=["Fine ID", "Member Name", "Book Name", "Fine Type", "Amount (Rs.)"]
                print("Pending fines:")
                print(tabulate(pending_fines_list, headers=headers, tablefmt=cellstyle))

        # Issued Books - All issued books including overdue books
        elif num_choice==13 and is_books_present and is_members_present:
            if not issued_books_list:
                print("No books are currently issued.")
            else:
                headers=["Transaction ID", "Book Name", "Member Name", "Issue Date", "Due Date"]
                print("Issued books:")
                print(tabulate(issued_books_list, headers=headers, tablefmt=cellstyle))

        # Due Today
        elif num_choice==14 and is_books_present and is_members_present:
            if not due_today_list:
                print("No books due today.")
            else: # Books due today exist in the database
                cr.execute("select curdate()")
                print("Today:", cr.fetchone()[0].strftime("%Y-%m-%d"))

                headers=["Transaction ID", "Book Name", "Member ID", "Member Name", "Issue Date"]
                print("Books Due Today:")
                print(tabulate(due_today_list, headers=headers, tablefmt=cellstyle))

                mail_due_choice=input("Enter to send an email to all the members (y/n): ").lower()
                if mail_due_choice.startswith("y"):
                    mailer.draft_group_emails(due_today_list, "Books Due Today", case="due today")    

        # Overdue Books
        elif num_choice==15 and is_books_present and is_members_present:
            if not overdue_books_list:
                print("No books are currently overdue.")
            else:
                cr.execute("select curdate()")
                print("Today:", cr.fetchone()[0].strftime("%Y-%m-%d"))

                headers=["Transaction ID", "Book Name", "Member ID", "Member Name", "Due Date", "Days Delayed"]            
                print("Overdue books:")
                print(tabulate(overdue_books_list, headers=headers, tablefmt=cellstyle))

                mail_overdue_choice=input("Enter to send an email to all the members (y/n): ").lower()
                if mail_overdue_choice.startswith("y"):
                    mailer.draft_group_emails(overdue_books_list, "Overdue Books Notice", case="overdue")

        # Tier Information - Tabulated data comparing the tiers
        elif num_choice==16:
            headers = ["Tier", "Price (Rs.)", "Maximum Books", "Loan Period (days)"]
            print(tabulate(tier_info, headers=headers, tablefmt=cellstyle))

        # All active books
        elif num_choice==17 and is_books_present:
            cr.execute("select book_id, book_name, publication_date, genre, author_name from books where active=1")
            result=cr.fetchall()
            if result:
                print("Existing Books:")
                print(tabulate(result, ["Book ID", "Book Name", "Publication Date", "Genre", "Author Name"], tablefmt=cellstyle))
            else:
                print("No books in the current catalog. Add new books to use this functionality.")

        # All members
        elif num_choice==18 and is_members_present:
            cr.execute("select * from members")
            result=cr.fetchall()
            if result:
                print("Members:")
                print(tabulate(result, ["Member ID", "Member Name", "Email Address"], tablefmt=cellstyle))
            else:
                print("No members in the library currently. Add new members to use this functionality.")

        elif num_choice==19 and is_books_present:
            top_ten_books()

        elif num_choice==20 and is_members_present:
            top_ten_members()

        elif num_choice==21:
            membership_chart()

        elif num_choice==22 and is_books_present:
            genre_chart()

        elif num_choice==23:
            revenue_source_chart()

        # Exits program closes the cursor, connection and breaks the loop
        elif num_choice==24:
            quit(run_variable=run)
            break

        # TODO: Depriciate
        # Custom Query
        elif num_choice==25:
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

        #TODO: Depriciate
        # Database Schema
        elif num_choice==26:
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

        if not is_books_present and is_members_present:
            print("Some functions cannot be accessed without adding books.")

        if not is_members_present and is_books_present:
            print("Some functions cannot be accessed without adding members.")

        if not is_members_present and not is_books_present:
            print("Some functions cannot be accessed without adding books and members.")
        
        # A break before the loop continues to ensure readability in the CLI 
        if num_choice != 24:
            input("\nPress Enter to continue...")

except KeyboardInterrupt:
    print("\nKeyboard Interrupt detected.")
    quit(run_variable=run)
