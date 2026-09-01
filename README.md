# Library Management System

A menu-driven Python + MySQL application for managing a library's books, members, transactions, fines, and memberships — with fuzzy search and visual analytics.

---

## Part 1: User Guide

### What This System Does

This is a command-line program you run in a terminal. It lets a librarian:

- Add books and members to the database
- Issue and return books
- Track fines for late returns and damaged books
- Manage tiered memberships (bronze/silver/gold/student) with expiry dates
- Search for books by title, author, or genre
- View reports: pending fines, issued books, overdue books, top borrowers
- View charts: top 10 books, top 10 members, membership split, genre breakdown
- Run custom `SELECT` queries and inspect the database schema directly

### Getting Started

1. Make sure MySQL is running locally with a `root` user. This project assumes the `root` user has **no password** set. If your MySQL root user has a password, either:
   - Remove it by running this in the `mysql` CLI: `ALTER USER 'root'@'localhost' IDENTIFIED BY ''; FLUSH PRIVILEGES;`, or
   - Open `db.py` and replace the empty string in `password=""` with your own password
2. Run `main.py`. On first run, it automatically creates the `library_db` database and all required tables if they don't already exist.
3. You'll see a welcome banner, then a numbered menu. Type a number and press Enter to choose an action.

### Menu Walkthrough

**Actions**
| Option | What it does |
|---|---|
| 1. Add books | Prompts for title, publication date, genre, author. Adds a new book. |
| 2. Add members | Prompts for name and address. Adds a member *without* a membership — pay separately. |
| 3. Issue book | Checks the book is available and the member has an active membership with room under their tier's book limit, then issues it. |
| 4. Return book | Records the return date, calculates late fines automatically, and asks if the book was damaged. |
| 5. Settle Fines | Lists a member's unpaid fines; settle one specific fine or all of them at once. |
| 6. Pay Membership | Records a new membership payment. If the member already has time remaining on an existing membership, the new period starts after the current one expires (memberships stack). |

**Information**
| Option | What it does |
|---|---|
| 7. Generic Search | Fuzzy-search books by title/author, or search by genre. Typos are tolerated. |
| 8. Book Info | Shows a book's current borrower (if any) and its full transaction history. |
| 9. Member Info | Shows a member's current tier, transaction history, and membership payment history. |
| 10. Membership Info | Lists all members with active memberships (and their expiry dates), plus members with none. |
| 11. Pending Fines | Lists every unpaid fine across all members. |
| 12. Issued Books | Lists every book currently checked out. |
| 13. Overdue Books | Lists every book currently checked out *and* past its due date. |
| 14. Top 10 Books | Bar chart of the 10 most-issued books. |
| 15. Top 10 Members | Bar chart of the 10 members who've issued the most books. |
| 16. Membership Split | Pie chart of how many members hold each tier (including no active membership). |
| 17. Genre Diagram | Pie chart of the library's book collection by genre. |
| 18. Custom Query | Enter your own `SELECT` statement and see the raw results. Only `SELECT` is allowed, for safety. |
| 19. See Database Schema | Lists every table and its columns. |
| 20. Exit | Closes the database connection and quits. |

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
constants.py     — all tunable business values (prices, fines, loan periods, limits)
dates.py         — date arithmetic helpers
books.py         — book CRUD, availability checks, fuzzy search
members.py       — member CRUD, membership status checks, membership payments
transactions.py  — issuing, returning, and fine settlement logic
graphing.py       — matplotlib/seaborn chart generation
main.py          — the menu loop that ties everything together
```

### `db.py` — Database Layer

- `create_database()` runs once on import: creates the database and all 5 tables (`books`, `members`, `transactions`, `fines`, `membership_payments`) if they don't exist, using `foreign key` constraints to link `transactions` → `books`/`members`, and `fines` → `transactions`.
- A single shared `connect` (connection) and `cr` (cursor) are created at import time and reused across every module — there's no connection pooling or per-function connections.
- `next_id(table_name)` is a manual auto-increment: it looks up `max(primary_key)` in the given table and returns `+1`, or `1` if the table is empty. This exists instead of using MySQL's built-in `AUTO_INCREMENT`.

### `constants.py`

Pure data — no logic. Centralizes every business rule (fine amounts, loan periods, tier prices, book limits, membership duration) so they can be tuned in one place instead of scattered through the codebase.

### `dates.py`

Two helpers built on Python's `datetime`:
- `add_date(original_date, increment)` — adds `increment` days to a `YYYY-MM-DD` string, returns a new string.
- `is_late(date1, date2)` — returns how many days `date2` is *after* `date1`, or `0` if it isn't after. Used both to calculate late fines (`is_late(due_date, return_date)`) and to validate that a return date isn't before the issue date.

### `books.py`

- `is_available(book_id)` — checks all transactions with `return_date is null` (i.e. currently issued books) and returns `False` if the given book is among them.
- `currentBorrower(book_id)` — if the book is checked out, joins `members` and `transactions` to find who has it.
- `add_books()` — straightforward insert after prompting for details.
- `search_books()` — two modes:
  - **Title/Author**: builds a dictionary mapping `"{book_name} {author_name}"` strings to the full book record, then uses `rapidfuzz.process.extract()` with `fuzz.partial_ratio` to find the best fuzzy matches (score ≥ 60), tolerating typos and partial input.
  - **Genre**: same idea but with `process.extractOne()` against the list of distinct genres, matching the user's input to the closest real genre before querying books in it.

### `members.py`

- `active_members()` — returns every membership payment row where today's date falls between `coverage_start` and `expiry_date`.
- `is_active_member(member_id)` — loops through `active_members()` to find the given member's current tier, or `None` if they have none.
- `pay_membership()` — the trickiest logic here: if the member has no prior membership, the new one starts today. If they have one that's still valid, the new membership's `start_date` is set to the *existing* membership's expiry date, so paid time never overlaps (memberships stack sequentially rather than resetting).
- `no_of_books_issued_to(member_id)` — counts the member's currently-unreturned transactions, used to enforce the tier's book limit.

### `transactions.py`

- `issue_book()` — validates book availability and membership status/limit before inserting a new transaction row with `return_date` set to `None` (stored as `NULL`).
- `return_book()` — updates `return_date`, then:
  - Calculates late days via `is_late(due_date, return_date)` and inserts a `fines` row if late.
  - Asks about damage and inserts a separate `fines` row if damaged.
- `settle_fines()` — lists a member's unpaid fines, then either marks one specific fine as paid (`fine_id`) or all of them at once (`fine_id == 0`), using a two-table `update` with `fines.paid=1`.

### `graphing.py`

- `pie_chart()` and `plot_top_ten()` are shared rendering helpers — every chart function builds its data, then calls one of these instead of duplicating matplotlib boilerplate.
- `plot_top_ten()` wraps long labels with `textwrap.fill`, reverses the list order (matplotlib draws horizontal bars bottom-up, so reversing puts rank #1 at the top), and adds value labels via `plt.bar_label`.
- `top_ten_books()` / `top_ten_members()` — old-style implicit joins (`from transactions, books where ...`) rather than explicit `JOIN ... ON` syntax; grouped by primary key + display name for `ONLY_FULL_GROUP_BY` safety.
- `membership_chart()` — builds a tier → member-ID-list dictionary by calling `is_active_member()` per member, then converts counts into a pie chart.
- `genre_chart()` — tallies book counts per genre into a dictionary, then plots it.

### `main.py`

A single `while run:` loop:
1. Prints the menu.
2. Reads and validates the user's numeric choice.
3. Dispatches to an `elif` branch per option — some call functions from other modules directly, others (like options 8–13, 19) contain their own inline SQL for one-off reports that don't warrant a dedicated function.
4. Option 18 sanitizes custom queries by only permitting strings starting with `select` (case-insensitive), then wraps execution in a bare `try/except` so malformed SQL doesn't crash the program.
5. Option 20 closes the cursor and connection cleanly before breaking the loop.

### Known Limitations / Things Worth Improving

- No input sanitization beyond option 18's `SELECT`-only check — direct `int()` casts on IDs will crash the program on non-numeric input in most menu options.
- The shared global `cr`/`connect` from `db.py` means there's no way to run concurrent operations safely; fine for a single-user CLI tool.
- Several `main.py` options (8, 9, 11, 12, 13, 19) contain inline SQL rather than delegating to their respective modules — a possible refactor target for consistency.
- `next_id()` re-scans `max(id)` on every call rather than tracking state, which is simple but not efficient at scale.