from sqlalchemy import Integer,String,Column
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped
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

class Bank(Base):
    __tablename__ = 'bank'
    name:Mapped[str] = Column(String(50),primary_key=True)
    account:Mapped[int] = Column(Integer)
    money:Mapped[int] = Column(Integer)


async def transfers():
    async with async_session() as session:
        # 1.自动提交/回滚
        # 整个with就是一个事物,要么全部成功,要么全部失败
        async with session.begin():
            # 查询付款用户
            pay_user = await session.get(Bank,'李四')
            # 查询收款用户
            collection_user = await session.get(Bank,'张三')
            if not pay_user or not collection_user:
                print('用户不存在')
                return 0
            if pay_user.money < 1000:
                print('余额不足')
                return 0
            else:
                # 扣钱
                pay_user.money -= 1000
                # 加钱
                collection_user.money += 1000
            # 代码执行到这里,自动commit了
                print("转账成功")
                return 1

        # 2.手动提交/回滚
        try:
            # 查询用户
            pay_user = await session.get(Bank,'李四')
            collection_user = await session.get(Bank,'张三')
            if not pay_user or not collection_user:
                print('用户不存在')
                return 0
            if pay_user.money < 1000:
                print('余额不足')
                return 0
            else:
                # 执行操作
                pay_user.money -= 1000
                collection_user.money += 1000
                # 手动提交
                await session.commit()
                print('转账成功')
        except Exception:
            # 回滚事物
            await session.rollback()
            print('转账失败')





async def main():
    await transfers()
    await async_engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())