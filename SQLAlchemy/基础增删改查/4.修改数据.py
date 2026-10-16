from sqlalchemy import Integer,String,update,select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column
import asyncio



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


async def modification_data():
    async with async_session() as session:
        # 先查询后修改(适合复杂逻辑)
        stmt = select(User).where(User.id == 1)
        data = await session.execute(stmt)
        user = data.scalar_one_or_none()
        if user:
            # 直接修改实例属性
            user.number = '011111'
            await session.commit()
            print('修改成功')
        else:
            print('用户不存在')

        # 批量修改
        stmt = update(User).where(User.id > 5).values(number='0999999')
        result = await session.execute(stmt)
        await session.commit()
        print(f'{result.rowcount}行被修改')



async def main():
    await modification_data()
    await async_engine.dispose()


if __name__ == '__main__':
    asyncio.run(main())