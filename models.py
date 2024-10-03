from dataclasses import dataclass
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


@dataclass
class Contest(Base):
    __tablename__ = "contest"

    cid = Column(Integer, primary_key=True, autoincrement=True)
    name: str = Column(String(190), unique=True, nullable=False)
    created_by: str = Column(String(100), default=None)
    createdon: datetime = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_date: datetime = Column(DateTime, nullable=False)
    end_date: datetime = Column(DateTime, nullable=False)
    status: bool = Column(Boolean, default=None)
    point_per_proofread: int = Column(SmallInteger, default=None)
    point_per_validate: int = Column(SmallInteger, default=None)
    lang: str = Column(String(3), default=None)

    admins = relationship(
        "ContestAdmin", back_populates="contests", secondary=association_table
    )
    books = relationship("Book", back_populates="contest")
    users = relationship("User", back_populates="contests")


class ContestAdmin(Base):
    __tablename__ = "contest_admin"

    user_name = Column(String(190), primary_key=True, nullable=False)
    cid = Column(Integer, ForeignKey("contest.cid"))

    contests = relationship(
        "Contest", back_populates="admins", secondary=association_table
    )


class Book(Base):
    __tablename__ = "book"

    cid = Column(Integer, ForeignKey("contest.cid"))
    contest = relationship("Contest", back_populates="books")
    name = Column(String(190), nullable=False, primary_key=True)
    index_pages = relationship("IndexPage", back_populates="book")


@dataclass
class IndexPage(Base):
    __tablename__ = "index_page"

    id = Column(Integer, primary_key=True, autoincrement=True)
    page_name: str = Column(String(190), nullable=False)
    book_name = Column(String(190), ForeignKey("book.name"))
    validator_username = Column(String(190), ForeignKey("user.user_name"))
    proofreader_username = Column(String(190), ForeignKey("user.user_name"))

    validate_time = Column(DateTime, default=None)
    proofread_time = Column(DateTime, default=None)
    v_revision_id = Column(Integer, default=None)
    p_revision_id = Column(Integer, default=None)

    book = relationship("Book", back_populates="index_pages", foreign_keys=[book_name])
    validator = relationship(
        "User",
        foreign_keys=[validator_username],
        back_populates="validated_pages",
    )
    proofreader = relationship(
        "User",
        foreign_keys=[validator_username],
        overlaps="validator",
        back_populates="proofread_pages",
    )


class User(Base):
    __tablename__ = "user"

    user_name = Column(String(190), primary_key=True, nullable=False)
    cid = Column(Integer, ForeignKey("contest.cid"))

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


Base.metadata.create_all(engine)
