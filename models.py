from dataclasses import dataclass
from datetime import datetime
from extensions import db

from config import config, curr_env

DB_URL = "" if curr_env == "production" else "localhost"

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

@dataclass
class Contest(db.Model):
    __tablename__ = "contest"

    cid = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(190), nullable=False)
    created_by = db.Column(db.String(100), default=None)
    createdon = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.Boolean, default=None)
    point_per_proofread = db.Column(db.SmallInteger, default=None)
    point_per_validate = db.Column(db.SmallInteger, default=None)
    lang = db.Column(db.String(3), default=None)

    admins = db.relationship(
        "ContestAdmin", back_populates="contests", secondary=association_table
    )
    books = db.relationship("Book", back_populates="contest")
    users = db.relationship("User", back_populates="contests")
    jury_members = db.relationship(
        "Jury", back_populates="contests", secondary=jury_association_table
    )

class ContestAdmin(db.Model):
    __tablename__ = "contest_admin"

    user_name = db.Column(db.String(190), primary_key=True, nullable=False)
    cid = db.Column(db.Integer, db.ForeignKey("contest.cid"))

    contests = db.relationship(
        "Contest", back_populates="admins", secondary=association_table
    )

class Book(db.Model):
    __tablename__ = "book"

    cid = db.Column(db.Integer, db.ForeignKey("contest.cid"))
    contest = db.relationship("Contest", back_populates="books")
    name = db.Column(db.String(190), nullable=False, primary_key=True)
    index_pages = db.relationship("IndexPage", back_populates="book")

@dataclass
class IndexPage(db.Model):
    __tablename__ = "index_page"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page_name = db.Column(db.String(190), nullable=False)
    book_name = db.Column(db.String(190), db.ForeignKey("book.name"))
    validator_username = db.Column(db.String(190), db.ForeignKey("user.user_name"))
    proofreader_username = db.Column(db.String(190), db.ForeignKey("user.user_name"))

    validate_time = db.Column(db.DateTime, default=None)
    proofread_time = db.Column(db.DateTime, default=None)
    v_revision_id = db.Column(db.Integer, default=None)
    p_revision_id = db.Column(db.Integer, default=None)

    book = db.relationship("Book", back_populates="index_pages", foreign_keys=[book_name])
    validator = db.relationship(
        "User",
        foreign_keys=[validator_username],
        back_populates="validated_pages",
    )
    proofreader = db.relationship(
        "User",
        foreign_keys=[proofreader_username],
        back_populates="proofread_pages",
    )
    reviews = db.relationship("Review", back_populates="page")

class User(db.Model):
    __tablename__ = "user"

    user_name = db.Column(db.String(190), primary_key=True, nullable=False)
    cid = db.Column(db.Integer, db.ForeignKey("contest.cid"))

    contests = db.relationship("Contest", back_populates="users")
    proofread_pages = db.relationship(
        "IndexPage",
        back_populates="proofreader",
        foreign_keys="[IndexPage.proofreader_username]",
    )
    validated_pages = db.relationship(
        "IndexPage",
        back_populates="validator",
        foreign_keys="[IndexPage.validator_username]",
    )
    reviews = db.relationship("Review", back_populates="reviewer")

class Jury(db.Model):
    __tablename__ = "jury"

    user_name = db.Column(db.String(190), primary_key=True, nullable=False)

    contests = db.relationship(
        "Contest", back_populates="jury_members", secondary=jury_association_table
    )

class Review(db.Model):
    __tablename__ = "review"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    page_id = db.Column(db.Integer, db.ForeignKey("index_page.id"), nullable=False)
    reviewer_id = db.Column(db.String(190), db.ForeignKey("user.user_name"), nullable=False)
    review_text = db.Column(db.String(500), nullable=True)
    review_date = db.Column(db.DateTime, default=datetime.utcnow)

    page = db.relationship("IndexPage", back_populates="reviews")
    reviewer = db.relationship("User", back_populates="reviews")
