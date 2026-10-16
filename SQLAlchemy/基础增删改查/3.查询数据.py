from sqlalchemy import Integer,String,select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column
import asyncio



URL = 'mysql+aiomysql://root:123456@localhost:3306/study?charset=utf8mb4'

async_engine = create_async_engine(URL,echo=True)

async_session = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession
)



class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String(50))
    number:Mapped[str] = mapped_column(String(50))


async def inquire_data():
    async with async_session() as session:
        # 查询所有数据
        stmt = select(User)
        all_data = (await session.scalars(stmt)).all()
        for user in all_data:
            print(f'id:{user.id},name:{user.name},number:{user.number}')

        # 条件查询(大于/小于/不等于/等于/like模糊匹配/in查询/is (not) nul/and(and_)/or)
        stmt = select(User).where(User.id > 1)
        all_data = (await session.execute(stmt)).all()
        for user in all_data:
            print(f'id:{user.id},name:{user.name},number:{user.number}')

        # 主键查询
        user = await session.get(User,1)
        if user:
            print(f'id:{user.id},name:{user.name},number:{user.number}')
        else:
            print('用户不存在')

        # 按指定字段查询
        stmt = select(User.name,User.number)
        all_data = (await session.execute(stmt))
        result = all_data.mappings().all()
        print(result)



async def main():
    await inquire_data()
    await async_engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
