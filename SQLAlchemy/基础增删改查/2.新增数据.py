import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine,AsyncSession
from sqlalchemy import Integer, String,insert
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column


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
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String(10),nullable=False)
    number:Mapped[str] = mapped_column(String(50),nullable=False)


async def add_user():
    async with async_session() as session:
        # 单条插入
        new_user = User(
            id = 1,
            name = 'Marry',
            number = '12478980980'
        )
        session.add(new_user)
        await session.commit()
        print('添加成功')

        # 批量插入
        user_list = [
            User(id=4,name='tom',number='03874689'),
            User(id=5,name='mike',number='03874289'),
            User(id=6,name='lily',number='038744689'),
        ]
        session.add_all(user_list)
        await session.commit()
        print('添加成功')

        # 超高性能批量插入(Core语法)
        # 字典列表,无需创建实例
        data = [
            {'id':4,'name':'Tom','number':'09784311'},
            {'id':5,'name':'Nick','number':'42255311'},
            {'id':6,'name':'Query','number':'23584311'},
            {'id':7,'name':'kimi','number':'87674311'}
        ]
        await session.execute(insert(User).values(data))
        await session.commit()
        print('插入成功')




# 先执行添加，再显式关闭引擎
async def main():
    await add_user()
    # 显式关闭引擎，释放所有连接
    await async_engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())