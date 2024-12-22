from typing import Dict, List, Optional

from pywikisource import WikiSourceApi
import datetime as dt
from models import Contest, Book, IndexPage, Session, User
from dateutil import parser

def run() -> None:
    session = Session()

    contests: List[Contest] = session.query(Contest).all()
    user_agent: str = "IndicWikisourceContest/1.1 (Development; https://example.org/IndicWikisourceContest/;) pywikisource/0.0.5"

    for contest in contests:
        # print(contest.name)
        if dt.datetime.today() > contest.end_date:
            contest.status = False            
        if contest.status == False:
            continue 
        elif contest.status == True:
            ws: WikiSourceApi = WikiSourceApi(contest.lang, user_agent)

            books: List[Book] = session.query(Book).filter_by(cid=contest.cid).all()

            for book in books:
                try:
                    page_list: List[str] = ws.createdPageList(book.name)
                    # print(page_list)

                    for page in page_list:
                        ipage: IndexPage = IndexPage(book_name=book.name, page_name=page)
                        response: Dict = ws.pageStatus(page)
                        # print(response)

                        if response['proofread'] is not None:
                            user: Optional[User] = session.query(User).filter_by(user_name=response["proofread"]["user"], cid=contest.cid).first()
                            if not user:
                                user = User(user_name=response["proofread"]["user"], cid=contest.cid)
                                session.add(user)
                            ipage.proofreader_username = user.user_name
                            proofread_time: dt.datetime = parser.parse(response["proofread"]["timestamp"])
                            ipage.proofread_time = proofread_time.strftime('%Y-%m-%d %H:%M:%S')
                            ipage.p_revision_id = response["proofread"]["revid"]

                        if response['validate'] is not None:
                            user: Optional[User] = session.query(User).filter_by(user_name=response["validate"]["user"], cid=contest.cid).first()
                            if not user:
                                user = User(user_name=response["validate"]["user"], cid=contest.cid)
                                session.add(user)
                            ipage.validator_username = user.user_name
                            validate_time: dt.datetime = parser.parse(response["validate"]["timestamp"])
                            ipage.validate_time = validate_time.strftime('%Y-%m-%d %H:%M:%S')
                            ipage.v_revision_id = response["validate"]["revid"]

                        session.add(ipage)

                except Exception as e:
                    print(f"Error in {contest.name} contest: {e}")

        
    session.commit()

    session.close()

if __name__ == "__main__":
    run()
