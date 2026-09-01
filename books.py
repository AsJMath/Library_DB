from db import connect, cr, next_id
from rapidfuzz import process, fuzz

def is_available(book_id):
    # all books out of library and not available
    cr.execute("select * from transactions where return_date is null")

    issued_books = cr.fetchall()
    for record in issued_books:
        if book_id == record[1]:
            return False
    return True

def currentBorrower(book_id):
    if not is_available(book_id):
        cr.execute("select members.member_id, member_name, book_id from members, transactions where members.member_id=transactions.member_id and return_date is null and book_id=%s", (book_id,))
        member_details=cr.fetchone()
        member_id, member_name=member_details[0], member_details[1]
        return member_id, member_name
    else:
        print("Book is in the library.")
        return None

def add_books():
    book_id=next_id("books")
    book_name=input("Enter the book name: ")
    publication_date=input("Enter the date of publication in YYYY-MM-DD: ")
    genre=input("Enter the genre: ")
    author_name=input("Enter the name of the author: ")

    cr.execute("insert into books values(%s, %s, %s, %s, %s)", (book_id, book_name, publication_date, genre, author_name))
    connect.commit()
    print("New book added.")

def search_books():
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
        query=input("Enter the book title or author: ")

        if len(query) < 5:
            print("Please enter at least 5 characters to search.")
            return

        cr.execute("select book_id, book_name, author_name from books")
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
            print("No matching books found.")
        else:
            print(f"Search results for '{query}':")
            for match_str, score, index in matches:
                record=choices[match_str] # finding the value from the choices dictionary for book_id, book_name and author_name
                print(f"book id: {record[0]} | {record[1]} | {record[2]}")
    
    elif method==2:
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
            cr.execute("select book_id, book_name, author_name, publication_date from books where genre=%s", (matched_genre, ))
            result=cr.fetchall()

            print(f"Books in genre: {matched_genre}")
            for record in result:
                print(f"book id: {record[0]} | {record[1]} | {record[2]} | published: {record[3]}")
