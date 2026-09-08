# FILES
from constants import mysqlpassword

# MODULES
import mysql.connector as ms

# Sets up the database and the empty tables with correct names and fields of correct datatypes to begin library operations
def create_database():
    temp_conn = ms.connect(host="localhost", user="root", password=mysqlpassword)
    temp_cr = temp_conn.cursor()

    temp_cr.execute("create database if not exists library_db")
    temp_cr.execute("use library_db")
    temp_cr.execute("create table if not exists books (book_id int primary key auto_increment, book_name text, publication_date date, genre text, author_name text, active tinyint(1) default 1)")
    temp_cr.execute("create table if not exists members (member_id int primary key auto_increment, member_name text, email_address varchar(255))")
    temp_cr.execute("create table if not exists transactions (transaction_id int primary key auto_increment, book_id int, member_id int, issue_date date, return_date date, due_date date, foreign key (book_id) references books(book_id), foreign key (member_id) references members(member_id))")
    temp_cr.execute("create table if not exists fines (fine_id int primary key auto_increment, transaction_id int, fine_type text, amount decimal(6,2), paid tinyint(1), foreign key (transaction_id) references transactions(transaction_id))")
    temp_cr.execute("create table if not exists membership_payments (payment_id int primary key auto_increment, member_id int, tier text, amount decimal(6,2), payment_date date, coverage_start date, expiry_date date, foreign key (member_id) references members(member_id))")
    temp_conn.commit()
    temp_cr.close()
    temp_conn.close()

# create_database() is called explicitly because when db.py is imported in main.py (like all imports), the file being imported is executed. None of the other files perform any visible actions when imported because their functions are not being called within the file, only externally.
create_database()

connect=ms.connect(host="localhost", user="root", password=mysqlpassword, database="library_db")
cr=connect.cursor(dictionary=False) # Ensures that return results are tuples and not dictionaries

def quit(run_variable):
        print("Exiting program...")
        cr.close()
        connect.close()
        run_variable=False
