from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Mapped, relationship
from extensions import db

from config import config, curr_env

DB_URL: str = "" if curr_env == "production" else "localhost"

association_table = db.Table(
    "association_table",
    db.Column("contest_cid", db.ForeignKey("contest.cid")),
    db.Column("contest_admin_user_name", db.ForeignKey("contest_admin.user_name")),
)

jury_association_table = db.Table(
    "jury_association_table",
    db.Column("contest_cid", db.ForeignKey("contest.cid")),
    db.Column("jury_user_name", db.ForeignKey("jury.user_name")),
)

book_contest_association_table = db.Table(
    "book_contest_association_table",
    db.Column("contest_cid", db.ForeignKey("contest.cid")),
    db.Column("book_name", db.ForeignKey("book.name")),
)

user_contest_association_table = db.Table(
    "user_contest_association_table",
    db.Column("contest_cid", db.ForeignKey("contest.cid")),
    db.Column("user_name", db.ForeignKey("user.user_name")),
)

@dataclass
class Contest(db.Model):
    __tablename__ = "contest"

    cid: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = db.Column(db.String(190), nullable=False)
    created_by: Mapped[Optional[str]] = db.Column(db.String(100), default=None)
    createdon: Mapped[datetime] = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    start_date: Mapped[datetime] = db.Column(db.DateTime, nullable=False)
    end_date: Mapped[datetime] = db.Column(db.DateTime, nullable=False)
    status: Mapped[Optional[bool]] = db.Column(db.Boolean, default=None)
    point_per_proofread: Mapped[Optional[int]] = db.Column(db.SmallInteger, default=None)
    point_per_validate: Mapped[Optional[int]] = db.Column(db.SmallInteger, default=None)
    lang: Mapped[Optional[str]] = db.Column(db.String(3), default=None)

    admins: Mapped[List["ContestAdmin"]] = relationship(
        "ContestAdmin", back_populates="contests", secondary=association_table
    )
    books: Mapped[List["Book"]] = relationship(
        "Book", back_populates="contests", secondary=book_contest_association_table
    )
    users: Mapped[List["User"]] = relationship(
        "User", back_populates="contests", secondary=user_contest_association_table
    )
    jury_members: Mapped[List["Jury"]] = relationship(
        "Jury", back_populates="contests", secondary=jury_association_table
    )

@dataclass
class ContestAdmin(db.Model):
    __tablename__ = "contest_admin"

    user_name: Mapped[str] = db.Column(db.String(190), primary_key=True, nullable=False)

    contests: Mapped[List["Contest"]] = relationship(
        "Contest", back_populates="admins", secondary=association_table
    )

@dataclass
class Book(db.Model):
    __tablename__ = "book"

    name: Mapped[str] = db.Column(db.String(190), nullable=False, primary_key=True)
    contests: Mapped[List["Contest"]] = relationship(
        "Contest", back_populates="books", secondary=book_contest_association_table
    )
    index_pages: Mapped[List["IndexPage"]] = relationship("IndexPage", back_populates="book")

@dataclass
class IndexPage(db.Model):
    __tablename__ = "index_page"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page_name: Mapped[str] = db.Column(db.String(190), nullable=False)
    book_name: Mapped[str] = db.Column(db.String(190), db.ForeignKey("book.name"))
    validator_username: Mapped[Optional[str]] = db.Column(db.String(190), db.ForeignKey("user.user_name"))
    proofreader_username: Mapped[Optional[str]] = db.Column(db.String(190), db.ForeignKey("user.user_name"))

    validate_time: Mapped[Optional[datetime]] = db.Column(db.DateTime, default=None)
    proofread_time: Mapped[Optional[datetime]] = db.Column(db.DateTime, default=None)
    v_revision_id: Mapped[Optional[int]] = db.Column(db.Integer, default=None)
    p_revision_id: Mapped[Optional[int]] = db.Column(db.Integer, default=None)

    book: Mapped["Book"] = relationship("Book", back_populates="index_pages", foreign_keys=[book_name])
    validator: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[validator_username],
        back_populates="validated_pages",
    )
    proofreader: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[proofreader_username],
        back_populates="proofread_pages",
    )
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="page")

@dataclass
class User(db.Model):
    __tablename__ = "user"

    user_name: Mapped[str] = db.Column(db.String(190), primary_key=True, nullable=False)

    contests: Mapped[List["Contest"]] = relationship(
        "Contest", back_populates="users", secondary=user_contest_association_table
    )
    proofread_pages: Mapped[List["IndexPage"]] = relationship(
        "IndexPage",
        back_populates="proofreader",
        foreign_keys="[IndexPage.proofreader_username]",
    )
    validated_pages: Mapped[List["IndexPage"]] = relationship(
        "IndexPage",
        back_populates="validator",
        foreign_keys="[IndexPage.validator_username]",
    )
    reviews: Mapped[List["Review"]] = relationship("Review", back_populates="reviewer")

@dataclass
class Jury(db.Model):
    __tablename__ = "jury"

    user_name: Mapped[str] = db.Column(db.String(190), primary_key=True, nullable=False)

    contests: Mapped[List["Contest"]] = relationship(
        "Contest", back_populates="jury_members", secondary=jury_association_table
    )

@dataclass
class Review(db.Model):
    __tablename__ = "review"

    id: Mapped[int] = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page_id: Mapped[int] = db.Column(db.Integer, db.ForeignKey("index_page.id"), nullable=False)
    reviewer_id: Mapped[str] = db.Column(db.String(190), db.ForeignKey("user.user_name"), nullable=False)
    review_text: Mapped[Optional[str]] = db.Column(db.String(500), nullable=True)
    review_date: Mapped[datetime] = db.Column(db.DateTime, default=datetime.utcnow)

    page: Mapped["IndexPage"] = relationship("IndexPage", back_populates="reviews")
    reviewer: Mapped["User"] = relationship("User", back_populates="reviews")
