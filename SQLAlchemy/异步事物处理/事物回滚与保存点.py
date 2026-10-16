import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine,AsyncSession
from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import DeclarativeBase, Mapped

# URL
URL = 'mysql+aiomysql://root:123456@localhost:3306/study?charset=utf8mb4'

# 创建异步引擎
async_engine = create_async_engine(URL,echo=True)

# 创建异步工厂
async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# ORM基类
class Base(DeclarativeBase):
    pass

# 定义数据模型
class User(Base):
    __tablename__ = 'user'
    # 定义表字段
    id:Mapped[int] = Column(Integer,primary_key=True)
    name:Mapped[str] = Column(String(10),nullable=False)
    number:Mapped[str] = Column(String(50),nullable=False)


async def add_user():
    async with async_session() as session:
        async with session.begin():
            # 新增用户1
            user_1 = User(id=10,name='Ail',number='0978905')
            session.add(user_1)
            # flush只是把数据刷新到数据库,没有提交事物
            await session.flush()
            # 创建保存点
            save_point = await session.begin_nested()
            try:
                # 新增用户2
                user_2 = User(id=9,name='Oil',number='0978315')
                session.add(user_2)
                await session.flush()
                await save_point.commit()
                print('添加成功')
            except Exception:
                # 回滚到保存点(用户1的操作不受到影响)
                await save_point.rollback()
                print('事物已回滚')


async def main():
    await add_user()
    await async_engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())