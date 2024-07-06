from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Create the base class
Base = declarative_base()


# Define the contests table
class Contest(Base):
    __tablename__ = "contests"

    cid = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(190), unique=True, nullable=False)
    created_by = Column(String(100), default=None)
    createdon = Column(DateTime, nullable=False, default=datetime.utcnow)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    cstatus = Column(Boolean, default=None)
    p_point = Column(SmallInteger, default=None)
    v_point = Column(SmallInteger, default=None)
    lang = Column(String(3), default=None)

    # Relationships
    admins = relationship("ContestAdmin", back_populates="contest")
    books = relationship("ContestBook", back_populates="contest")
    unlisted_users = relationship("UnlistedUser", back_populates="contest")


# Define the ContestAdmin table
class ContestAdmin(Base):
    __tablename__ = "ContestAdmin"

    cid = Column(Integer, ForeignKey("contests.cid"), primary_key=True)
    user_name = Column(String(190), primary_key=True, nullable=False)

    # Relationships
    contest = relationship("Contest", back_populates="admins")


# Define the IndexPages table
class IndexPage(Base):
    __tablename__ = "IndexPages"

    idbp = Column(Integer, primary_key=True, autoincrement=True)
    index_name = Column(String(200, collation="utf8mb3_bin"), nullable=False)
    index_page = Column(String(100, collation="utf8mb3_bin"), nullable=False)
    icode = Column(Integer, nullable=False)

    # Relationships
    books = relationship("ContestBook", back_populates="index_page")


# Define the ContestBooks table
class ContestBook(Base):
    __tablename__ = "ContestBooks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cid = Column(Integer, ForeignKey("contests.cid"), nullable=False)
    idbp = Column(Integer, ForeignKey("IndexPages.idbp"), nullable=False)
    validator = Column(String(190), default=None)
    proofreader = Column(String(190), default=None)
    validate_time = Column(DateTime, default=None)
    proofread_time = Column(DateTime, default=None)
    v_revision_id = Column(Integer, default=None)
    p_revision_id = Column(Integer, default=None)

    # Relationships
    contest = relationship("Contest", back_populates="books")
    index_page = relationship("IndexPage", back_populates="books")


# Define the UnlistedUser table
class UnlistedUser(Base):
    __tablename__ = "UnlistedUser"

    cid = Column(Integer, ForeignKey("contests.cid"), primary_key=True)
    user_name = Column(String(190), primary_key=True, nullable=False)

    # Relationships
    contest = relationship("Contest", back_populates="unlisted_users")


# Create an engine and a session
engine = create_engine("mariadb+pymysql://hrideshmg:robot123@127.0.0.1:3306/wscontest")
Base.metadata.create_all(engine)
