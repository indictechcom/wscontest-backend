from typing import Dict, List, Optional, Any

from pywikisource import WikiSourceApi
import datetime as dt
from pytz import timezone
from models import Contest, Book, IndexPage, User
from dateutil import parser
from extensions import db 
from app import app 

def run() -> None:
    print("Starting db_update script...")
    with app.app_context():  
        print("Application context established")
        contests: List[Contest] = Contest.query.all()
        print(f"Found {len(contests)} contests in database")
        user_agent: str = "IndicWikisourceContest/1.1 (Development; https://example.org/IndicWikisourceContest/;) pywikisource/0.0.5"

        for contest in contests:
            print(f"\nProcessing contest: {contest.name} (ID: {contest.cid})")
            if dt.datetime.today() > contest.end_date:
                contest.status = False
                print(f"Contest {contest.name} has ended, setting status to False")
            if contest.status == False:
                print(f"Skipping contest {contest.name} - status is False")
                continue 
            elif contest.status == True:
                print(f"Processing active contest: {contest.name}")
                ws: WikiSourceApi = WikiSourceApi(contest.lang, user_agent)

                books: List[Book] = contest.books
                print(f"Found {len(books)} books for contest {contest.name}")

                for book in books:
                    print(f"  Processing book: {book.name}")
                    try:
                        page_list: List[str] = ws.createdPageList(book.name)
                        print(f"    Found {len(page_list)} pages for book {book.name}")

                        for page in page_list:
                            print(f"      Processing page: {page}")
                            ipage: IndexPage = IndexPage(book_name=book.name, page_name=page)
                            response: Dict[str, Any] = ws.pageStatus(page)
                            print(f"        Page status response: {response}")

                            if response['proofread'] is not None:
                                print(f"        Processing proofread data for user: {response['proofread']['user']}")
                                user: Optional[User] = User.query.filter_by(user_name=response["proofread"]["user"]).first()
                                if not user:
                                    print(f"        Creating new user: {response['proofread']['user']}")
                                    user = User(user_name=response["proofread"]["user"])
                                    db.session.add(user)
                                else:
                                    print(f"        Found existing user: {user.user_name}")
                                # Add user to contest if not already in it
                                if contest not in user.contests:
                                    print(f"        Adding user {user.user_name} to contest {contest.name}")
                                    user.contests.append(contest)
                                else:
                                    print(f"        User {user.user_name} already in contest {contest.name}")
                                ipage.proofreader_username = user.user_name
                                proofread_time: dt.datetime = parser.parse(response["proofread"]["timestamp"])
                                ipage.proofread_time = proofread_time.strftime('%Y-%m-%d %H:%M:%S')
                                ipage.p_revision_id = response["proofread"]["revid"]

                            if response['validate'] is not None:
                                print(f"        Processing validate data for user: {response['validate']['user']}")
                                user: Optional[User] = User.query.filter_by(user_name=response["validate"]["user"]).first()
                                if not user:
                                    print(f"        Creating new user: {response['validate']['user']}")
                                    user = User(user_name=response["validate"]["user"])
                                    db.session.add(user)
                                else:
                                    print(f"        Found existing user: {user.user_name}")
                                # Add user to contest if not already in it
                                if contest not in user.contests:
                                    print(f"        Adding user {user.user_name} to contest {contest.name}")
                                    user.contests.append(contest)
                                else:
                                    print(f"        User {user.user_name} already in contest {contest.name}")
                                ipage.validator_username = user.user_name
                                validate_time: dt.datetime = parser.parse(response["validate"]["timestamp"])
                                ipage.validate_time = validate_time.strftime('%Y-%m-%d %H:%M:%S')
                                ipage.v_revision_id = response["validate"]["revid"]

                            print(f"        Adding IndexPage to session: {ipage.page_name}")
                            db.session.add(ipage)

                    except Exception as e:
                        print(f"Error in {contest.name} contest, book {book.name}: {e}")

        print("\nCommitting all changes to database...")
        db.session.commit()
        print("Database update completed successfully!")

if __name__ == "__main__":
    print("=== WikiSource Contest Database Update Script ===")
    try:
        run()
    except Exception as e:
        print(f"Script failed with error: {e}")
        import traceback
        traceback.print_exc()
    print("=== Script execution completed ===")
