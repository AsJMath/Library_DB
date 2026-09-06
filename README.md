# Library Management System

A command-line library management system built with Python and MySQL. Handles book cataloging, member registration, book issuing/returns, membership tiers, fines, and reporting through an interactive CLI menu.

## Requirements

- Python 3.x
- MySQL Server (running locally)
- Python packages:
  ```
  mysql-connector-python
  tabulate
  rapidfuzz
  matplotlib
  ```

Install dependencies:
```bash
pip install mysql-connector-python tabulate rapidfuzz matplotlib
```

## Setup

1. **Configure your MySQL credentials** in `constants.py`:
   ```python
   mysqlpassword = ""  # set your MySQL root password here
   ```

2. **Run the application:**
   ```bash
   python main.py
   ```
   On first run, the database and all required tables are created automatically — no manual schema setup needed.

3. **(Optional) Load demo data:**
   ```bash
   python demo_setup.py
   ```
   Wipes and reseeds the database with sample books, members, transactions, fines, and membership history — useful for exploring the system without entering data by hand.

## Using the Application

Running `main.py` drops you into a menu loop. Type the number of an option and press Enter; most actions will prompt you for any additional details they need (book ID, member ID, dates, etc.).

```
$ Actions
1. Add books
2. Delete books
3. Add members
4. Issue book
5. Return book
6. Settle Fines
7. Pay Membership

$ Information
8. Generic Search
9. Book Info
10. Member Info
11. Membership Info
12. Pending Fines
13. Issued Books
14. Due Today
15. Overdue Books
16. Tier Info

$ Charts
17. Top 10 Books
18. Top 10 Members
19. Membership Chart
20. Genre Chart
21. Revenue Source Chart
22. Exit

$ Advanced
23. Custom Query
24. See Database Schema
```

Type `credits` at any menu prompt to see author/tooling credits.

### Notification Indicators

A `[!!]` marker appears next to **Pending Fines**, **Issued Books**, **Due Today**, and **Overdue Books** whenever that category currently has items needing attention — so you can tell what's outstanding without opening each option.

### 1. Add Books
Enter a book name. If a similar or previously-deleted book is found, you'll be offered the chance to restore it instead of creating a duplicate. Otherwise, you'll be prompted for publication date, genre, and author.

### 2. Delete Books
Search for the book, then enter its ID to remove it. This is a soft-delete — the book is marked inactive rather than erased, and can be restored later via Add Books. Books currently checked out can't be deleted until they're returned.

### 3. Add Members
Enter a name and email address. New members have no membership by default — use Pay Membership separately to activate one.

### 4. Issue Book
Search for and select a book, then enter the member's ID. The system checks that the member has an active membership and hasn't hit their tier's borrowing limit before recording the issue and calculating a due date.

### 5. Return Book
Enter the book's ID. You'll enter the return date, and the system automatically calculates any late fine. You'll also be asked whether the book was damaged, which applies a separate flat fine if so.

### 6. Settle Fines
Enter a member ID to see their pending fines, then choose to settle one specific fine or all of them at once.

### 7. Pay Membership
Enter a member ID and choose a tier (bronze/silver/gold/student). If the member has an existing membership, the new one is chained to start when the old one expires; otherwise it starts immediately.

### 8. Generic Search
Search books by title/author (fuzzy match) or by genre.

### 9. Book Info
Look up a book to see its current borrower (if any) and full transaction history.

### 10. Member Info
Look up a member to see their current tier, transaction history, and membership payment history.

### 11. Membership Info
Lists all members with active memberships and separately lists members without one, with the option to view a pie chart breakdown by tier.

### 12–15. Pending Fines / Issued Books / Due Today / Overdue Books
Each lists the relevant records. Due Today and Overdue Books also offer to draft a `mailto:` email per affected member, listing their books, which opens in your default mail client.

### 16. Tier Info
Displays a table comparing all membership tiers by price, borrowing limit, and loan period.

### 17–21. Charts
Visualizations built with matplotlib: top 10 books/members by times issued, membership tier distribution, genre distribution, and revenue split between fines and membership payments.

### 22. Exit
Closes the database connection and ends the program.

### 23. Custom Query
Run a raw `SELECT` statement against the database. Only `SELECT` is permitted, for safety.

### 24. See Database Schema
Prints all tables and their columns/types.

## Membership Tiers

| Tier | Price (Rs.) | Max Books | Loan Period (days) |
|---|---|---|---|
| Bronze | 100 | 2 | 14 |
| Silver | 250 | 4 | 21 |
| Gold | 500 | 6 | 30 |
| Student | 100 | 6 | 30 |

Membership duration is ~10 months (300 days) per payment.

## Fines

- **Late return:** Rs. 20 per day late
- **Damage:** flat Rs. 700

## Project Structure

```
├── main.py           # CLI menu loop
├── books.py          # Book CRUD, fuzzy search, availability checks
├── members.py        # Member registration, membership tiers/payments
├── transactions.py   # Issuing, returning, fines, settlement
├── graphing.py        # Chart generation
├── mailer.py         # mailto: draft generation
├── dates.py          # Date arithmetic helpers
├── db.py             # Database connection and schema creation
├── demo_setup.py     # Wipes and seeds demo data
└── constants.py      # Tier pricing/limits, fine amounts, UI strings
```

