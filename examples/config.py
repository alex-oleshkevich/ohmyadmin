import pathlib
import sqlalchemy as sa
from async_storages import FileStorage, LocalStorage
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

metadata = sa.MetaData()
Base = declarative_base()
this_dir = pathlib.Path(__file__).parent
uploads_dir = this_dir / 'uploads'
engine = create_async_engine('postgresql+asyncpg://postgres:postgres@localhost/ohmyadmin', future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
file_storage = FileStorage(LocalStorage(this_dir / 'uploads'))
