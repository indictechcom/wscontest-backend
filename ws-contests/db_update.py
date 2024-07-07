from pywikisource import WikiSourceApi
import json
import datetime as dt
from pytz import timezone
from models import Contest, ContestBook, IndexPage, Session

session = Session()

# Fetch active contests from the database
contests = session.query(Contest).filter_by(status=True).all()

user_agent = "IndicWikisourceContest/1.1 (https://example.org/IndicWikisourceContest/;) pywikisource/0.0.5"

for contest in contests:
    con = {}
    ws = WikiSourceApi(contest.lang, user_agent)

    # Fetch contest books related to the contest
    books = session.query(ContestBook).filter_by(cid=contest.cid).all()

    for book in books:
        try:
            con[book.name] = {}
            page_list = ws.createdPageList(book.name.split(':')[1])

            for page in page_list:
                con[book.name][page] = {}
                con[book.name][page] = ws.pageStatus(page)
        except Exception as e: 
            print(f"Error in {contest.name} contest: {e}")

    con["LastUpdate"] = dt.datetime.now(timezone('UTC')).strftime("%A, %d. %B %Y %I:%M%p") + ' UTC'

     

# Close the session
session.close()
