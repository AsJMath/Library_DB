# FILES
from db import cr, connect

# MODULES
import webbrowser
import urllib.parse
from tabulate import tabulate

# PARTS OF A URL
"""
https://www.example.com:443/library/books?genre=fiction&sort=title#results
1. Scheme [https://] - Tells the OS/browser how to communicate, i.e. what protocol to use
2. Host [www.example.com] - The address/server being connected to
3. Port [:443] - Directs data to the correct application
4. Path [/library/books] - A specifice source or path within that webpage
5. Query String [?genre=fiction&sort=title] - Starts with a ?; extra constraints and parameters passed to the server, formatted as key=value pairs seperated by &
6. Fragment [#result] - Points to a specific section within the page (handles within the client application itself and is never sent to the server); entire result frmo 1-5 is sent to the server and the client application selectively picks the required fragment
"""

# COROLLARY TO mailto: URL
"""
mailto:aditi@example.com?subject=Library%20Fine%20Notice&body=Hi
1. Scheme = mailto:
2. Host ≈ Address = aditi@example.com
3. Port - Ommited
4. Path - Ommited (doesn't apply to the context of mails)
5. Query String = ?subject=Library%20Fine%20Notice&body=Hi
6. Fragment - Ommited
"""

def send_mail(to, subject, body, cc=None, bcc=None):
    params = {'subject': subject, 'body': body}
    if cc:
        params['cc'] = cc
    if bcc:
        params['bcc'] = bcc

    # urllib.parse.urlencode helps to convert a dictionary to a Query String (Refer 5. of PARTS OF URL and COROLLARY TO mailto: URL)
    # .urlencode handles only the structure of the encoding; it has no information of what kind of encoding has to be done [MECHANICAL STRUCTURE]
    # quote_via=urllib.parse.quote tells the .urlenode function what kind of encoding is to be done [STRATEGY OF ENCODING]
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    # The actual URL being sent (Refer COROLLARY TO mailto: URL), formatted with f-strings ()
    mailto_url = f"mailto:{to}?{query}"

    # webbrowser.open() is not for webpages alone; it merely hands a URL to the OS and lets the OS decide what to do with it. 
    # Thus, the opening of a mail application when executing a mailto: URL is handled by the OS; webbrowser.open() hands that link over to the OS
    # The OS receives the URL and matches the scheme (https:// or mailto:) against its internal registery and then decides what to do (open the default web browser or the mail application)
    webbrowser.open(mailto_url)

# case must either be 'due today' or 'overdue'
def mail_body(member_name, books:list, case):
    book_sequence=""
    i=1
    for book in books:
        book_sequence+=f"{i}. {book}\n"
        i+=1

    subject=f"""
Hi {member_name}. This automated message is to inform you that the following books in your possession are {case}.
{book_sequence}Please return them by today at your convenience.
"""
    return subject

# Groups books by member, then drafts one email per member listing all their books.
# Reused for books due today and overdue books in main.py
def draft_group_emails(rows, subject_line, case):
    # 'rows' comes from two different call sites with different column counts, but both share the same first 4 columns in the same order:
    #   row[0] = transaction_id   (unused here)
    #   row[1] = book_name
    #   row[2] = member_id
    #   row[3] = member_name

    # Due Today sends 5 columns: (transaction_id, book_name, member_id, member_name, issue_date)
    # Overdue sends 6 columns: (transaction_id, book_name, member_id, member_name, due_date, days_delayed)

    # Since this function only reads row[1] through row[3], the extra trailing column(s) on either side are simply ignored, thus no unpacking mismatch.

    grouped_members={}
    for row in rows:
        book_name, member_id, member_name = row[1], row[2], row[3]
        if member_id not in grouped_members:
            grouped_members[member_id] = {"name": member_name, "books": []}
        grouped_members[member_id]["books"].append(book_name)

    index=0
    for member_id, info in grouped_members.items():
        cr.execute("select email_address from members where member_id=%s", (member_id,))
        email_address=cr.fetchone()[0]
        member_name=info["name"]
        books=info["books"]
        index+=1

        print(f"Drafting email to {member_name}...")
        send_mail(to=email_address, subject=subject_line, body=mail_body(member_name, books, case=case))
        if index < len(grouped_members):
            input("Press Enter to draft the next email...")