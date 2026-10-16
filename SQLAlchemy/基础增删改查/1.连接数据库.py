from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import asyncio


# 连接URL
URL = 'mysql+aiomysql://root:123456@localhost:3306/study?charset=utf8mb4'

# 创建异步引擎
async_engine = create_async_engine(URL,echo=True)

# 创建ORM声明式基类
class Base(DeclarativeBase):
    pass

# 创建异步会话工厂

async_session = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,   # 提交后实例不失效
    autoflush=False           # 关闭自动刷新
)

async def connection_db():
    async with async_session() as session:
        print('数据库连接成功')



if __name__ == '__main__':
    asyncio.run(connection_db())