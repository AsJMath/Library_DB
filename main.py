### main.py

# FILES
import db # import db automatically runs the db file and db.create database is called
import books
import members
import constants
import graphing
import transactions
import utils
import mailer # for draft_group_email function

# MODULES
from tabulate import tabulate

# Refreshes the presence [!!] flags 
def refresh_presence_flags():
    db.cr.execute("select 1 from books limit 1")
    books_present = db.cr.fetchone() is not None
    db.cr.execute("select 1 from members limit 1")
    members_present = db.cr.fetchone() is not None
    return books_present, members_present

is_books_present, is_members_present = refresh_presence_flags()

utils.fancy_print(constants.intro_message)
utils.buffer()
run=True
# Entire while loop CLI (with all input statements i.e. possible failure points) wrapped in try-except to allow for Keyboard Interrupt
try:
    while run:
        # Indicator System
        pending_fines_list = transactions.pending_fines()
        issued_books_list = books.issued_books()
        due_today_list = books.due_today_books()
        overdue_books_list = books.overdue_books()

        pending_fines_indicator = constants.indicator if pending_fines_list else ""
        issued_books_indicator = constants.indicator if issued_books_list else ""
        due_today_books_indicator = constants.indicator if due_today_list else ""
        overdue_books_indicator = constants.indicator if overdue_books_list else ""

        print(f"""
Choose an option
$ Actions
1. Add books
2. Edit books
3. Delete books
4. Add members
5. Delete members
6. Issue book
7. Return book
8. Settle Fines
9. Pay Membership

$ Information
10. Generic Search - Search books by book, author or genre
11. Book Info - Information about the book, current borrower and its transaction history
12. Member Info - Information about the member, membership status and their transaction history
13. Membership Info - Information about all members and their membership status
14. Pending Fines{pending_fines_indicator} - List of all pending fines
15. Issued Books{issued_books_indicator} - List of all books out of the library
16. Due Today{due_today_books_indicator} - List of all book due today
17. Overdue Books{overdue_books_indicator} - List all books overdue
18. Tier Info - List all the tiers and their benefits
19. Books - View the entire books list
20. Members - View the entire members list

$ Charts
21. Top 10 Books - Top 10 list of most issued books
22. Top 10 Members - Top 10 list of members who issue books most
23. Membership Chart - See a pie chart of what memberships members have
24. Genre Chart - See a pie chart of the genre's available
25. Revenue Source Chart - See a pie chart of the revenue the library generates from each source

$ Other
26. Exit
27. Custom Query - Enter your own custom SELECT query
28. See Database Schema
29. Clear all data
""")

        num_choice=input("Enter the number: ")
        if num_choice=="who made this":
            utils.fancy_print(constants.credits_message)
            utils.buffer()
            continue

        # Handles stray values that are not integers or that are not within the valid ranges
        try:
            num_choice=int(num_choice)
        except ValueError:
            utils.fancy_print("Try Again!")
            continue # forces the next iteration of the loop

        if num_choice not in range(1,30):
            utils.fancy_print("Try again with a number from 1 to 29.")

        elif num_choice==1:
            books.add_book()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==2 and is_books_present:
            books.edit_book()

        elif num_choice==3 and is_books_present:
            books.delete_book()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==4:
            members.add_member()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==5 and is_members_present:
            members.delete_member()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==6 and is_books_present and is_members_present:
            transactions.issue_book()

        elif num_choice==7 and is_books_present and is_members_present:
            transactions.return_book()

        elif num_choice==8 and is_books_present and is_members_present:
            transactions.settle_fines()

        elif num_choice==9 and is_members_present:
            members.pay_membership()

        elif num_choice==10 and is_books_present:
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
                books.query_books_by_name()

            elif method==2:
                target_genre=books.query_books_by_genre() # query_books_by_genre function gets executed and the return value gets stored in the target_genre
                show_chart=input("Would you like to see a piechart of the book genres? (y/n): ").lower()
                if show_chart.startswith("y"):
                    graphing.genre_chart(target_genre)

        # Book Info
        elif num_choice==11 and is_books_present:
            matches, choices, book_ids = books.query_books_by_name(active_only=False) # Gives the option to view the books even if they are inactive
            print()

            if not matches:
                # Two cases for no matches, both handled with print statements within query_books_by_name
                continue

            book_id_input = input("Enter the book id to view: ")
            try:
                book_id = int(book_id_input)
            except ValueError:
                print("Invalid input.")
                continue

            if book_id not in book_ids:
                print("Please enter a book id from the search results.")
                continue

            # name
            db.cr.execute("select book_name from books where book_id=%s",(book_id,))
            name=db.cr.fetchone()[0]

            # True by default but becomes optional if the book is found to be deleted
            show_info=True
            active=books.book_exists(book_id)
            if not active:
                deleted_choice=input(f"'{name}' is no longer part of the library catalog. Enter if you still want to see its information (y/n): ").lower()
                show_info = deleted_choice.startswith("y")

            if show_info:
                # current borrower
                result=books.current_borrower(book_id)
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
                db.cr.execute("select transaction_id, members.member_id, member_name, issue_date, return_date from transactions, members where members.member_id=transactions.member_id and book_id=%s order by issue_date", (book_id,))
                transaction_history=db.cr.fetchall()
                headers=["Transaction ID", "Member Id", "Member Name", "Issue Date", "Return Date"]

                print("Transaction History:")
                print(tabulate(transaction_history, headers=headers, tablefmt=constants.cellstyle))

        # Member Info
        elif num_choice==12 and is_members_present:
            matches, choices, member_ids = members.query_by_member_name()
            print()

            if not matches:
                # Two cases for no matches, both handled with print statements within query_books_by_name
                continue

            member_id_input = input("Enter the member id to view: ")
            try:
                member_id = int(member_id_input)
            except ValueError:
                print("Invalid input.")
                continue

            if member_id not in member_ids:
                print("Please enter a member id from the search results.")
                continue

            # name
            db.cr.execute("select member_name from members where member_id=%s",(member_id,))
            name=db.cr.fetchone()[0]
            print("Name:", name)
            print("Current Tier:", members.is_active_member(member_id))

            print()

            # Transaction History
            db.cr.execute("select transaction_id, books.book_id, book_name, issue_date, return_date from transactions, books where books.book_id=transactions.book_id and member_id=%s order by issue_date", (member_id, ))
            transaction_history=db.cr.fetchall()
            if transaction_history:
                print("Transaction History: ")
                headers=["Transaction ID", "Book ID", "Book Name", "Issue Date", "Return Date"]
                print(tabulate(transaction_history, headers=headers, tablefmt=constants.cellstyle))
            else:
                print("No existing transactions.")

            print()

            # Membership History
            db.cr.execute("select payment_id, tier, payment_date, coverage_start, expiry_date from membership_payments where member_id=%s", (member_id, ))
            membership_history=db.cr.fetchall()
            if membership_history:
                print("Membership History: ")
                header=["Payment ID", "Tier", "Payment Date", "Coverage Start", "Expiry Date"]
                print(tabulate(membership_history, headers=header, tablefmt=constants.cellstyle))
            else:
                print("No existing membership history.")
           
            print()

            # Pending Fines
            db.cr.execute("select fines.transaction_id, books.book_name, fine_type, amount, transactions.due_date from fines, transactions, books where fines.transaction_id=transactions.transaction_id and transactions.book_id=books.book_id and member_id=%s and paid=0", (member_id,))
            pending_fine_history=db.cr.fetchall()
            if pending_fine_history:
                print("Pending Fine History:")
                header=["Transaction ID", "Book Name", "Fine Type", "Amount", "Due Date"]
                print(tabulate(pending_fine_history, headers=header, tablefmt=constants.cellstyle))

            show_fine_history=input("Do you want to see the full fine history? (y/n): ").lower()
            if show_fine_history.startswith("y"):
                # Fine History
                print()
                db.cr.execute("select fines.transaction_id, books.book_name, fine_type, amount, transactions.due_date, paid from fines, transactions, books where fines.transaction_id=transactions.transaction_id and transactions.book_id=books.book_id and member_id=%s", (member_id,))
                fine_history=db.cr.fetchall()
                if fine_history:
                    print("Fine History: ")
                    header=["Transaction_ID", "Book Name", "Fine Type", "Amount (Rs.)", "Date of Fine", "Status"]
                    print(tabulate(fine_history, headers=header, tablefmt=constants.cellstyle))

        # Membership Info
        elif num_choice==13 and is_members_present:
            active_membership_info = members.active_members() # returns list of all (member_id, tier, expiry_date)
            active_member_ids=[]
            if not active_membership_info:
                print("No members currently have an active membership.")
            else:
                rows = []
                for member_id, tier, expiry_date in active_membership_info:
                    db.cr.execute("select member_name from members where member_id=%s", (member_id,))
                    member_name = db.cr.fetchone()[0]
                    rows.append([member_id, member_name, tier, expiry_date])
                    active_member_ids.append(member_id)

                headers = ["Member ID", "Member Name", "Tier", "Membership Expiry Date"]
                print("Active members:")
                print(tabulate(rows, headers=headers, tablefmt=constants.cellstyle))

            db.cr.execute("select member_id, member_name from members")
            all_members=db.cr.fetchall()
            inactive_members=[]
            for member_id, member_name in all_members:
                if member_id not in active_member_ids: # member doesn't have a membership
                    inactive_members.append([member_id, member_name])
            print()
            print("Members without membership:")
            if inactive_members:
                print(tabulate(inactive_members, headers=["Member ID", "Member Name"], tablefmt=constants.cellstyle))
            else:
                print("All members have an active membership.")

            chart_choice=input("Would you like to see a pie chart of the memberships? (y/n): ").lower()
            if chart_choice.startswith("y"):
                graphing.membership_chart()

        # Pending Fines
        elif num_choice==14 and is_members_present and is_books_present:
            # condition paid=0 indicates unpaid fines
            if not pending_fines_list:
                print("No fines are currently pending.")
            else:
                headers=["Fine ID", "Member Name", "Book Name", "Fine Type", "Amount (Rs.)"]
                print("Pending fines:")
                print(tabulate(pending_fines_list, headers=headers, tablefmt=constants.cellstyle))

        # Issued Books - All issued books including overdue books
        elif num_choice==15 and is_books_present and is_members_present:
            if not issued_books_list:
                print("No books are currently issued.")
            else:
                headers=["Transaction ID", "Book Name", "Member Name", "Issue Date", "Due Date"]
                print("Issued books:")
                print(tabulate(issued_books_list, headers=headers, tablefmt=constants.cellstyle))

        # Due Today
        elif num_choice==16 and is_books_present and is_members_present:
            if not due_today_list:
                print("No books due today.")
            else: # Books due today exist in the database
                db.cr.execute("select curdate()")
                print("Today:", db.cr.fetchone()[0].strftime("%Y-%m-%d"))

                headers=["Transaction ID", "Book Name", "Member ID", "Member Name", "Issue Date"]
                print("Books Due Today:")
                print(tabulate(due_today_list, headers=headers, tablefmt=constants.cellstyle))

                mail_due_choice=input("Enter to send an email to all the members (y/n): ").lower()
                if mail_due_choice.startswith("y"):
                    mailer.draft_group_emails(due_today_list, "Books Due Today", case="due today")

        # Overdue Books
        elif num_choice==17 and is_books_present and is_members_present:
            if not overdue_books_list:
                print("No books are currently overdue.")
            else:
                db.cr.execute("select curdate()")
                print("Today:", db.cr.fetchone()[0].strftime("%Y-%m-%d"))

                headers=["Transaction ID", "Book Name", "Member ID", "Member Name", "Due Date", "Days Delayed"]
                print("Overdue books:")
                print(tabulate(overdue_books_list, headers=headers, tablefmt=constants.cellstyle))

                mail_overdue_choice=input("Enter to send an email to all the members (y/n): ").lower()
                if mail_overdue_choice.startswith("y"):
                    mailer.draft_group_emails(overdue_books_list, "Overdue Books Notice", case="overdue")

        # Tier Information - Tabulated data comparing the tiers
        elif num_choice==18:
            headers = ["Tier", "Price (Rs.)", "Maximum Books", "Loan Period (days)"]
            print(tabulate(constants.tier_info, headers=headers, tablefmt=constants.cellstyle))

        # All active books
        elif num_choice==19 and is_books_present:
            db.cr.execute("select book_id, book_name, publication_date, genre, author_name from books where active=1")
            result=db.cr.fetchall()
            if result:
                print("Existing Books:")
                print(tabulate(result, ["Book ID", "Book Name", "Publication Date", "Genre", "Author Name"], tablefmt=constants.cellstyle))
            else:
                print("No books in the current catalog. Add new books to use this functionality.")

        # All members
        elif num_choice==20 and is_members_present:
            db.cr.execute("select * from members")
            result=db.cr.fetchall()
            if result:
                print("Members:")
                print(tabulate(result, ["Member ID", "Member Name", "Email Address"], tablefmt=constants.cellstyle))
            else:
                print("No members in the library currently. Add new members to use this functionality.")

        elif num_choice==21 and is_books_present:
            graphing.top_ten_books()

        elif num_choice==22 and is_members_present:
            graphing.top_ten_members()

        elif num_choice==23:
            graphing.membership_chart()

        elif num_choice==24 and is_books_present:
            graphing.genre_chart()

        elif num_choice==25:
            graphing.revenue_source_chart()

        # Exits program closes the cursor, connection and breaks the loop
        elif num_choice==26:
            run=False
            db.quit()
            break

        # Custom Query
        elif num_choice==27:
            query=input("Enter your custom SELECT query: ")
            if query.strip().lower().startswith("select"):
                try:
                    db.cr.execute(query)
                    rows = db.cr.fetchall()
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

        # Database Schema
        elif num_choice==28:
            db.cr.execute("show tables")
            tables = db.cr.fetchall()

            for table in tables:
                table_name = table[0]
                print()
                print(f"--- {table_name} ---")
                db.cr.execute(f"desc {table_name}")
                columns = db.cr.fetchall()
                for col in columns:
                    print(f" {col[0]} ({col[1]})")

        # Clear all data
        elif num_choice==29:
            db.wipe_data()

        if not is_books_present and is_members_present:
            print("\nSome functions cannot be accessed without adding books.")

        if not is_members_present and is_books_present:
            print("\nSome functions cannot be accessed without adding members.")

        if not is_members_present and not is_books_present:
            print("\nSome functions cannot be accessed without adding books and members.")

        # A break before the loop continues to ensure readability in the CLI
        if num_choice != 26:
            utils.buffer()

except KeyboardInterrupt:
    utils.fancy_print("\nKeyboard Interrupt detected.")
    run=False
    db.quit()