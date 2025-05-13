from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from source.config import DB_CONFIG
import pymysql


Base = declarative_base()

# DATABASE_URL = (f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
#                 f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
#
# engine = create_engine(DATABASE_URL, pool_recycle=1800, pool_pre_ping=True)
# SessionLocal = sessionmaker(bind=engine)
#
# Base=declarative_base()


class DatabaseManager:
    """Handles database connections and provides basic session management"""

    def __init__(self, db_config):
        self.config = db_config
        self.engine = None
        self.session_factory = None
        self._setup_connection()

    def _setup_connection(self):
        """Creates engine and session factory"""
        database_url = (f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
                        f"@{self.config['host']}:{self.config['port']}/{self.config['database']}")
        self.engine = create_engine(database_url, pool_recycle=1800, pool_pre_ping=True)
        self.session_factory = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)

    def get_session(self):
        """Returns a new database session"""
        return self.session_factory()
