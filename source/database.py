from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from source.config import DB_CONFIG

DATABASE_URL = (f"mysql+pymysql://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
                f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

engine = create_engine(DATABASE_URL, pool_recycle=1800, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)

Base=declarative_base()

