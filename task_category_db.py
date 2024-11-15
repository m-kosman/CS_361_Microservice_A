import enum
import json
from sqlalchemy import create_engine, Integer, String, ForeignKey
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Mapped, mapped_column
from contextlib import contextmanager
from typing import Union

class Categories(enum.Enum):
    work = "work"
    school = "school"
    home = "home"
    health = "health/fitness"
    personal = "personal"
    shopping = "shopping"
    finance = "finance"

    @classmethod
    def get_enum_from_display(cls, display_name: str) -> Union[enum, None]:
        """Receives the display name for a unit and returns the RecipeUnit"""
        for category in cls:
            if category.value == display_name:
                return category
        return None


Base = declarative_base()


class Category(Base):
    """Represents a task category"""
    __tablename__ = 'category'

    id: Mapped[int] = mapped_column('category_id', Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column('category', SQLAEnum(Categories, values_callable=lambda x: [e.value for e in x]))

    keywords: Mapped[list["Keyword"]] = relationship("CategoryKeyword", back_populates="category")

    def __repr__(self):
        return f"Category(id={self.id!r}, name={self.name!r})"


class Keyword(Base):
    """Represents a keyword"""
    __tablename__ = 'keyword'

    id: Mapped[int] = mapped_column("keyword_id", Integer, primary_key=True, autoincrement=True)
    keyword_name: Mapped[str] = mapped_column("keyword", String(255), nullable=False)

    categories: Mapped[list["Category"]] = relationship("CategoryKeyword", back_populates="keyword")

    def __repr__(self):
        return f"<Keyword(id={self.id!r}, keyword_name={self.keyword_name!r})>"


class CategoryKeyword(Base):
    """Represents a link between a keyword and a category"""
    __tablename__ = 'category_keywords'

    id: Mapped[int] = mapped_column("category_keyword_id", Integer, primary_key=True, autoincrement=True)
    category_id: Mapped[int] = mapped_column("category_id", Integer, ForeignKey('category.category_id'), nullable=False)
    keyword_id: Mapped[int] = mapped_column("keyword_id", Integer, ForeignKey('keyword.keyword_id'), nullable=False)

    category: Mapped["Category"] = relationship("Category", back_populates="keywords")
    keyword: Mapped["Keyword"] = relationship("Keyword", back_populates="categories")

    def __repr__(self):
        return f"<CategoryKeyword(id={self.id!r}, category_id={self.category_id!r}, keyword_id={self.keyword_id!r})>"


# set up database engine
engine = create_engine('sqlite+pysqlite:///task_category.db')
Base.metadata.create_all(bind=engine, checkfirst=True)
Session = sessionmaker(bind=engine, expire_on_commit=False)


def add_categories():
    """Pre-adds the enumerated categories to the Unit table"""
    session = Session()
    try:
        for category in Categories:
            if not session.query(Category).filter_by(name=category.value).first():
                session.add(Category(name=category.value))
        session.commit()
    except Exception as e:
        session.rollback()


def add_starter_data(json_file):
    """Pre-adds the starter keywords to the database """
    with open(json_file, "r") as file:
        categories = json.load(file)
    session = Session()
    try:
        # get category id
        for category_name, keywords in categories.items():
            category_id = get_category_id(category_name)
            # loop over list of keywords
            for keyword_name in keywords:
                # check for duplicates
                keyword = session.query(Keyword).filter_by(keyword_name=keyword_name).first()

                if not keyword:
                    # create keyword if it does not exist
                    keyword = Keyword(keyword_name=keyword_name)
                    session.add(keyword)
                    session.flush()

                # add keyword/category link to junction table
                category_keyword = CategoryKeyword(category_id=category_id, keyword_id=keyword.id)
                session.add(category_keyword)

        session.commit()
    except Exception as e:
        session.rollback()
        return


def get_category_id(display_name:str) -> int:
    """Helper method to get a category id from the display name of the enumerated category"""
    session = Session()
    # looks up category from the display name
    try:
        category_instance = session.query(Category).filter_by(name=display_name).first()
        # returns the id
        if category_instance:
            return category_instance.id
        else:
            return None
    except Exception as e:
        session.rollback()
        print(f"Error retrieving category: {e}")
        return None


class TaskCategoryDatabase:

    def __init__(self):
        self.session = Session()

    @contextmanager
    def session_scope(self):
        """Manages the database sessions"""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
        finally:
            self.session.close()

    def get_category_id(self, display_name: str) -> int:
        """returns the category id"""
        return get_category_id(display_name)

    def get_all_keywords_for_category(self, category_id:int) -> Union[list, None]:
        """
        Receives a category id and returns a list of all the keywords linked to the category.
        :param category_id: category database id
        :return: List of all keywords linked to category
        """
        with self.session_scope() as session:
            try:
                # gets all the keyword instances
                keywords = session.query(Keyword.keyword_name).join(CategoryKeyword).filter(
                        CategoryKeyword.category_id == category_id).all()
                # if any keywords are found it adds it to a list and returns it
                if keywords:
                    keyword_list = [keyword[0] for keyword in keywords]
                    return keyword_list
                return None
            except Exception as e:
                session.rollback()
                return

    def add_keyword_category(self, category:str, task:str) -> bool:
        """
        Adds keywords to database with corrected category based on user feedback.
        :param category: category name
        :param task: task to be added
        :return: True if added otherwise False
        """
        with self.session_scope() as session:
            try:
                # gets the category id
                category_id = self.get_category_id(category)

                # checks for duplicate
                keyword = session.query(Keyword).filter_by(keyword_name=task).first()

                if not keyword:
                    # create keyword if it does not exist
                    keyword = Keyword(keyword_name=task)
                    session.add(keyword)
                    session.flush()

                # add keyword/category link to junction table
                category_keyword = CategoryKeyword(category_id=category_id, keyword_id=keyword.id)
                session.add(category_keyword)
                session.commit()
                return True
            except Exception as e:
                session.rollback()
                return False


if __name__ == "__main__":
    # initializes database
    add_categories()
    add_starter_data('starter_tasks.json')
