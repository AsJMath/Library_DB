# Library Management System

A menu-driven Python + MySQL application for managing a library's books, members, transactions, fines, and memberships — with fuzzy search, visual analytics, and email drafting.

---

## Part 1: User Guide

### What This System Does

This is a command-line program you run in a terminal. It lets a librarian:

- Add, delete (and restore), and search for books using fuzzy matching
- Add members and issue/return books, with tier-based limits and rolling membership expiry
- Track fines for late returns and damaged books
- Manage tiered memberships (bronze/silver/gold/student) with expiry dates
- View reports: pending fines, issued books, due-today and overdue books, top borrowers
- Draft ready-to-send email notices (via your default mail app) for books due today or overdue
- View charts: top 10 books, top 10 members, membership split, genre breakdown, revenue by source
- Run custom `SELECT` queries and inspect the database schema directly

### Getting Started

1. Make sure MySQL is running locally with a `root` user. This project assumes the `root` user has **no password** set. If your MySQL root user has a password, either:
   - Remove it by running this in the `mysql` CLI: `ALTER USER 'root'@'localhost' IDENTIFIED BY ''; FLUSH PRIVILEGES;`, or
   - Open `constants.py` and replace the empty string in `mysqlpassword=""` with your own password
2. Run `main.py`. On first run, it automatically creates the `library_db` database and all required tables if they don't already exist.
3. You'll see a welcome banner, then a numbered menu. Type a number and press Enter to choose an action.

### Menu Walkthrough

**Actions**
| Option | What it does |
|---|---|
| 1. Add books | Searches existing (including deleted) books first — if the title resembles a previously deleted book, offers to restore it instead of creating a duplicate. Otherwise prompts for publication date, genre, and author, and adds a new book. |
| 2. Delete books | Searches for a book by title/author, then soft-deletes it (marks it inactive rather than removing the row) — preserving transaction/fine history. Blocked if the book is currently checked out. |
| 3. Add members | Prompts for name and email address. Adds a member *without* a membership — pay separately. |
| 4. Issue book | Searches for a book to issue, checks it exists and is available, checks the member has an active membership with room under their tier's book limit, then issues it. |
| 5. Return book | Records the return date, calculates late fines automatically, and asks if the book was damaged. |
| 6. Settle Fines | Lists a member's unpaid fines; settle one specific fine or all of them at once. |
| 7. Pay Membership | Records a new membership payment. If the member already has time remaining on an existing membership, the new period starts after the current one expires (memberships stack). |

**Information**
| Option | What it does |
|---|---|
| 8. Generic Search | Fuzzy-search active books by title/author, or search by genre. Typos are tolerated. |
| 9. Book Info | Shows a book's current borrower (if any) and its full transaction history. Warns first if the book has been deleted. |
| 10. Member Info | Shows a member's current tier, transaction history, and membership payment history. |
| 11. Membership Info | Lists all members with active memberships (and their expiry dates), plus members with none. Offers a membership pie chart. |
| 12. Pending Fines | Lists every unpaid fine across all members. |
| 13. Issued Books | Lists every book currently checked out. |
| 14. Due Today | Lists books due back today. Offers to draft one grouped email per member listing all their books due today. |
| 15. Overdue Books | Lists books past their due date and still not returned. Offers to draft one grouped email per member listing all their overdue books. |
| 16. Top 10 Books | Bar chart of the 10 most-issued books (all-time, including deleted books — this is historical data). |
| 17. Top 10 Members | Bar chart of the 10 members who've issued the most books. |
| 18. Membership Chart | Pie chart of how many members hold each tier (including no active membership). |
| 19. Genre Chart | Pie chart of the *active* book collection by genre. |
| 20. Revenue Source Chart | Pie chart comparing total revenue from fines vs. membership payments. |
| 21. Exit | Closes the database connection and quits. |

**Advanced**
| Option | What it does |
|---|---|
| 22. Custom Query | Enter your own `SELECT` statement and see the raw results. Only `SELECT` is allowed, for safety. |
| 23. See Database Schema | Lists every table and its columns. |

### Deleting and Restoring Books

Books are never truly removed from the database — deleting a book just marks it inactive (`active=0`), so its transaction and fine history stays intact and correctly linked. A currently-issued book cannot be deleted until it's returned.

If you later "add" a book whose title closely matches a previously deleted one, the system will offer to restore the original record instead of creating a duplicate — this keeps historical records (fines, past borrows) attached to a single consistent book entry rather than fragmenting across two IDs.

### Email Notices

Options 14 and 15 can draft an email per member (grouping all their relevant books into one message) using your computer's default mail application — no email account or password is stored or used by the program itself. The program only builds a `mailto:` link and hands it to your operating system, which opens your configured mail client with the recipient, subject, and message body pre-filled. You review and send each one manually.

### Membership Tiers

| Tier | Price | Loan period | Max books at once |
|---|---|---|---|
| Bronze | Rs. 100 | 14 days | 2 |
| Silver | Rs. 250 | 21 days | 4 |
| Gold | Rs. 500 | 30 days | 6 |
| Student | Rs. 100 | 30 days | 6 |

Every membership lasts ~10 months (300 days) from its start date.

### Fines

- **Late return:** Rs. 20 per day late.
- **Damage:** flat Rs. 700, recorded if you answer "yes" when asked at return time.

### Charts, Practically

Charts open in a separate window (matplotlib). Close the window to return to the menu — the program keeps running underneath, it's just waiting for you.

---

## Part 2: Developer / Code Guide

### File Structure

```
db.py            — database connection, table creation, shared cursor, ID generator
constants.py     — all tunable business values (prices, fines, loan periods, limits, table style)
dates.py         — date arithmetic helpers
books.py         — book CRUD (including soft delete/restore), availability checks, fuzzy search
members.py       — member CRUD, membership status checks, membership payments
transactions.py  — issuing, returning, and fine settlement logic
graphing.py       — matplotlib chart generation
mailer.py        — mailto: link construction and grouped email drafting
main.py          — the menu loop that ties everything together
demo_setup.py    — one-off script to create and seed the database with sample data
```

### `db.py` — Database Layer

- `create_database()` runs once on import: creates the database and all 5 tables (`books`, `members`, `transactions`, `fines`, `membership_payments`) if they don't exist, using `foreign key` constraints to link `transactions` → `books`/`members`, and `fines` → `transactions`. `books` includes an `active` column (default `1`) supporting soft deletion; `members` does not, since member removal isn't supported (a lapsed membership already prevents new borrowing — see Design Notes below).
- A single shared `connect` (connection) and `cr` (cursor) are created at import time and reused across every module.
- `next_id(table_name)` is a manual auto-increment: looks up `max(primary_key)` in the given table and returns `+1`, or `1` if the table is empty.

### `constants.py`

Pure data — no logic. Centralizes every business rule (fine amounts, loan periods, tier prices, book limits, membership duration) plus the shared `tabulate` style (`cellstyle`) used consistently across every table printed in the CLI.

### `dates.py`

- `add_date(original_date, increment)` — adds `increment` days to a `YYYY-MM-DD` string, returns a new string.
- `is_late(date1, date2)` — returns how many days `date2` is *after* `date1`, or `0` otherwise. Used both to calculate late fines and to validate that a return date isn't before the issue date.

### `books.py`

- `is_available(book_id)` — checks currently-issued transactions (`return_date is null`) to determine checked-out status only.
- `book_exists(book_id)` — separately checks a book's `active` flag, distinguishing "checked out" from "deleted" (these are deliberately kept as two separate functions rather than merged into one ambiguous boolean).
- `current_borrower(book_id)` — if checked out, returns the current borrower's ID, name, and due date.
- `add_books()` — searches all books (active and deleted) for a close match to the entered title before creating anything new. If the closest match is already active, warns and makes no changes (prevents accidental duplicate issuing/adding). If the closest match is deleted, offers to restore it. Otherwise, proceeds to create a new book.
- `query_books_by_name(active_only, query)` — shared fuzzy-search function (via `rapidfuzz`) reused by search, issuing, deleting, and book-add duplicate-checking. `active_only=True` (the default) restricts to active books; `active_only=False` searches everything and also returns each result's active status, needed by `add_books()`.
- `query_books_by_genre()` — fuzzy-matches a genre name, then lists active books in that genre.
- `delete_book()` — searches for a book, confirms it isn't currently checked out, then sets `active=0`. Transaction and fine history referencing that book remain fully intact.

### `members.py`

- `active_members()` — returns every membership payment row currently within its coverage window.
- `is_active_member(member_id)` — finds a specific member's current tier, or `None`.
- `pay_membership()` — new memberships start today if the member has none; if they have a still-valid membership, the new one starts at the *existing* membership's expiry date, so paid periods stack sequentially rather than overlapping or resetting.
- `no_of_books_issued_to(member_id)` — counts a member's currently-unreturned books, enforcing the tier's book limit.

### `transactions.py`

- `issue_book()` — searches for a book to issue, validates it exists and is available, validates membership status/limit, then inserts a new transaction with `return_date` as `NULL`.
- `return_book()` — updates `return_date`, calculates late fines via `is_late(due_date, return_date)`, and asks about damage, inserting separate `fines` rows as needed.
- `settle_fines()` — lists a member's unpaid fines, then marks one specific fine or all of them as paid.

### `graphing.py`

- `pie_chart()` and `plot_top_ten()` — shared rendering helpers reused across every chart function, avoiding duplicated matplotlib boilerplate. `pie_chart()` supports an optional `explode_sequence` to visually highlight one slice (used by the genre chart to highlight a searched-for genre).
- `top_ten_books()` / `top_ten_members()` — deliberately **not** filtered by `active`, since these represent historical circulation data; a withdrawn book's past popularity is still a meaningful data point.
- `genre_chart(target_genre)` — **is** filtered by `active=1`, since this chart represents the *current* live collection, not history. If `target_genre` is supplied (e.g. from a genre search), that slice is exploded outward.
- `revenue_source_chart()` — compares total fine revenue against total membership payment revenue.

### `mailer.py`

- `send_mail(to, subject, body, cc, bcc)` — builds a `mailto:` URL (percent-encoding the subject/body via `urllib.parse.urlencode`) and hands it to the OS via `webbrowser.open()`, which opens the user's default mail client with the message pre-filled. No credentials, SMTP server, or email account are used by the program — the librarian reviews and sends each email manually.
- `mail_body(member_name, books, case)` — builds a numbered list of book titles into a plain-text message body; `case` is either `"due today"` or `"overdue"`, changing the message wording.
- `draft_group_emails(rows, subject_line, case)` — shared by both the Due Today and Overdue Books menu options. Groups multiple books belonging to the same member into a single email (so a member with 3 overdue books gets one email listing all 3, not three separate ones), looks up each member's stored email address, and pauses between each drafted email so the librarian isn't flooded with mail app windows opening at once.

### `main.py`

A single `while run:` loop:
1. Prints the menu.
2. Reads and validates the user's numeric choice.
3. Dispatches to an `elif` branch per option — some call functions from other modules directly, others contain their own inline SQL for one-off reports.
4. Option 22 sanitizes custom queries to only permit strings starting with `select`, wrapped in a `try/except` so malformed SQL doesn't crash the program.
5. Option 21 closes the cursor and connection cleanly before breaking the loop.

### `demo_setup.py`

A standalone script (not imported by `main.py`) that wipes and reseeds the database with realistic sample data across all 5 tables — useful for resetting to a known state during development or demonstration, including deliberately varied membership states (active, expired, chained renewal) and fine scenarios (paid, unpaid, late, damage).

### Design Notes

- **Why books support soft delete but members don't:** A lapsed membership already prevents a member from borrowing further (`is_active_member()` returns `None`, and `issue_book()` blocks on this) — no additional mechanism was needed. Books have no equivalent natural "lapse" state, so an explicit `active` flag was needed to represent a withdrawn/lost book while preserving its transaction history against the foreign key constraint.
- **Why `top_ten_*` charts ignore `active` but the genre chart doesn't:** these charts answer two different questions — "what happened historically" (unaffected by later deletions) versus "what's currently on the shelves" (should reflect deletions immediately).
- **Why email sending uses `mailto:` instead of SMTP:** avoids storing any email credentials in the codebase entirely, keeps the librarian in control of every message before it's sent, and needs no external dependency beyond Python's standard library.

### Known Limitations / Things Worth Improving

- No input sanitization beyond option 22's `SELECT`-only check — direct `int()` casts on IDs will crash the program on non-numeric input in most menu options (e.g. `settle_fines()`'s fine ID prompt).
- The shared global `cr`/`connect` from `db.py` means there's no way to run concurrent operations safely; fine for a single-user CLI tool.
- `revenue_source_chart()` will error on a completely empty `fines` or `membership_payments` table (`sum()` returns `NULL` on no rows).
- `query_books_by_genre()`'s initial genre list isn't filtered by `active`, so a genre that only exists among deleted books may appear searchable even though no active books would be returned.
- Several `main.py` options contain inline SQL rather than delegating to their respective modules — a possible refactor target for consistency.
- `next_id()` re-scans `max(id)` on every call rather than tracking state, which is simple but not efficient at scale.