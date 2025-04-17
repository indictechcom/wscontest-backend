from typing import Dict, List, Optional

from pywikisource import WikiSourceApi
import datetime as dt
from pytz import timezone
from models import Contest, Book, IndexPage, User
from dateutil import parser
from extensions import db  # Import db from extensions instead

def run():
    contests = Contest.query.all()
    user_agent = "IndicWikisourceContest/1.1 (Development; https://example.org/IndicWikisourceContest/;) pywikisource/0.0.5"

    for contest in contests:
        if dt.datetime.today() > contest.end_date:
            contest.status = False            
        if contest.status == False:
            continue 
        elif contest.status == True:
            ws: WikiSourceApi = WikiSourceApi(contest.lang, user_agent)

            books = Book.query.filter_by(cid=contest.cid).all()

            for book in books:
                try:
                    page_list: List[str] = ws.createdPageList(book.name)

                    for page in page_list:
                        ipage: IndexPage = IndexPage(book_name=book.name, page_name=page)
                        response: Dict = ws.pageStatus(page)

                        if response['proofread'] is not None:
                            user = User.query.filter_by(user_name=response["proofread"]["user"], cid=contest.cid).first()
                            if not user:
                                user = User(user_name=response["proofread"]["user"], cid=contest.cid)
                                db.session.add(user)
                            ipage.proofreader_username = user.user_name
                            proofread_time: dt.datetime = parser.parse(response["proofread"]["timestamp"])
                            ipage.proofread_time = proofread_time.strftime('%Y-%m-%d %H:%M:%S')
                            ipage.p_revision_id = response["proofread"]["revid"]

                        if response['validate'] is not None:
                            user = User.query.filter_by(user_name=response["validate"]["user"], cid=contest.cid).first()
                            if not user:
                                user = User(user_name=response["validate"]["user"], cid=contest.cid)
                                db.session.add(user)
                            ipage.validator_username = user.user_name
                            validate_time: dt.datetime = parser.parse(response["validate"]["timestamp"])
                            ipage.validate_time = validate_time.strftime('%Y-%m-%d %H:%M:%S')
                            ipage.v_revision_id = response["validate"]["revid"]

                        db.session.add(ipage)

                except Exception as e:
                    print(f"Error in {contest.name} contest: {e}")

    db.session.commit()

if __name__ == "__main__":
    run()
