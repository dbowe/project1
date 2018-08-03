import os

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
import psycopg2 
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
conn = psycopg2.connect (host = "54.227.240.7", user = "xswqlrsiueleeq", password = "0dca74419c585b275bfb66dc496a7f63f685166b0fe9eb9df9d354e80f2a8429", database = "d6vfal3rnfrjfc");
cur = conn.cursor()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signing_in", methods=["POST"])
def signing_in():
    username = request.form.get("username")
    password = request.form.get("password")

    cur.execute("SELECT user_id from users where username = %s AND password = %s", (username, password))
    if cur.rowcount == 0:
        ## No such users
        return render_template("index.html", additional_msg="Invalid username/password.  Please try again.")
    else :
        user = cur.fetchone()
        id = user[0]
        session["user_id"] = id
        session[id] = 1
        return render_template("booksearch.html", additional_msg="")

@app.route("/register", methods=["POST", "GET"])
def register():
    return render_template("register.html")

@app.route("/registered", methods=["POST"])
def registered():
    first = request.form.get("first")
    last = request.form.get("last")
    username = request.form.get("username")
    password = request.form.get("password")

    cur.execute("SELECT user_id FROM users WHERE username = %s", [username])
    if cur.rowcount == 0:
        cur.execute("INSERT INTO users (first, last, username, password) VALUES (%s, %s, %s, %s)", [first, last, username, password])
        conn.commit()
        cur.execute("SELECT user_id FROM users WHERE username = %s", [username])
        user = cur.fetchone()
        my_id = user[0]
        session["user_id"] = my_id
        session[my_id] = 1
        return render_template("booksearch.html",  additional_msg ="")
    else:
        return render_template("register.html", additional_msg="User already exists. Please try again.")

@app.route("/registered/<int:isloggedin>", methods=["POST", "GET"])
def user_registered(isloggedin):
    if 'user_id' in session:
        return render_template("booksearch.html", additional_msg = "Start a new search")
    else:
        return render_template("error.html", errmsg = "Please log in")
        

@app.route("/listbooks", methods=["POST"])
def listbooks():
    if 'user_id' in session:  
        isbn = request.form.get("isbn")
        title = request.form.get("title")
        author = request.form.get("author")

        if isbn == "" and title == "" and author == "" :
            return render_template("booksearch.html", additional_msg = "You must enter at least one search criteria")
        if title != "" :
            title = f"%{title}%"
        if isbn != "" :
            isbn = f"%{isbn}%"
        if author != "": 
            author = f"%{author}%"
        cur.execute("SELECT * from books WHERE isbn LIKE %s OR title ILIKE %s OR author ILIKE %s", (isbn, title,  author))
        books = cur.fetchall()
        if len(books) == 0:
            return render_template("booksearch.html", additional_msg="No books found with search criteria")
        else:
            session["booklist"] = books
            return render_template("listbooks.html", books = books, additional_msg="")
    else:
        return render_template("error.html", errmsg = "Please log in to search books")

@app.route("/bookdetails/<string:my_isbn>", methods=["POST", "GET"])
def bookdetails(my_isbn):
    # If user is logged in
    if 'user_id' in session:

        # Check for reviews from this site
        cur.execute("SELECT books.isbn, title, author, publication, review, rating from books  JOIN reviews ON reviews.isbn = books.isbn AND reviews.isbn = %s", [my_isbn]);

        # If there are no reviews, check for existance of book in database
        if cur.rowcount == 0:
            cur.execute("SELECT isbn, title, author, publication from books WHERE isbn = %s", [my_isbn]);
            # Return error if no book exists
            if cur.rowcount == 0:
                return render_template("error.html", errmsg="No such book")
        mybooks = cur.fetchall()
        res = requests.get("https://www.goodreads.com/book/review_counts.json", data=[("key","Gv8kJNdlJtebek4EQ0eQ"), ("isbns",my_isbn)])
        # Oops.  API request failed
        if res.status_code != 200:
            raise Exception ("Error: API request unsuccessful.")
        # API successful!  Return information
        else:
            data = res.json()
            book = data["books"][0]
            gr_cnt = book['ratings_count']
            gr_avg = book['average_rating']
            return render_template("bookdetails.html", books = mybooks, isbn = my_isbn, gr_avg = gr_avg, gr_cnt = gr_cnt)
    else:
        return render_template("error.html", errmsg = "Please log in to see book details")
    
@app.route("/api/<string:my_isbn>", methods=["GET"])
def ret_json(my_isbn):

    cur.execute("SELECT title, author, publication, review, rating FROM books JOIN reviews ON books.isbn = reviews.isbn AND books.isbn = %s", [my_isbn])
    if cur.rowcount == 0:
        cur.execute("SELECT title, author, publication FROM books WHERE books.isbn = %s", [my_isbn])
        if cur.rowcount == 0:
            return jsonify({"error": "No such book", "status_code": 404})
        else:
            book = cur.fetchone()
            return jsonify({
                    "title": book[0],
                    "author": book[1],
                    "publication": book[2],
                    "isbn": my_isbn,
                    "review_count": "0",
                    "average_score": "0",
                    "status_code": 200
                    })
    else:
        books = cur.fetchall()
        num = cur.rowcount
        sum = 0
        for i in range (num - 1):
            sum += books[i][4]
        avg_rating = sum / num 
        book = books[0]
        return jsonify({
                "title": book[0],
                "author": book[1],
                "publication": book[2],
                "isbn": my_isbn,
                "review_count": num,
                "average_score": avg_rating,
                "status_code": 200
                })


@app.route("/submitted", methods=["POST"])
def submitted():
    rating = request.form.get("rating")
    isbn = request.form.get("isbn")
    review = request.form.get("review")

    # if user is logged in
    if 'user_id' in session:
        my_id = session["user_id"]
        cur.execute("SELECT username FROM users WHERE user_id = %s", [my_id])
        current_user = cur.fetchone()
        cur.execute("SELECT user_id FROM reviews WHERE user_id = %s AND isbn = %s", [my_id, isbn])
        if cur.rowcount != 0:
            return render_template("listbooks.html", books = session["booklist"], additional_msg="You may only submit 1 review per book.")
        
        cur.execute("INSERT INTO reviews (user_id, isbn, review, rating) VALUES (%s, %s, %s, %s)", [my_id, isbn,  review, rating])
        conn.commit()
                               
        return render_template("listbooks.html", books = session["booklist"], additional_msg="Thank you for your review")
    else:
        return render_template("error.html", errmsg = "Please log in to submit a review")

@app.route("/logout", methods=["POST"])
def logout():
    if 'user_id' in session:
        id = session["user_id"]
        session[id] = 0;
        del session['user_id']
        return render_template("logout.html")
    else:
        return render_template("error.html", errmsg = "Not logged in .")
