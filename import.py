import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    b = open("books.csv")
    reader = csv.reader(b)
    next (reader) #skip header row
    for isbn, title, author, publication in reader:
#        print(f"isbn {isbn} title {title} author {author} publication {publication}")   
        db.execute("INSERT INTO books (isbn, title, author, publication) VALUES (:isbn, :title, :author, :publication)", {"isbn": isbn, "title": title, "author": author, "publication": publication})
    db.commit()

if __name__ == "__main__":
    main()
