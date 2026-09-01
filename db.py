import mysql.connector as ms

def create_database():
    password=""
    temp_conn = ms.connect(host="localhost", user="root", password=password)
    temp_cr = temp_conn.cursor()

    temp_cr.execute("create database if not exists library_db")
    temp_cr.execute("use library_db")
    temp_cr.execute("create table if not exists books (book_id int primary key, book_name text, publication_date date, genre text, author_name text)")
    temp_cr.execute("create table if not exists members (member_id int primary key, member_name text, address text)")
    temp_cr.execute("create table if not exists transactions (transaction_id int primary key, book_id int, member_id int, issue_date date, return_date date, due_date date, foreign key (book_id) references books(book_id), foreign key (member_id) references members(member_id))")
    temp_cr.execute("create table if not exists fines (fine_id int primary key, transaction_id int, fine_type text, amount decimal(6,2), paid tinyint(1), foreign key (transaction_id) references transactions(transaction_id))")
    temp_cr.execute("create table if not exists membership_payments (payment_id int primary key, member_id int, tier text, amount decimal(6,2), payment_date date, coverage_start date, expiry_date date, foreign key (member_id) references members(member_id))")

    temp_conn.commit()
    temp_cr.close()
    temp_conn.close()
create_database()

connect=ms.connect(host="localhost", user="root", password="mysql", database="library_db")
cr=connect.cursor()

primkeys = {
    "books": "book_id",
    "members": "member_id",
    "transactions": "transaction_id",
    "fines": "fine_id",
    "membership_payments": "payment_id"
}


def next_id(table_name):
    primkey = primkeys[table_name]
    cr.execute(f"select max({primkey}) from {table_name}")
    max_id=cr.fetchone()[0]
    if max_id is None:
        return 1
    else:
        return max_id + 1
