from typing import Dict, List, Optional, Any
import logging
import sys

from pywikisource import WikiSourceApi
import datetime as dt
from pytz import timezone
from models import Contest, Book, IndexPage, User
from dateutil import parser
from extensions import db 
from app import app 

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('db_update.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__) 

def run() -> None:
    logger.info("Starting db_update script...")
    with app.app_context():  
        logger.info("Application context established")
        contests: List[Contest] = Contest.query.all()
        logger.info(f"Found {len(contests)} contests in database")
        user_agent: str = "IndicWikisourceContest/1.1 (Development; https://example.org/IndicWikisourceContest/;) pywikisource/0.0.5"

        for contest in contests:
            logger.info(f"Processing contest: {contest.name} (ID: {contest.cid})")
            if dt.datetime.today() > contest.end_date:
                contest.status = False
                logger.info(f"Contest {contest.name} has ended, setting status to False")
            if contest.status == False:
                logger.info(f"Skipping contest {contest.name} - status is False")
                continue 
            elif contest.status == True:
                logger.info(f"Processing active contest: {contest.name}")
                ws: WikiSourceApi = WikiSourceApi(contest.lang, user_agent)

                books: List[Book] = contest.books
                logger.info(f"Found {len(books)} books for contest {contest.name}")

                for book in books:
                    logger.info(f"Processing book: {book.name}")
                    try:
                        page_list: List[str] = ws.createdPageList(book.name)
                        logger.info(f"Found {len(page_list)} pages for book {book.name}")

                        for page in page_list:
                            logger.debug(f"Processing page: {page}")
                            ipage: IndexPage = IndexPage(book_name=book.name, page_name=page)
                            response: Dict[str, Any] = ws.pageStatus(page)
                            logger.debug(f"Page status response: {response}")

                            if response['proofread'] is not None:
                                logger.debug(f"Processing proofread data for user: {response['proofread']['user']}")
                                user: Optional[User] = User.query.filter_by(user_name=response["proofread"]["user"]).first()
                                if not user:
                                    logger.info(f"Creating new user: {response['proofread']['user']}")
                                    user = User(user_name=response["proofread"]["user"])
                                    db.session.add(user)
                                else:
                                    logger.debug(f"Found existing user: {user.user_name}")
                                # Add user to contest if not already in it
                                if contest not in user.contests:
                                    logger.info(f"Adding user {user.user_name} to contest {contest.name}")
                                    user.contests.append(contest)
                                else:
                                    logger.debug(f"User {user.user_name} already in contest {contest.name}")
                                ipage.proofreader_username = user.user_name
                                proofread_time: dt.datetime = parser.parse(response["proofread"]["timestamp"])
                                ipage.proofread_time = proofread_time.strftime('%Y-%m-%d %H:%M:%S')
                                ipage.p_revision_id = response["proofread"]["revid"]

                            if response['validate'] is not None:
                                logger.debug(f"Processing validate data for user: {response['validate']['user']}")
                                user: Optional[User] = User.query.filter_by(user_name=response["validate"]["user"]).first()
                                if not user:
                                    logger.info(f"Creating new user: {response['validate']['user']}")
                                    user = User(user_name=response["validate"]["user"])
                                    db.session.add(user)
                                else:
                                    logger.debug(f"Found existing user: {user.user_name}")
                                # Add user to contest if not already in it
                                if contest not in user.contests:
                                    logger.info(f"Adding user {user.user_name} to contest {contest.name}")
                                    user.contests.append(contest)
                                else:
                                    logger.debug(f"User {user.user_name} already in contest {contest.name}")
                                ipage.validator_username = user.user_name
                                validate_time: dt.datetime = parser.parse(response["validate"]["timestamp"])
                                ipage.validate_time = validate_time.strftime('%Y-%m-%d %H:%M:%S')
                                ipage.v_revision_id = response["validate"]["revid"]

                            logger.debug(f"Adding IndexPage to session: {ipage.page_name}")
                            db.session.add(ipage)

                    except Exception as e:
                        logger.error(f"Error in {contest.name} contest, book {book.name}: {e}")

        logger.info("Committing all changes to database...")
        db.session.commit()
        logger.info("Database update completed successfully!")

if __name__ == "__main__":
    logger.info("=== WikiSource Contest Database Update Script ===")
    try:
        run()
    except Exception as e:
        logger.error(f"Script failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
    logger.info("=== Script execution completed ===")
