from pywikisource import WikiSourceApi
import json
import datetime as dt
from pytz import timezone
from models import Contest, Book, IndexPage, Session, User
from dateutil import parser
def run():
    session = Session()

    contests = session.query(Contest).all()
    user_agent = "IndicWikisourceContest/1.1 (Development; https://example.org/IndicWikisourceContest/;) pywikisource/0.0.5"

    for contest in contests:
        # print(contest.name)
        if dt.datetime.today() > contest.end_date:
            contest.status = False            
        if contest.status == False:
            continue 
        elif contest.status == True:
            ws = WikiSourceApi(contest.lang, user_agent)

            books = session.query(Book).filter_by(cid=contest.cid).all()

            for book in books:
                try:
                    page_list = ws.createdPageList(book.name)
                    # print(page_list)

                    for page in page_list:
                        ipage = IndexPage(book_name=book.name, page_name=page)
                        response = ws.pageStatus(page)
                        # print(response)

                        if response['proofread'] is not None:
                            user = session.query(User).filter_by(user_name=response["proofread"]["user"], cid=contest.cid).first()
                            if not user:
                                user = User(user_name=response["proofread"]["user"], cid=contest.cid)
                                session.add(user)
                            ipage.proofreader_username = user.user_name
                            proofread_time = parser.parse(response["proofread"]["timestamp"])
                            ipage.proofread_time = proofread_time.strftime('%Y-%m-%d %H:%M:%S')
                            ipage.p_revision_id = response["proofread"]["revid"]

                        if response['validate'] is not None:
                            user = session.query(User).filter_by(user_name=response["validate"]["user"], cid=contest.cid).first()
                            if not user:
                                user = User(user_name=response["validate"]["user"], cid=contest.cid)
                                session.add(user)
                            ipage.validator_username = user.user_name
                            validate_time = parser.parse(response["validate"]["timestamp"])
                            ipage.validate_time = validate_time.strftime('%Y-%m-%d %H:%M:%S')
                            ipage.v_revision_id = response["validate"]["revid"]

                        session.add(ipage)

                except Exception as e:
                    print(f"Error in {contest.name} contest: {e}")

        
    session.commit()

    session.close()

if __name__ == "__main__":
    run()
