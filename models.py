from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Table,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from config import config, curr_env

# Create the base class
engine = create_engine(config["SQL_URI"])
Session = sessionmaker(bind=engine)
Base = declarative_base()
DB_URL = "" if curr_env == "production" else "localhost"

association_table = Table(
    "association_table",
    Base.metadata,
    Column("contest_cid", ForeignKey("contest.cid")),
    Column("contest_admin_user_name", ForeignKey("contest_admin.user_name")),
)


# Define the contests table
class Contest(Base):
    __tablename__ = "contest"

    cid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(190), unique=True, nullable=False)
    created_by = Column(String(100), default=None)
    createdon = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Boolean, default=None)
    point_per_proofread = Column(SmallInteger, default=None)
    point_per_validate = Column(SmallInteger, default=None)
    lang = Column(String(3), default=None)

    # Relationships
    admins = relationship(
        "ContestAdmin", back_populates="contests", secondary=association_table
    )
    books = relationship("ContestBook", back_populates="contest")
    users = relationship("User", back_populates="contests")


# Define the ContestAdmin table
class ContestAdmin(Base):
    __tablename__ = "contest_admin"

    user_name = Column(String(190), primary_key=True, nullable=False)
    cid = Column(Integer, ForeignKey("contest.cid"))

    # Relationships
    contests = relationship(
        "Contest", back_populates="admins", secondary=association_table
    )


class ContestBook(Base):
    __tablename__ = "contest_book"

    cid = Column(Integer, ForeignKey("contest.cid"))
    contest = relationship("Contest", back_populates="books")
    name = Column(String(190), nullable=False, primary_key=True)
    index_pages = relationship("IndexPage", back_populates="contest_book")


# Define the IndexPage table
class IndexPage(Base):
    __tablename__ = "index_page"

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_book_name = Column(String(190), ForeignKey("contest_book.name"))
    validator_username = Column(String(190), ForeignKey("user.user_name"))
    proofreader_username = Column(String(190), ForeignKey("user.user_name"))

    validate_time = Column(DateTime, default=None)
    proofread_time = Column(DateTime, default=None)
    v_revision_id = Column(Integer, default=None)
    p_revision_id = Column(Integer, default=None)

    # Relationships
    contest_book = relationship(
        "ContestBook", back_populates="index_pages", foreign_keys=[contest_book_name]
    )
    validator = relationship(
        "User",
        foreign_keys=[validator_username],
        back_populates="validated_pages",
    )
    proofreader = relationship(
        "User",
        foreign_keys=[validator_username],
        back_populates="proofread_pages",
    )


# Define the User table
class User(Base):
    __tablename__ = "user"

    user_name = Column(String(190), primary_key=True, nullable=False)
    cid = Column(Integer, ForeignKey("contest.cid"))

    # Relationships
    contests = relationship("Contest", back_populates="users")
    proofread_pages = relationship(
        "IndexPage",
        back_populates="proofreader",
        foreign_keys="[IndexPage.proofreader_username]",
    )
    validated_pages = relationship(
        "IndexPage",
        back_populates="validator",
        foreign_keys="[IndexPage.validator_username]",
        overlaps="proofreader",
    )


# create all tables
Base.metadata.create_all(engine)
