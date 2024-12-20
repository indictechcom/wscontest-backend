from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

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
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Mapped, mapped_column

from config import config, curr_env

engine = create_engine(config["SQL_URI"])
Session = sessionmaker(bind=engine)
Base = declarative_base()
DB_URL: str = "" if curr_env == "production" else "localhost"

association_table = Table(
    "association_table",
    Base.metadata,
    Column("contest_cid", ForeignKey("contest.cid")),
    Column("contest_admin_user_name", ForeignKey("contest_admin.user_name")),
)


@dataclass
class Contest(Base):
    __tablename__ = "contest"

    cid: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(190), unique=True, nullable=False)
    created_by: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    createdon: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    start_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[Optional[bool]] = mapped_column(Boolean, default=None)
    point_per_proofread: Mapped[Optional[int]] = mapped_column(SmallInteger, default=None)
    point_per_validate: Mapped[Optional[int]] = mapped_column(SmallInteger, default=None)
    lang: Mapped[Optional[str]] = mapped_column(String(3), default=None)

    admins: Mapped[List["ContestAdmin"]] = relationship(
        "ContestAdmin", back_populates="contests", secondary=association_table
    )
    books: Mapped[List["Book"]] = relationship("Book", back_populates="contest")
    users: Mapped[List["User"]] = relationship("User", back_populates="contests")


class ContestAdmin(Base):
    __tablename__ = "contest_admin"

    user_name: Mapped[str] = mapped_column(String(190), primary_key=True, nullable=False)
    cid: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contest.cid"))

    contests: Mapped[List[Contest]] = relationship(
        "Contest", back_populates="admins", secondary=association_table
    )


class Book(Base):
    __tablename__ = "book"

    cid: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contest.cid"))
    contest: Mapped[Optional[Contest]] = relationship("Contest", back_populates="books")
    name: Mapped[str] = mapped_column(String(190), nullable=False, primary_key=True)
    index_pages: Mapped[List["IndexPage"]] = relationship("IndexPage", back_populates="book")


@dataclass
class IndexPage(Base):
    __tablename__ = "index_page"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    page_name: Mapped[str] = mapped_column(String(190), nullable=False)
    book_name: Mapped[str] = mapped_column(String(190), ForeignKey("book.name"))
    validator_username: Mapped[Optional[str]] = mapped_column(String(190), ForeignKey("user.user_name"))
    proofreader_username: Mapped[Optional[str]] = mapped_column(String(190), ForeignKey("user.user_name"))

    validate_time: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    proofread_time: Mapped[Optional[datetime]] = mapped_column(DateTime, default=None)
    v_revision_id: Mapped[Optional[int]] = mapped_column(Integer, default=None)
    p_revision_id: Mapped[Optional[int]] = mapped_column(Integer, default=None)

    book: Mapped[Book] = relationship("Book", back_populates="index_pages", foreign_keys=[book_name])
    validator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[validator_username],
        back_populates="validated_pages",
    )
    proofreader: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[validator_username],
        overlaps="validator",
        back_populates="proofread_pages",
    )


class User(Base):
    __tablename__ = "user"

    user_name: Mapped[str] = mapped_column(String(190), primary_key=True, nullable=False)
    cid: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("contest.cid"))

    contests: Mapped[List[Contest]] = relationship("Contest", back_populates="users")
    proofread_pages: Mapped[List[IndexPage]] = relationship(
        "IndexPage",
        back_populates="proofreader",
        foreign_keys="[IndexPage.proofreader_username]",
    )
    validated_pages: Mapped[List[IndexPage]] = relationship(
        "IndexPage",
        back_populates="validator",
        foreign_keys="[IndexPage.validator_username]",
        overlaps="proofreader",
    )


Base.metadata.create_all(engine)
