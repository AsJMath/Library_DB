# FILES
from constants import mysqlpassword

# MODULES
import mysql.connector as ms

def create_and_seed_database():
    temp_conn = ms.connect(host="localhost", user="root", password=mysqlpassword)
    temp_cr = temp_conn.cursor()

    temp_cr.execute("create database if not exists library_db")
    temp_cr.execute("use library_db")
    temp_cr.execute("create table if not exists books (book_id int primary key, book_name text, publication_date date, genre text, author_name text, active tinyint(1) default 1)")
    temp_cr.execute("create table if not exists members (member_id int primary key, member_name text, address text)")
    temp_cr.execute("create table if not exists transactions (transaction_id int primary key, book_id int, member_id int, issue_date date, return_date date, due_date date, foreign key (book_id) references books(book_id), foreign key (member_id) references members(member_id))")
    temp_cr.execute("create table if not exists fines (fine_id int primary key, transaction_id int, fine_type text, amount decimal(6,2), paid tinyint(1), foreign key (transaction_id) references transactions(transaction_id))")
    temp_cr.execute("create table if not exists membership_payments (payment_id int primary key, member_id int, tier text, amount decimal(6,2), payment_date date, coverage_start date, expiry_date date, foreign key (member_id) references members(member_id))")

    temp_conn.commit()
    temp_cr.execute("delete from fines")
    temp_cr.execute("delete from membership_payments")
    temp_cr.execute("delete from transactions")
    temp_cr.execute("delete from members")
    temp_cr.execute("delete from books")
    temp_conn.commit()

    books = [
        (1, "1984", "1949-06-08", "Dystopian", "George Orwell", 1),
        (2, "Animal Farm", "1945-08-17", "Satire", "George Orwell", 1),
        (3, "Pride and Prejudice", "1813-01-28", "Romance", "Jane Austen", 1),
        (4, "Emma", "1815-12-23", "Romance", "Jane Austen", 1),
        (5, "Things Fall Apart", "1958-06-17", "Fiction", "Chinua Achebe", 1),
        (6, "Norwegian Wood", "1987-09-04", "Fiction", "Haruki Murakami", 1),
        (7, "Kafka on the Shore", "2002-09-12", "Fiction", "Haruki Murakami", 1),
        (8, "Beloved", "1987-09-02", "Fiction", "Toni Morrison", 1),
        (9, "One Hundred Years of Solitude", "1967-05-30", "Magical Realism", "Gabriel Garcia Marquez", 1),
        (10, "Love in the Time of Cholera", "1985-01-01", "Romance", "Gabriel Garcia Marquez", 1),
        (11, "Murder on the Orient Express", "1934-01-01", "Mystery", "Agatha Christie", 1),
        (12, "And Then There Were None", "1939-11-06", "Mystery", "Agatha Christie", 1),
        (13, "The Sound of Waves", "1954-06-10", "Fiction", "Yukio Mishima", 1),
        (14, "The God of Small Things", "1997-04-04", "Fiction", "Arundhati Roy", 1),
        (15, "Foundation", "1951-05-01", "Sci-Fi", "Isaac Asimov", 1),
        (16, "I, Robot", "1950-12-02", "Sci-Fi", "Isaac Asimov", 1),
        (17, "Mrs Dalloway", "1925-05-14", "Modernist", "Virginia Woolf", 1),
        (18, "To the Lighthouse", "1927-05-05", "Modernist", "Virginia Woolf", 1),
        (19, "War and Peace", "1869-01-01", "Historical", "Leo Tolstoy", 1),
        (20, "Crime and Punishment", "1866-01-01", "Fiction", "Fyodor Dostoevsky", 1),
        (21, "The Hounds of Baskerville", "1902-03-25", "Crime", "Arthur Conan Doyle", 1),
        (22, "Harry Potter and the Philosopher's Stone", "1997-06-26", "Fantasy", "J.K. Rowling", 1),
        (23, "The Catcher in the Rye", "1951-07-16", "Fiction", "J.D. Salinger", 1),
        (24, "Franny and Zooey", "1961-09-14", "Fiction", "J.D. Salinger", 1),
        (25, "Brave New World", "1932-08-30", "Dystopian", "Aldous Huxley", 1),
        (26, "The Doors of Perception", "1954-01-01", "Non-Fiction", "Aldous Huxley", 1),
        (27, "The Great Gatsby", "1925-04-10", "Fiction", "F. Scott Fitzgerald", 1),
        (28, "Tender Is the Night", "1934-04-12", "Fiction", "F. Scott Fitzgerald", 1),
        (29, "Slaughterhouse-Five", "1969-03-31", "Sci-Fi", "Kurt Vonnegut", 1),
        (30, "Cat's Cradle", "1963-01-01", "Sci-Fi", "Kurt Vonnegut", 1),
        (31, "The Hobbit", "1937-09-21", "Fantasy", "J.R.R. Tolkien", 1),
        (32, "The Fellowship of the Ring", "1954-07-29", "Fantasy", "J.R.R. Tolkien", 1),
        (33, "Fahrenheit 451", "1953-10-19", "Dystopian", "Ray Bradbury", 1),
        (34, "The Martian Chronicles", "1950-05-04", "Sci-Fi", "Ray Bradbury", 1),
        (35, "Wuthering Heights", "1847-12-01", "Romance", "Emily Bronte", 1),
        (36, "Jane Eyre", "1847-10-16", "Romance", "Charlotte Bronte", 1),
        (37, "The Trial", "1925-04-26", "Fiction", "Franz Kafka", 1),
        (38, "The Metamorphosis", "1915-01-01", "Fiction", "Franz Kafka", 1),
        (39, "Great Expectations", "1861-08-01", "Fiction", "Charles Dickens", 1),
        (40, "A Tale of Two Cities", "1859-04-30", "Historical", "Charles Dickens", 1),
    ]
    temp_cr.executemany("insert into books values (%s, %s, %s, %s, %s, %s)", books)
    temp_conn.commit()

    # --- Members ---
    members = [
        (1, "Aditi Sharma", "12 MG Road, Bangalore"),
        (2, "Rohan Mehta", "45 Park Street, Kolkata"),
        (3, "Sneha Iyer", "7 Anna Salai, Chennai"),
        (4, "Karan Malhotra", "23 Linking Road, Mumbai"),
        (5, "Priya Nair", "9 Residency Road, Bangalore"),
        (6, "Vikram Singh", "18 Civil Lines, Delhi"),
        (7, "Ananya Reddy", "5 Banjara Hills, Hyderabad"),
        (8, "Arjun Kapoor", "31 Camac Street, Kolkata"),
        (9, "Neha Gupta", "14 FC Road, Pune"),
        (10, "Rahul Verma", "2 Sector 17, Chandigarh"),
        (11, "Ishaan Bhatt", "22 Marine Drive, Mumbai"),
        (12, "Meera Krishnan", "9 Cathedral Road, Chennai"),
        (13, "Aarav Joshi", "17 Koramangala, Bangalore"),
        (14, "Divya Menon", "3 Jubilee Hills, Hyderabad"),
        (15, "Kabir Chatterjee", "56 Salt Lake, Kolkata"),
        (16, "Ritika Desai", "8 SG Highway, Ahmedabad"),
        (17, "Yash Rathod", "14 Sector 21, Chandigarh"),
        (18, "Ananya Pillai", "27 MG Road, Pune"),
        (19, "Dev Malhotra", "40 Vasant Kunj, Delhi"),
        (20, "Simran Kaur", "11 Model Town, Ludhiana"),
    ]
    temp_cr.executemany("insert into members values (%s, %s, %s)", members)
    temp_conn.commit()

    # --- Transactions ---
    # (transaction_id, book_id, member_id, issue_date, return_date, due_date)
    transactions = [
        (1, 1, 1, "2026-06-01", "2026-08-02", "2026-06-15"),
        (2, 3, 2, "2026-06-03", "2026-06-20", "2026-06-17"),
        (3, 5, 3, "2026-06-05", None, "2026-06-19"),
        (4, 7, 4, "2026-06-10", "2026-06-25", "2026-06-24"),
        (5, 9, 5, "2026-06-12", None, "2026-06-26"),
        (6, 2, 6, "2026-06-14", "2026-06-28", "2026-06-28"),
        (7, 11, 7, "2026-06-15", "2026-07-04", "2026-06-29"),
        (8, 4, 8, "2026-06-18", "2026-07-02", "2026-07-02"),
        (9, 6, 9, "2026-06-20", None, "2026-07-04"),
        (10, 13, 10, "2026-06-22", "2026-07-05", "2026-07-06"),
        (11, 15, 1, "2026-06-25", None, "2026-07-09"),
        (12, 8, 2, "2026-06-28", "2026-07-10", "2026-07-12"),
        (13, 1, 1, "2026-07-31", "2026-08-02", "2026-08-14"),
        (14, 1, 8, "2026-07-01", None, "2026-07-15"),
        (15, 26, 5, "2026-06-26", "2026-07-12", "2026-07-10"),
        (16, 40, 4, "2026-06-24", "2026-07-17", "2026-07-08"),
        (17, 19, 2, "2026-06-06", "2026-06-22", "2026-06-20"),
        (18, 21, 3, "2026-07-06", "2026-07-30", "2026-07-20"),
        (19, 12, 8, "2026-07-11", "2026-07-26", "2026-07-25"),
        (20, 31, 2, "2026-06-15", "2026-06-29", "2026-06-29"),
        (21, 13, 10, "2026-06-27", "2026-06-29", "2026-07-11"),
        (22, 25, 18, "2026-07-14", "2026-07-24", "2026-07-28"),
        (23, 18, 12, "2026-06-07", "2026-06-23", "2026-06-21"),
        (24, 7, 20, "2026-06-14", "2026-07-07", "2026-06-28"),
        (25, 33, 11, "2026-06-30", "2026-07-22", "2026-07-14"),
        (26, 29, 10, "2026-06-16", None, "2026-06-30"),
        (27, 21, 3, "2026-07-07", "2026-07-15", "2026-07-21"),
        (28, 27, 15, "2026-06-19", "2026-07-05", "2026-07-03"),
        (29, 12, 17, "2026-06-27", "2026-07-03", "2026-07-11"),
        (30, 14, 16, "2026-06-27", "2026-07-08", "2026-07-11"),
        (31, 8, 18, "2026-07-07", None, "2026-07-21"),
        (32, 26, 11, "2026-07-15", "2026-08-02", "2026-07-29"),
        (33, 35, 3, "2026-06-06", None, "2026-06-20"),
        (34, 36, 3, "2026-06-04", None, "2026-06-18"),
    ]
    temp_cr.executemany(
        "insert into transactions values (%s, %s, %s, %s, %s, %s)", transactions
    )
    temp_conn.commit()

    # --- Fines ---
    # fine_id 3 intentionally skipped, matching the original demo data
    fines = [
        (1, 2, "late", 60.00, 0),
        (2, 4, "late", 20.00, 1),
        (4, 15, "late", 40.00, 1),
        (5, 16, "late", 180.00, 1),
        (6, 17, "late", 40.00, 1),
        (7, 18, "late", 200.00, 1),
        (8, 18, "damage", 700.00, 1),
        (9, 19, "late", 20.00, 1),
        (10, 19, "damage", 700.00, 0),
        (11, 23, "late", 40.00, 0),
        (12, 24, "late", 180.00, 1),
        (13, 24, "damage", 700.00, 1),
        (14, 25, "late", 160.00, 1),
        (15, 28, "late", 40.00, 1),
        (16, 32, "late", 80.00, 1),
        (17, 1, "late", 960.00, 0),
        (18, 7, "late", 100.00, 0),
        (19, 34, "late", 20.00, 0),
        (20, 34, "damage", 700.00, 0),
    ]
    temp_cr.executemany(
        "insert into fines values (%s, %s, %s, %s, %s)", fines
    )
    temp_conn.commit()

    # --- Membership Payments ---
    # today's date assumed as 2026-08-25 for these seed values
    #
    # member 1: active bronze
    # member 2: active silver
    # member 3: active gold
    # member 4: active student
    # member 5: expired (lapsed) membership only
    # member 6: chained history — bronze (expired), then gold (active)
    # members 7-20: no membership record (never paid)
    membership_payments = [
        (1, 1, "bronze", 100.00, "2026-08-01", "2026-08-01", "2027-05-28"),   # active
        (2, 2, "silver", 250.00, "2026-07-15", "2026-07-15", "2027-05-11"),   # active
        (3, 3, "gold",   500.00, "2026-08-10", "2026-08-10", "2027-06-06"),   # active
        (4, 4, "student", 100.00, "2026-08-20", "2026-08-20", "2027-06-16"),  # active
        (5, 5, "bronze", 100.00, "2025-06-01", "2025-06-01", "2026-03-28"),   # expired (lapsed)
        (6, 6, "bronze", 100.00, "2025-09-01", "2025-09-01", "2026-06-28"),   # expired leg of chain
        (7, 6, "gold",   500.00, "2026-06-28", "2026-06-08", "2027-04-24"),   # active leg of chain (starts at prior expiry)
    ]
    temp_cr.executemany(
        "insert into membership_payments values (%s, %s, %s, %s, %s, %s, %s)", membership_payments
    )
    temp_conn.commit()

    print("Demo database created and seeded successfully. Connection closed.")
    temp_conn.close()

create_and_seed_database()