### main.py

# FILES
# All import statements run the respective files they import. All the files below consist of function definitions and no function calls except db.py, which calls the db.create_database() function, creating a database if it doesn't exist.
import db
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
# Refreshed on startup and whenever actions that change the data to either of books or members are executed via the CLI
def refresh_presence_flags():
    db.cr.execute("select 1 from books limit 1")
    books_present = db.cr.fetchone() is not None
    db.cr.execute("select 1 from members limit 1")
    members_present = db.cr.fetchone() is not None
    return books_present, members_present

is_books_present, is_members_present = refresh_presence_flags()

# Which options need books and/or members to exist: option number: (needs_books?, needs_members?)
requirements = {
    2: (True, False),
    3: (True, False),
    5: (False, True),
    6: (False, True),
    7: (True, True),
    8: (True, True),
    9: (True, True),
    10: (False, True),
    11: (True, False),
    12: (True, False),
    13: (False, True),
    14: (False, True),
    15: (True, True),
    16: (True, True),
    17: (True, True),
    18: (True, True),
    22: (True, False),
    23: (False, True),
    25: (True, False),
}

# Prints the intro message
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
5. Edit members
6. Delete members
7. Issue book
8. Return book
9. Settle Fines
10. Pay Membership

$ Information
11. Generic Search - Search books by book, author or genre
12. Book Info - Information about the book, current borrower and its transaction history
13. Member Info - Information about the member, membership status and their transaction history
14. Membership Info - Information about all members and their membership status
15. Pending Fines{pending_fines_indicator} - List of all pending fines
16. Issued Books{issued_books_indicator} - List of all books out of the library
17. Due Today{due_today_books_indicator} - List of all book due today
18. Overdue Books{overdue_books_indicator} - List all books overdue
19. Tier Info - List all the tiers and their benefits
20. Books - View the entire books list
21. Members - View the entire members list

$ Charts
22. Top 10 Books - Top 10 list of most issued books
23. Top 10 Members - Top 10 list of members who issue books most
24. Membership Chart - See a pie chart of what memberships members have
25. Genre Chart - See a pie chart of the genre's available
26. Revenue Source Chart - See a pie chart of the revenue the library generates from each source

$ Other
27. Custom Query - Enter your own custom SELECT query
28. See Database Schema
29. Clear all data
Type 'exit' to quit the program.
""")

        num_choice=input("Type your choice: ").strip().lower()
        if num_choice=="who made this":
            utils.fancy_print(constants.credits_message)
            utils.buffer()
            continue
        elif num_choice=="exit":
            run=False
            db.quit()
            break

        # Handles stray values that are not integers or that are not within the valid ranges
        try:
            num_choice=int(num_choice)
        except ValueError:
            utils.fancy_print("Try Again!")
            utils.buffer()
            continue # forces the next iteration of the loop

        blocked=False
        if num_choice in requirements:
            needs_books, needs_members = requirements[num_choice]
            missing_books = needs_books and not is_books_present
            missing_members = needs_members and not is_members_present

            if missing_books and missing_members:
                utils.fancy_print("This function cannot be accessed without adding books and members.")
                blocked = True
            elif missing_books:
                utils.fancy_print("This function cannot be accessed without adding books.")
                blocked = True
            elif missing_members:
                utils.fancy_print("This function cannot be accessed without adding members.")
                blocked = True        
        
        if blocked:
            pass

        elif num_choice not in range(1,30):
            utils.fancy_print("Try again with a number from 1 to 28.")
            utils.buffer()

        elif num_choice==1:
            books.add_book()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==2:
            books.edit_book()

        elif num_choice==3:
            books.delete_book()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==4:
            members.add_member()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==5:
            members.edit_member()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==6:
            members.delete_member()
            is_books_present, is_members_present = refresh_presence_flags()

        elif num_choice==7:
            transactions.issue_book()

        elif num_choice==8:
            transactions.return_book()

        elif num_choice==9:
            transactions.settle_fines()

        elif num_choice==10:
            members.pay_membership()

        elif num_choice==11:
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
        elif num_choice==12:
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

            # True by default but becomes optional if the book is found to be deleted. Thus, exits the loop and forces the next iteration after executing code below the loop.
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
        elif num_choice==13:
            matches, choices, member_ids = members.query_by_member_name()
            print()

            if not matches:
                # Two cases for no matches, both handled with print statements within query_books_by_name. Thus, exits the loop and forces the next iteration after executing code below the loop.
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
        elif num_choice==14:
            active_membership_info = members.active_members() # returns list of all (member_id, member_name, tier, expiry_date)
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
        elif num_choice==15:
            # condition paid=0 indicates unpaid fines
            if not pending_fines_list:
                print("No fines are currently pending.")
            else:
                headers=["Fine ID", "Member Name", "Book Name", "Fine Type", "Amount (Rs.)"]
                print("Pending fines:")
                print(tabulate(pending_fines_list, headers=headers, tablefmt=constants.cellstyle))

        # Issued Books - All issued books including overdue books
        elif num_choice==16:
            if not issued_books_list:
                print("No books are currently issued.")
            else:
                headers=["Transaction ID", "Book Name", "Member Name", "Issue Date", "Due Date"]
                print("Issued books:")
                print(tabulate(issued_books_list, headers=headers, tablefmt=constants.cellstyle))

        # Due Today
        elif num_choice==17:
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
        elif num_choice==18:
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
        elif num_choice==19:
            headers = ["Tier", "Price (Rs.)", "Maximum Books", "Loan Period (days)"]
            print(tabulate(constants.tier_info, headers=headers, tablefmt=constants.cellstyle))

        # All active books
        elif num_choice==20:
            db.cr.execute("select book_id, book_name, publication_date, genre, author_name from books where active=1")
            result=db.cr.fetchall()
            if result:
                print("Existing Books:")
                print(tabulate(result, ["Book ID", "Book Name", "Publication Date", "Genre", "Author Name"], tablefmt=constants.cellstyle))
            else:
                print("No books in the current catalog. Add new books to use this functionality.")

        # All members
        elif num_choice==21:
            db.cr.execute("select * from members")
            result=db.cr.fetchall()
            if result:
                print("Members:")
                print(tabulate(result, ["Member ID", "Member Name", "Email Address"], tablefmt=constants.cellstyle))
            else:
                print("No members in the library currently. Add new members to use this functionality.")

        elif num_choice==22:
            graphing.top_ten_books()

        elif num_choice==23:
            graphing.top_ten_members()

        elif num_choice==24:
            graphing.membership_chart()

        elif num_choice==25:
            graphing.genre_chart()

        elif num_choice==26:
            graphing.revenue_source_chart()

        # Custom Query
        elif num_choice==27:
            query=input("Enter your custom SELECT query: ")
            if query.strip().lower().startswith("select"):
                try:
                    db.cr.execute(query)
                    rows = db.cr.fetchall()
                    if rows:
                        headers=[]
                        for col in db.cr.description:
                            headers.append(col[0])
                        print(tabulate(rows, headers=headers, tablefmt=constants.cellstyle, missingval="NULL"))
                    else:
                        print("The query returned no rows.")
                except Exception as e:
                    print(e)
            else:
                print("Only SELECT statements are allowed for safety.")

        # Database Schema
        elif num_choice==28:
            db.cr.execute("show tables")
            tables = db.cr.fetchall()

            for table in tables:
                utils.buffer()
                table_name = table[0]
                print()
                print(f"--- {table_name} ---")
                db.cr.execute(f"desc {table_name}")
                columns = db.cr.fetchall()
                print(tabulate(columns, headers=["Field", "Type", "Null", "Key", "Default", "Extra"], tablefmt=constants.cellstyle, missingval="NULL"))

        # Clear all data
        elif num_choice==29:
            db.wipe_data()
            # No need to update the flags since the wipe_data() function exits the program. Restarting refreshes the flags again outisde the loop.

        # A break before the loop continues to ensure readability in the CLI
        utils.buffer()

except KeyboardInterrupt:
    utils.fancy_print("\nKeyboard Interrupt detected.")
    run=False
    db.quit()