import asyncio
from sqlalchemy import Integer, String,delete,select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column

URL = 'mysql+aiomysql://root:123456@localhost:3306/study?charset=utf8mb4'

async_engine = create_async_engine(URL,echo=True)

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String(50))
    number:Mapped[str] = mapped_column(String(50))


async def del_data():
    async with async_session() as session:
        # 先查询后删除
        stmt = select(User).where(User.id == 6)
        data =  await session.execute(stmt)
        user = data.scalar_one_or_none()
        if  user:
            await session.delete(user)
            await session.commit()
            print('删除成功')
        else:
            print('用户不存在')

        # 批量删除
        stmt = delete(User).where(User.id > 3)
        result = await session.execute(stmt)
        await session.commit()
        print(f'{result.rowcount}行被删除')


async def main():
    await del_data()
    await async_engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())