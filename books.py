# FILES
from db import connect, cr, next_id
from constants import cellstyle

# MODULES
from rapidfuzz import process, fuzz
from tabulate import tabulate

# For a given book id, checks if the book is within the library and is available for borrowing or deleting
def is_available(book_id):
    # all books out of library and not available
    cr.execute("select * from transactions where return_date is null")
    issued_books = cr.fetchall()
    for record in issued_books:
        if book_id == record[1]:
            return False
    return True

# Checks if the book is an active book (active=1) or not (active=0, meaning deleted)
def book_exists(book_id):
    cr.execute("select active from books where book_id=%s", (book_id,))
    result = cr.fetchone() 
    # Can be a non-zero nested tuple, can be a nested tuple with zero, can be a none object if book_id doesn't exist at all
    if result is None:
        return False  # handles: book_id doesn't exist at all
    return bool(result[0]) # handles: book_id is active, book_id is inactive

# Identifies the current borrower of a book
def current_borrower(book_id):
    # Checks that the book is actually in somebody's hands and not in the library
    if not is_available(book_id):
        cr.execute("select members.member_id, member_name, due_date from members, transactions where members.member_id=transactions.member_id and return_date is null and book_id=%s", (book_id,))
        result=cr.fetchone()
        # returns (member_id, member_name, due_date)
        member_id, member_name, due_date=result[0], result[1], result[2]
        return member_id, member_name, due_date
    else:
        print("Book is in the library.")
        return None

# Adding new books into the library catalog
def add_books():
    book_name=input("Enter the book name: ")
    # Runs query_books_by_name, meaning matches, choices gets returned and unpacked alongside the printing of viable values
    matches, choices = query_books_by_name(active_only=False, query=book_name)

    # Checks if the book being added is a deleted (non-existent, active=0) book using the query_books_by_name function
    if matches:
        pick=input("Did you mean one of these? Enter the Book ID to select it, or 0 to add as a new book: ")
        try:
            pick=int(pick)
        except ValueError:
            print("Invalid input. Adding as a new book instead...")
            pick=0

        if pick != 0:
            matched_record=None
            for record in choices.values():
                if record[0] == pick: # record[0] is the book id from the choices.values() dictionary of tuple values
                    matched_record=record
                    break

            if matched_record is None:
                # Book ID is not found in the list of viable choices of existing books, meaning the book is likely a new addition to the library.
                print("Book ID not found. Adding as a new book instead...")
            else:
                is_active=matched_record[3] # matched_record[3] is the active status of the record if matched.
                if is_active:
                    print(f"'{matched_record[1]}' already exists in the active catalog. No changes made.")
                    return
                else:
                    cr.execute("update books set active=1 where book_id=%s", (pick,))
                    connect.commit()
                    print("Book restored to the active catalog.")
                    return

    print("Adding as a new book...")
    book_id=next_id("books")
    publication_date=input("Enter the date of publication in YYYY-MM-DD: ")
    genre=input("Enter the genre: ")
    author_name=input("Enter the name of the author: ")

    cr.execute("insert into books values(%s, %s, %s, %s, %s, %s)", (book_id, book_name, publication_date, genre, author_name, 1))
    connect.commit()
    print("New book added.")

# Generic Search using rapidfuzz module
def generic_search():
    while True:
        method=input("""
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
        query_books_by_genre()
                    
def query_books_by_name(active_only=True, query=None):
    if query is None:
        query=input("Enter the book title or author: ")

    if len(query) < 5:
        print("Please enter at least 5 characters to search.")
        return [], {} # satisfies the return matches, choices for consistency irrespective of which return gets triggered.

    if active_only:
        cr.execute("select book_id, book_name, author_name from books where active=1")
    else:
        cr.execute("select book_id, book_name, author_name, active from books")
    all_books=cr.fetchall()

    choices={}
    for record in all_books:
        key=f"{record[1]} {record[2]}" # key is the string of book name + author name, which is what the rapidfuzz algorithm searches for
        choices[key]=record
        # each key that the rapidfuzz algorithm searches for (a string) is linked to the actual data from the database, the book (book_name) and its details (book_id and author_name)
    matches=process.extract(query, choices.keys(), limit=5, score_cutoff=60, scorer=fuzz.partial_ratio)
    # .extract(<the string to be searched for, <what to search in>, <how many results to show>, <requires a minimum match of how much %>)
    # scorer=fuzz.partial_ratio finds the best matching substring within each key, rather than comparing the full strings —

    # matches is a list of tuples, with each tuple of the format (<key from choices>, <likelihood of a match out of 100>, <index in the choices dictionary>)
    print()
    if not matches:
        print("No existing books found.")
    else:
        rows=[]
        for match_str, score, index in matches:
            record=choices[match_str]
            rows.append([record[0], record[1], record[2]])  # only show ID, name, author  active status stays hidden from the table

        print(tabulate(rows, headers=["Book ID", "Book Name", "Author Name"], tablefmt=cellstyle))
    return matches, choices

def query_books_by_genre():
    query=input("Enter the genre: ")

    cr.execute("select distinct genre from books")
    genre_rows=cr.fetchall()
    all_genres=[]
    for row in genre_rows:
        all_genres.append(row[0])
    
    best_match=process.extractOne(query, all_genres, score_cutoff=60)
    # .extractOne returns a tuple whose first element is a string from the all_genres iterable that matches closest to query within the cutoff of 60%
    # .extractOne returns a single tuple in the format (<string>, <likelihood out of 100>, <index in the all_genres iterable>)

    print()
    if best_match is None:
        print("No matching genre found.")
    else:
        matched_genre=best_match[0]
        cr.execute("select book_id, book_name, author_name, publication_date from books where genre=%s and active=1", (matched_genre, ))
        result=cr.fetchall()
        headers=["Book ID", "Book Name", "Author Name", "Publication Date"]
        print(f"Books in genre: {matched_genre}")
        print(tabulate(result, headers=headers, tablefmt=cellstyle))
        return matched_genre

# Deletion of books from the database is directly difficult because records in the transaction table referencing the book_id as foreign key may exist 
def delete_book():
    # Allows for a search function to determine the book id until the desired book is located
    while True:
        query_books_by_name()
        print()
        book_id = int(input("Enter the book id to delete or enter 0 to seach again: "))
        if book_id==0:
            continue
        if is_available(book_id):
            # book is available i.e. is in the library and can be deleted (thus proceed)
            break
        else:
            due_date=current_borrower(book_id)[2] # currentBorrower returns a tuple of type (<member_id>, <member name>, <due_date>)
            print(f"This book is out of the library, expected to be returned on {due_date} and cannot be deleted yet.")

    cr.execute("update books set active=0 where book_id=%s", (book_id,))
    connect.commit()
    print(f"Book has been removed from the catalog.")