# FILES
from db import cr  # , connect, next_id
from members import is_active_member

# MODULES
import matplotlib.pyplot as plt
import textwrap

def pie_chart(fractions_sequence, label_sequence, color_list=None, title=None, explode_sequence=None):
    plt.pie(fractions_sequence, labels=label_sequence, autopct='%1.1f%%', startangle=90, pctdistance=0.85, labeldistance=1.1, colors=color_list, explode=explode_sequence)
    plt.title(title)
    plt.tight_layout()
    plt.show()
 
def plot_top_ten(labels, values, xlabel, ylabel, title):
    wrapped_labels = []
    for name in labels:
        wrapped_labels.append(textwrap.fill(name, width=12))
 
    # first items appear at the bottom of a barchart in matplot lib. The below 3 lines fix that.
    wrapped_labels.reverse()
    values_reversed = values.copy()
    values_reversed.reverse()
 
    plt.figure(figsize=(10, 6))
    bars = plt.barh(wrapped_labels, values_reversed, color="skyblue")
    plt.bar_label(bars, label_type="edge", color="white", padding=2)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(axis="x", alpha=0.3)

    manager=plt.gcf().canvas.manager
    manager.set_window_title(title)

    plt.subplots_adjust(left=0.3)
    plt.tight_layout()
    plt.show()

# Doesn't consider if the book is active or not; relies on historical data and can be useful to the librarian to find out of the book should be reactivated
def top_ten_books():
    cr.execute("select books.book_name, count(transactions.transaction_id) from transactions, books where transactions.book_id=books.book_id group by books.book_id, books.book_name order by count(transactions.transaction_id) desc limit 10")
    result = cr.fetchall()
 
    labels = []
    values = []
    for row in result:
        labels.append(row[0])
        values.append(row[1])
 
    plot_top_ten(labels, values, "Number of times issued", "Books", "Top 10 Books")
 
def top_ten_members():
    cr.execute("select members.member_name, count(transactions.transaction_id) from transactions, members where transactions.member_id=members.member_id group by members.member_id, members.member_name order by count(transactions.transaction_id) desc limit 10")
    result = cr.fetchall()
 
    labels = []
    values = []
    for row in result:
        labels.append(row[0])
        values.append(row[1])
 
    plot_top_ten(labels, values, "Number of times issued", "Members", "Top 10 Members")

def membership_chart():
    cr.execute("select member_id from members")
    member_ids=cr.fetchall() # List of tuples with one element

    split = {
        "bronze": [],
        "silver": [],
        "gold": [],
        "student": [],
        "none": []
    }

    for row in member_ids:
        id=row[0]
        tier=is_active_member(id) # Returns either a string or None
        if tier is None:
            split["none"].append(id)
        else:
            split[tier].append(id)

    divisions=[]
    tiers=[]
    for key in split:
        divisions.append(len(split[key])) # len(split[key]) gives the number of member ids for each tier
        tiers.append(key.capitalize())
    pie_chart(divisions, tiers, color_list=["#CD7F32", "#C4C4C4", "#D4AF37", "#84A1DB", "#DE1818A4"], title="Membership Chart")

# Generates a particular piechart with the parameter target_genre exploded
# Default value none allows for situation where no genre is generated
def genre_chart(target_genre=None):
    cr.execute("select distinct genre from books")
    result=cr.fetchall()
    all_genres=dict()
    for row in result:
        genre=row[0]
        # Initially sets the number of the genres to zero
        all_genres[genre]=0

    # List of all the genres, the labels next to the pie chart
    genres=list(all_genres.keys())

    explode_list=[]
    for genre in genres:
        if genre == target_genre:
            explode_list.append(0.2)
        else:
            explode_list.append(0)

    cr.execute("select book_id, genre from books where active=1")
    result=cr.fetchall() # Nested tuple like ((<book_id>, <genre>),)

    for record in result:
        all_genres[record[1]]+=1
    # all_genres is a dictionary of format {<genre>:<count>}

    # Sequence of all the ratios of books in terms of their count
    divisions=all_genres.values()
    pie_chart(divisions, genres, title="Genre Chart", explode_sequence=explode_list)

def revenue_source_chart():
    revenue_sources={
        "fines": 0,
        "membership": 0
    }

    cr.execute("select sum(amount) from fines")
    revenue_sources["fines"]=float(cr.fetchone()[0])

    cr.execute("select sum(amount) from membership_payments")
    revenue_sources["membership"]=float(cr.fetchone()[0])
    # cr.fetchone() returns a nested tuple with one element, the sum of the amount

    pie_chart(label_sequence=revenue_sources.keys(), fractions_sequence=revenue_sources.values(), title="Revenue Chart")