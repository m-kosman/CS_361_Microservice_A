import enum
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Numeric
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, backref, Mapped, mapped_column
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
DATABASE_URL = 'postgresql+psycopg://mkosman:8TdpE59JVFM@localhost:5432/task_category'
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)
Session = sessionmaker(bind=engine, expire_on_commit=False)


class TaskCategoryDatabase:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskCategoryDatabase, cls).__new__(cls)
            cls._instance.add_categories()
        return cls._instance

    @contextmanager
    def session_scope(self):
        """Manaages the dtabase sessions"""
        session = Session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def add_categories(self):
        """Pre-adds the enumerated categories to the Unit table"""
        with self.session_scope() as session:
            for category in Categories:
                if not session.query(Category).filter_by(name=category.value).first():
                    session.add(Category(name=category.value))

    def add_keywords_to_category(self, category_id, keywords):
        # used to preadd the keywords to the database
        with self.session_scope() as session:
            try:
                # Loop through the list of keywords
                for keyword_name in keywords:
                    # Check if the keyword already exists
                    keyword = session.query(Keyword).filter_by(keyword_name=keyword_name).first()

                    if not keyword:
                        # If the keyword does not exist, create it
                        keyword = Keyword(keyword_name=keyword_name)
                        session.add(keyword)
                        session.commit()  # Commit the transaction to get the new keyword's ID

                    # Now add the keyword to the junction table to associate it with the category
                    category_keyword = CategoryKeyword(category_id=category_id, keyword_id=keyword.id)
                    session.add(category_keyword)


                # Commit all changes in the session (adding keywords and updating the junction table)
                session.commit()
            except Exception as e:
                session.rollback()


if __name__ == "__main__":
    database = TaskCategoryDatabase()

    # home_tasks = ['clean', 'repair', 'fix', 'living room', 'dining room', 'kitchen', 'plumber', 'wrap presents',
    #               'put up christmas tree', 'declutter', 'dust', 'vacuum',  'rearrange closet', 'organize',
    #               'garden', 'bedroom', 'basement', 'garage', 'mow lawn', 'bathroom', 'bathtub', 'shower', 'toilet',
    #               'fix tv remote', 'put on license sticker', 'check garage door',
    #               'dining room windows', 'put bags out',  'bring in headphones', 'emissions inspection',
    #               'schedule ac service', 'hang new curtains', 'mail transfer', 'clean shower tub',
    #               'set clocks back',  'replace lightbulb in kitchen', 'vacuum out fireplace',
    #               'book car in for maintenace', 'get rid of old paint',  'fix kitchen table',
    #               'clean boxes', 'take dogs to vet', 'organize bedroom', 'oil change', 'wrap mother s day gifts',
    #               'finish all laundry', 'hang ruler', 'book electrician', 'clean garbage disposal',
    #               'send back glasses', 'white wash fireplace', 'finish floor',
    #               'put up shelves in bedroom', 'buy sander', 'find key card', 'put up clock',
    #               'set out clothes for the week',  'wax truck', 'schedule pool opening', 'address update',
    #               'paint molding', 'finish kitchen floor', 'clean out google drive',
    #               'buy wheelbarrow', 'tidy linen cupboard', 'straighten kitchen', 'wash underwear', 'sort clothes out',
    #               'install carbon monoxide detector', 'paint landing', 'health insurance forms', 'get rid of clutter',
    #               'order uhaul', 'well pump', 'office doors', 'sweep pool',
    #               'activate windows', 'anniversary planning', 'replace bathroom fan', 'put up coat rack', 'make gazpacho',
    #               'put up christmas lights', 'recaulk shower', 'make borscht', 'paint doors black',
    #               'put together tv stand', 'load bikes', 'redecorate kitchen', 'organize art room', 'garage organize',
    #               'try on bathing suit',  'throw out old clothes', 'fix extension cord', 'update router',
    #               'basement ceiling', 'tsa appointment', 'buy water heater', 'replace bulb in kitchen', 'book chapter',
    #               'hang fan', 'email ed', 'get dongle', 'organize basement closets', 'straighten up bathroom',
    #               'replace bathroom light bulbs',
    #               'change electric', 'put together bookshelf', 'fix wardrobe door',
    #               'load trailer', 'basement purge', 'change sheets and pillow cases', 'move stuff to attic', 'hang blackout curtains',
    #               'clean cameras', 'boiler cover', 'install deadbolt', 'clean inside of van',
    #               'capsule wardrobe', 'top up screen wash', 'mattress disposal', 'rec room', 'under stairs',
    #               'alarm company', 'sell bbq', 'renovate kitchen', 'get boat ready',
    #               'clean living room carpet', 'home internet', 'final project', 'put boxes away',
    #               'check fb', 'take down xmas', 'redo upstairs bathroom', 'clean out fish tank', 'fertilize lawns',
    #               'get xmas tree', 'vaccum rugs', 'tire swap', 'parents visa', 'clean dinning room table',
    #               'put together chairs', 'more lawn', 'decorate kitchen', 'bring stuff to basement',
    #               'plug in ipad', 'bring hoses in', 'clean tile', 'build lamp', 'shelves in kitchen',
    #               'clean office chair', 'call structural engineer', 'install office',
    #               'clean sink and toilet', 'hallway bathroom', 'clean diningroom', 'organize cupboards',
    #               'car cleanup', 'program remotes', 'start irrigation', 'fix room key', 'finish our laundry', 'clean bathroom fan']
    #
    # school_tasks = ["assignment", "homework", "hw" "project", "essay", "presentation", "study", "research", "review",
    #                 "exam", "test", "quiz", "coursework", "thesis", "lab report", "discussion", "revise", "paper", "notes",
    #                 "reading", "writing",  "math", "science", "history", "literature", "art", "physics", "chemistry", "biology",
    #                 'bio", '"geography", "philosophy", "econ", "economics", "psych", "psychology", "sociology", "engr",
    #                 "engineering", "computer science", "cs", "music", "language arts", "spanish", "chines", "japanese",
    #                 "french", "german" "english", "literature" "poli sci", "political science", "anthropology", "deadline",
    #                 "submission", "grade", "peer review", "evaluation", "project milestone", "class participation", "group work",
    #                 "individual work", "online course", "study group", "lectures", "seminar", "workshops", "course registration",
    #                 "textbook", "enrollment", "course materials", "tutoring", "lecture notes", "classroom", "prepare for exam",
    #                 "study", "assignment help", "finals", "midterm", "internship", "graduation", "academic calendar",
    #                 "student organization", "event", "campus activity", "field trip", "mentorship", "scholarship",
    #                 "study session", "library", "citation", "essay editing", "research paper", "start", "finish", "review",
    #                 "write", "complete", "edit", "submit", "read", "revise", "update", "finalize", "outline", "proofread",
    #                 "take notes", 'sociology paper', 'finish udemy course', 'process journal', 'hw #0', 'stats worksheets',
    #                 'adjust schedule','work on newsletter', 'ais final', 'speech questions', 'dietary analysis', 'sign up for cpr class',
    #                 'spanish online activities', 'label school supplies', 'mgt final', 'group project research',
    #                 'tutorial questions', 'physics exam corrections', 'chem 8', 'review for math test', 'phys exam 4',
    #                 'history dbq essay', 'print spelling lists', 'reflection paper 4', 'chem pre lab questions',
    #                 'read text book', 'finish journal entry', 'spanish supersite', 'chinese final', 'chem outline',
    #                 'uw application', 'pay for graduation', 'quiz #4', 'catch up on bio notes',
    #                 'maths h w', 'chapter 2 vocab', 'homework 3', 'read chapter 66', 'calc book work', 'tech talk',
    #                 'statement of purpose', 'us project', 'psychology ia', 'chem project', 'practice spanish oral',
    #                 'chem hw 7', 'essay #3', 'print chem lab', 'public health', 'mentor report', 'istation', 'history newspaper',
    #                 'alg homework', 'biology test review', 'review 8', 'literature circles', 'catch up on reading', 'dynamics',
    #                 'game theory homework', 'maths test revision', 'submit reflection', 'appendix b', 'drawing homework',
    #                 'shot list', 'add drop classes', 'finish journal', 'history ppt', 'discussion board', 'ioc recording',
    #                 'guided reading plan', 'review chinese', 'patho exam', 'comm homework',
    #                 'print matlab', 'spanish hwk', 'pathology lecture', 'practice powerpoint', 'intent to register',
    #                 'calculus practice problems', 'psych syllabus', 'programming assignment 6', 'theology assignment',
    #                 'acct study', 'wed practice', 'study spanish vocab', 'do assignment 2', 'team presentation',
    #                 'marketing final paper', 'ss homework', 'theater quiz', 'add assignments to planner',
    #                 'type up history notes','psych powerpoint', 'physics hw #0', 'french article', 'anatomy test',
    #                 'ob case study', 'check school schedule', 'chem quiz corrections', 'summer registration', 'ap review',
    #                 'math handout', 'science summary', 'hist essay', 'precal quiz', 'review class notes', 'biology prelab',
    #                 'vibrations homework', 'mktg presentation', 'writing copies', 'social notes', 'pick up books from bookstore',
    #                 'do interview', 'fundamentals', 'acting journals', 'take home math test', 'csf application',
    #                 'print psychology', 'filipino notes', 'solids hw', 'psychology ia draft', 'test in chemistry',
    #                 'managerial hw', 'finish bio hw', 'capstone final', 'review 6', 'read engl', 'assignment #2', 'log patients',
    #                 'finish coding', 'make google form', 'rental books', 'movie analysis', 'ap meeting', 'yearbook to do',
    #                 'read act 5 scene 5', 'read stories', 'osap application', 'bibliography', 'complete econ']
    #
    # work_tasks = ["meeting", "client meeting", "client presentation", "presentation", "report", "deadline", "email",
    #               "conference call", "team", "project", "client", "presentation slides", "status update", "feedback",
    #               "task list", "workshop", "training", "deadline", "contract", "negotiation", "human resources",
    #               "proposal", "strategy", "budget", "office", "management", "supervisor", "productivity", "hr",
    #               "discussion", "discuss", "attend meeting", "attend conference" "conference", "collaborate", "memo", "workflow", "promotion",
    #               "performance review", "salary", "project plan", "work assignment", "teamwork", "manager"
    #               "employee", "leadership", "communication", "decision-making", "workload", "follow up", "timesheet"
    #               "remote work", "overtime", 'meeting tasks', 'creative review', 'monthly comms', 'office layout', 'report time',
    #               'real estate meeting', 'send updated schedule', 'shareholder update','schedule feedback sessions',
    #                'check on timesheet', 'finish updating cv', 'schedule evals', "request for proposal", 'pay corp amex',
    #               'figure out voicemail', 'passport to hr', 'workflow meeting', 'direct deposit information',
    #               'finish and order business cards', 'interview sheet', 'cc cancel', 'refresh cv', 'it policies', 'cctv training',
    #               'fix paperwork', 'reaccreditation', 'teaching certificate', 'salesforce application', 'email strategy', 'contract sign',
    #               'complete application', 'backup quickbooks', 'product review deck', 'check time sheets', 'linked in update',
    #               'analytics presentation', 'make expense report', 'test database', 'year at a glance',
    #               'print time sheets', 'complete new hire packet', 'employee eval', 'production support', 'check jira tickets',
    #               'metlife proposal', 'post intern job', 'eow report', 'work contracts', 'review deliverables', 'update one drive',
    #               'new job posting', 'enroll in health care', 'send slides to team', 'business process mapping', 'respond to enquiries',
    #               'email new interns', 'timesheets email', 'android app testing', 'product testing', 'email journalists', 'retreat location',
    #               'set up lunch and learn', 'commuter benefit', 'follow up with payroll', 'associate training', 'email re meeting',
    #               'w 6 form', 'interview emails', 'out of office reminder', 'business cards pick up',  "onboarding",
    #               'setup out of office', 'rfp questions', 'complete meeting agenda', 'client profile', 'new timesheets',
    #               'get interns', 'write intern description',  'mandatory training modules', 'salary', 'hr write up',
    #               'call vendors', 'work on job applications','content marketing strategy', 'enter sick day',
    #               'monthly expense report', 'board meeting items', 'tuesday briefing', 'annual security training', 'enter invoices in qb']
    #
    # health_tasks = ["workout", "exercise", "gym", "strength training", "cardio", "fitness", "weight loss",
    #                 "diet", "nutrition", "healthy eating", "meal plan", "protein", "vitamins", "stretching",
    #                 "yoga", "running", "cycling", "swimming", "strength", "endurance", "reps", "sets",
    #                 "personal trainer", "pt", "fitness goal", "muscle gain", "calories", "calorie tracking",
    #                 "body weight", "gym routine", "healthy lifestyle", "wellness", "mental health",
    #                 "hydrate", "sleep", "workout routine", "rest day", "stretch", "mobility", "post-workout",
    #                 "fitness tracker", "exercise plan", "strength exercises", "flexibility", "weightlifting", "doctor",
    #                 "dentist", "doctor appointment", "dentist appointment", "doctor appt", "dr appt", "dentist appt",
    #                 "psychiatrist", "cardiologist", "gp", "pcp", "nurse", "medicine", "prescription", "refill medicine",
    #                 "refill prescription", "rx", "refill rx", 'dr refill', 'finish gym', 'stool test', 'daily workout',
    #                 'follow up doctors appointment', 'call dr i', 'call and reschedule dentist appointment',
    #                 'research workouts', 'baby doctor', 'go to the gym', 'pregnancy yoga', 'gym 8', 'sign up for a gym',
    #                 'exercises', 'back pain doctor', 'schedule dentist checkup', 'dentist filling', 'body check up',
    #                 'call doctor s office', 'review workout schedule', 'change address dentist', 'join a running club',
    #                 'check dentist appt', 'm dentist', 'dentist consultation', 'dr test results', 'next dentist',
    #                 'email the doctor', 'find local gym', 'gym cardio', 'review dentist', 'gym induction', 'run 6',
    #                 'papsmear', 'take gym clothes to work', 'call doctor about refill', 'find yoga class',
    #                 'make eye doctor appt', 'dentist 5 31', 'am yoga', 'look into dentists', 'call eye doctor for contacts',
    #                 'gym towel', 'dentist at 4', 'book dr s app', 'gym and sauna', 'move dr appt', 'email dentist',
    #                 'make a doctors appointment', 'liver test', 'phone doctor for appointment', 'gymnastics sign up',
    #                 'gym twice', 'make foot dr appointment', '10am dentist', 'verify dentist', 'run push ups', 'dentist eob',
    #                 'strength exercises', 'reschedule dentist for me', 'reschedule doctors appts', 'adjustable dumbells',
    #                 'call girls dentist', '61 squats', 'download yoga app', 'the gym', 'dad doctor', 'go to a yoga class',
    #                 'dr paper work', 'email dr chen', 'exercise machines', 'arrange dentist', 'reschedule dentist apt',
    #                 'set dentist appointment', 'make ent appt', 'girls dentist appointment', 'gym clothes for work',
    #                 'book physio appointment', 'book to see doctor', 'gym and trainer', 'sign up for gymnastics',
    #                 'call dentist mom', 'day 6 workout', 'chest press', 'get doctor s note', 'setup eye doctor appointment',
    #                 'call my gym', 'email about treadmill', 'make kids dentist appointment'
    #                 ]
    #
    #
    # finance_tasks = ["budget", "tax", "investment", "savings", "expenses", "income", "revenue", "loan",
    #                  "credit", "debt", "account", "billing", "finance report", "financial plan", "mortgage",
    #                  "stocks", "bonds", "retirement", "insurance", "payroll", "audit", "asset", "liabilities",
    #                  "capital", "accounting", "balance sheet", "tax return", "financial statements",
    #                  "net worth", "portfolio", "liquidity", "cash flow", "credit score", "financial advisor",
    #                  "interest rate", "invoice", "payment", "expenses tracking", "tax planning", "asset management",
    #                  "financial forecasting", "debt repayment", "budget planning", "financial goals", "credit report",
    #                  "mortgage payment", "loan approval", "investment portfolio", "bank account", "business expenses",
    #                  "financial analysis", "capital gains", "dividends", "retirement fund", "spending report",
    #                  "asset allocation", "liquid assets", "bankruptcy", "taxable income", "income tax",
    #                  "financial independence", "estate planning", "savings account", "financial literacy", "savings goal",
    #                  "financial strategy", "debt management", "debt consolidation", "interest-bearing accounts", "credit limit",
    #                  "monthly statement", "financial budgeting", "monthly budget", "personal finance", "financial freedom",
    #                  "cash management", "credit card debt", "spending limit", "emergency fund", "tax preparation",
    #                  "charitable donations", "retirement savings", "income tracking", "financial planning software",
    #                  "bank statement", "investment return", "mutual funds", "asset valuation", "mortgage rate",
    #                  "credit score improvement", "capital investment",
    #                  "financial reporting", "audit report", "financial disclosure", "investment strategy",
    #                  "income report", "net income", "long-term savings", "short-term savings", "financial advisor meeting",
    #                  "loan payment", "fixed income", "variable income", "personal finance management", "financial freedom plan",
    #                  'get reimbursed for gym', 'get dentist money', 'notify credit card', 'flooring estimate', 'get a safe',
    #                  'check ebay bill', 'ucla bills', 'pay uc health bill', 'look up comcast bill', 'figure out cell phone bill',
    #                  'set up tax appt', 'set up gas bill', 'pay heating bill', 'pay xfinity bill', 'pay telus bill',
    #                  'cancel showtime', 'submit phone bills', 'physio bills', 'pay eversource bill', 'review pay bills',
    #                  'pay seattle light bill', 'submit conference receipts', 'budget for bills', 'pay off credit card bills',
    #                  'parking bill', 'check garbage bill', 'pay kaiser bill', 'pay company bills', 'copy water bill',
    #                  'mon pay bills', 'pay boa bill', 'pay rates bills', 'doctors health fund', 'citi card bill',
    #                  'pay ohio health bill', 'pay dr a', 'check citibank statement', 'pay mediacom bill', 'pay american express today',
    #                  'dr cash', 'set up credit card']
    #
    # personal_tasks = ["personal development", "self-care", "goals", "routine", "hobby", "travel", "vacation",
    #                   "family", "friends", "relationship", "time management", "self-improvement", "mindfulness",
    #                   "reflection", "creativity", "reading", "journal", "balance", "plan", "meditate",
    #                   "well-being", "hobby", "weekend", "cook", "vacation", "relax", "morning routing",
    #                   "nightime routine", "plan vacation", "birthday", "anniversary", "self-reflection", "motivation",
    #                   "personal goal", "recharge", "me-time", "volunteer", "charity", "donate",
    #                   "community service", "creative writing", "crafting", "time for self", "reflection", "meditate",
    #                   "road trip", "call mom", "call dad",'bring book in', 'text', 'mom application', 'electronics recycle',
    #                   'sign insurance docs', 'text martin', 'soak in bath', 'call about apt', 'cheer competition',
    #                   'run laptop backup', 'brunch monday', 'email shelli', 'call mom thank you',
    #                   'drop car off for service', 'bridesmaid email', 'book coaching session', 'update software',
    #                   'call grandad', 'create my vision board', 'make lunches', 'have lunch', 'sunday outfit',
    #                   "catch up", "watch tv", "skincare", "church"
    #                   ]
    #
    # shopping_tasks = ["shopping", "buy", "purchase", "order", "cart", "checkout", "sale", "discount", "coupon",
    #                  "deal", "bargain", "clearance", "online shopping", "store", "shop", "buying", "retail",
    #                  "items", "products", "groceries", "clothing", "electronics", "fashion", "accessories",
    #                  "home goods", "furniture", "beauty products", "personal care", "gift", "gift card", "wishlist",
    #                  "buy now", "add to cart", "shopping list", "shopping spree", "supermarket", "mall", "store visit",
    #                  "sale items", "shopping cart", "price check", "price comparison", "shopping mall", "purchase items",
    #                  "discounted", "buying spree", "order online", "shipping", "delivery", "order status", "track order",
    #                  "return", "refund", "exchange", "shopping day", "buying list", "gift shopping", "birthday shopping",
    #                  "holiday shopping", "seasonal sale", "shopping for", "purchase online", "online store", "brick and mortar",
    #                  "special offer", "early access", "pre-order", "limited edition", "shopping trip", "black friday",
    #                  "cyber monday", "seasonal discount", "new arrivals", "exclusive deal", "gift registry", "shopping budget",
    #                  "price drop", "weekly sale", "super sale", "flash sale", "price alert", "shopping guide",
    #                  "sale event", "shopping habits", "back to school shopping", "end of season sale", "holiday deals",
    #                  "bulk shopping", "home shopping", "personal shopping", "shopping haul", "store opening",
    #                  "local shopping", "luxury shopping", "shop till you drop", "furniture shopping", "grocery store",
    #                  "clothing store", "electronic store", "shopping mall visit", "special offers", "membership discount",
    #                  "flash discount", "cashback offer", "shopping spree day", "superstore", "bulk buying", "gift ideas",
    #                  "food shopping", "clothes shopping", "groceries shopping", "buying clothes", "shop for groceries",
    #                  "online orders", "shopping voucher", "free shipping", "free delivery", "gift purchase", "amazon",
    #                  "walmart", "costco", "mall", "target", "trader joe's", "kroger", "cvs", "walgreens", "whole foods",
    #                  'return paint to home depot', 'buy gym shorts', 'buy running gear', 'order exercise equipment',
    #                  'dsw rewards', 'return amazon parcel',  'return amazon curtains', 'make a christmas shopping list',
    #                  'redeem costco certificate', 'shirt receipt', 'athleta coupon']
    #
    # database.add_keywords_to_category(5, personal_tasks)






