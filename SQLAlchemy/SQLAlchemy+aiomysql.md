# SQLAlchemy 2.0 + aiomysql

# 一、准备工作

## 1.1安装SQLAlchemy+aiomysql

```
pip install sqlalchemy>=2.0 aiomysql
```

## 1.2核心概念：

- **aiomysql**：Python 和 MySQL 之间的「异步传话员」，负责把 Python 的异步指令转成 MySQL 能懂的语言，不用等数据库返回就能处理其他任务。
- **AsyncEngine（异步引擎）**：数据库连接的核心工厂，全局只需要创建 1 个，负责管理数据库连接池，所有数据库操作都基于它。
- **AsyncSession（异步会话）**：我们和数据库交互的唯一入口，相当于一次和数据库的「对话」，所有增删改查都通过它执行，用完必须关闭。
- **Declarative Base（声明式基类）**：所有 ORM 模型的父类，你写的 Python 表模型都要继承它，它负责把 Python 类和 MySQL 的表自动映射。
- **Model（模型）**：一个 Python 类对应 MySQL 里的一张表，类的属性对应表的字段，类的一个实例对应表的一行数据。
- **事务**：一组数据库操作的「打包单元」，要么全部成功，要么全部失败回滚，保证数据一致性。

三、模型定义详解：字段、约束、索引

模型是 ORM 的核心，这一节讲透所有模型定义的细节，覆盖 99% 的业务场景。

### 1.2 常用字段类型与 MySQL 对应关系

| SQLAlchemy 类型             | 对应 MySQL 类型     | 适用场景                               |
| ------------------------- | --------------- | ---------------------------------- |
| Integer                   | INT             | 整数，主键、年龄、数量等                       |
| BigInteger                | BIGINT          | 大整数，比如雪花 ID、超大数值                   |
| String(length)            | VARCHAR(length) | 短字符串，用户名、邮箱、标题等，必须指定长度             |
| Text                      | TEXT            | 长文本，文章内容、详情描述等，无长度限制               |
| Boolean                   | TINYINT(1)      | 布尔值，状态、是否删除等                       |
| Float / Double            | FLOAT / DOUBLE  | 浮点数，价格、重量等                         |
| DECIMAL(precision, scale) | DECIMAL         | 高精度小数，金额、财务数据（避免浮点数精度丢失）           |
| DateTime                  | DATETIME        | 日期时间，创建时间、更新时间                     |
| Date                      | DATE            | 日期，生日、订单日期                         |
| Time                      | TIME            | 时间，打卡时间                            |
| JSON                      | JSON            | JSON 格式数据，扩展字段、配置信息（MySQL5.7 + 支持） |

## 1.3 核心约束与属性配置

每个字段都可以通过参数配置约束，保证数据合法性：

```python
from sqlalchemy import Integer, String, Column,DateTime,func
from sqlalchemy.orm import DeclarativeBase, Mapped
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'
    # 主键:primary_key = True，必须有一个主键,唯一约束：unique=True，值不能重复
    id:Mapped[int] = Column(Integer,primary_key=True,unique=True,comment='用户ID')
    # 非空约束:nullable=False，不允许为空
    name:Mapped[str] = Column(String(50),nullable=False,comment='姓名')
    # 默认值：default，插入时不赋值则用默认值
    number:Mapped[str] = Column(String(50),nullable=False,default='None',comment='号码')
    # 时间默认值：用func.now()获取数据库当前时间，不用Python的datetime.now()
    created_at:Mapped[datetime] = Column(DateTime, default=func.now(), comment='创建时间')
    # 自动更新时间：onupdate，数据更新时自动刷新时间
    updated_at:Mapped[datetime] = Column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
```

**重点提醒**：

- 时间字段默认值**必须用`func.now()`**，不要用 Python 的`datetime.datetime.now()`，后者只会在模型加载时执行一次，时间不会更新。
- 每个字段都加上`comment`注释，方便团队协作和数据库维护。

## 1.4 索引配置（单字段 / 联合索引）

索引是提升查询性能的核心，SQLAlchemy 中两种索引配置方式：

```python
from sqlalchemy import Column,Index,String,Integer
from sqlalchemy.orm import DeclarativeBase, Mapped

URL = 'mysql+aiomysql://root:123456@localhost:3306/study?charset=utf8mb4'

class Base(DeclarativeBase):
    pass

# 索引定义
class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = Column(Integer,primary_key=True)
    name:Mapped[str] = Column(String(50))
    number:Mapped[str] = Column(String(50))

    # 联合索引
    __table_args__ = (
        # 单字段索引
        Index('ix_user_name','name'),
        Index('ix_user_number','number'),
        # 普通联合索引
        Index('ix_name_number','name','number'),
    )
```

### 1.5 模型继承与复用

多个模型有相同字段时，可以用抽象基类复用，避免重复代码：、

```python
from sqlalchemy import String,Integer,Column
from sqlalchemy.orm import DeclarativeBase,Mapped


class Base(DeclarativeBase):
    # 抽象基类,不会生成表
    __abstract__ = True
    # 所有表通用字段
    id:Mapped[int] = Column(Integer,primary_key=True,comment='用户ID')
    name:Mapped[str] = Column(String(50),comment='姓名')
    number:Mapped[str] = Column(String(50),comment='号码')


# 继承通用基类，自动拥有id等字段
class User(Base):
    __tablename__ = 'user'
    # 可以添加这个表独有字段
    email:Mapped[str] = Column(String(100), unique=True, nullable=False)

class Book(Base):
    __tablename__ = 'book'
    user_id:Mapped[int] = Column(Integer)

print("User模型字段：", [k for k in User.__mapper__.columns.keys()])
print("Book模型字段：", [k for k in Book.__mapper__.columns.keys()])
```

# 二、增删改查功能的编写

## 2.1连接数据库

```python
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
```

## 2.2增加数据

```python
import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine,AsyncSession
from sqlalchemy import Integer, String, Column,insert
from sqlalchemy.orm import DeclarativeBase,Mapped

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
```

## 2.3查询数据

```python
from sqlalchemy import Column,Integer,String,select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped
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
    id:Mapped[int] = Column(Integer,primary_key=True)
    name:Mapped[str] = Column(String(50))
    number:Mapped[str] = Column(String(50))


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
```

## 2.3更新数据

```python
from sqlalchemy import Integer,String,update,select
from sqlalchemy import Column
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


class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = Column(Integer,primary_key=True)
    name:Mapped[str] = Column(String(50))
    number:Mapped[str] = Column(String(50))


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
```

## 2.4删除数据

```python
import asyncio
from sqlalchemy import Column, Integer, String,delete,select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped

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
    id:Mapped[int] = Column(Integer,primary_key=True)
    name:Mapped[str] = Column(String(50))
    number:Mapped[str] = Column(String(50))


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
```

# 三、异步事物处理

## 3.1 事务的核心特性

事务必须满足 ACID 四大特性，简单理解就是：**一组操作，要么全部成功，要么全部失败，不会出现一半成功一半失败的情况**。

比如转账：A 扣钱和 B 加钱必须在同一个事务里，不能 A 扣了钱，B 没加上。

执行SQL语句

```sql
create table study.bank
(
    name    varchar(50) null,
    account int         null,
    money   int         null
);
```

### 写法一:自动提交/回滚

```python
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
                return 


async def main():
    await transfers()
    await async_engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
```

### 写法二:手动提交事物/回滚

```python
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

        # .手动提交/回滚
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
```

### 事物回滚与保存点

```python
import asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine,AsyncSession
from sqlalchemy import Integer, String, Column
from sqlalchemy.orm import DeclarativeBase

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
    id = Column(Integer,primary_key=True)
    name = Column(String(10),nullable=False)
    number = Column(String(50),nullable=False)


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
```

## 3.2事务常见坑

1. **忘了 commit**：数据没写入数据库，最高频错误，必须 commit 才会生效
2. **长事务占用连接**：不要在事务里执行耗时的非数据库操作（比如调用第三方接口、循环 sleep），会占用数据库连接，导致连接池耗尽
3. **混用不同会话的事务**：一个事务只能在同一个 session 里执行，不能跨 session
4. **flush 和 commit 的区别**：flush 只是把数据刷到数据库，事务还没提交，rollback 还能回滚；commit 是提交事务，永久生效，无法回滚

# 四、ORM 关联关系：一对多 / 多对多 / 一对一

## 前置概念

- **外键**：关系数据库通过在多的一方或关联表设置列，引用另一表主键。

- **拥有方**：持有 `ForeignKey` 的模型。

- **反向方**：被引用的模型，通过 `relationship` 映射为集合或标量属性。

SQLAlchemy 中使用 `ForeignKey` 定义列级约束，再用 `relationship` 建立对象间的导航能力。

以下示例均基于 `declarative_base`：

python

```python
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship, backref, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
Base = declarative_base()
engine = create_engine('sqlite:///demo.db')  # 示例
session = Session(engine)
```

---

## 4.1 一对一（One-to-One）

数据库视角:

一张表的外键列设置 `UNIQUE` 约束。

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50)
);
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER UNIQUE,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

### 4.2 SQLAlchemy 映射

关键：`relationship` 中指定 `uselist=False`，让反向引用返回单个对象。

```python
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50))
    # 一对一：uselist=False 确保 profile 是单个对象
    profile = relationship("Profile", uselist=False, back_populates="user")
```

```python
class Profile(Base):
    __tablename__ = 'profiles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    bio = Column(Text)
    user = relationship("User", back_populates="profile")
```

### 4.3 使用

```python
user = User(username='alice')
profile = Profile(bio='Hello', user=user)  # 设置拥有方
session.add_all([user, profile])
session.commit()
```

## 正向访问

```py
print(user.profile.bio)     # 'Hello'
```

## 反向访问

```python
print(profile.user.username)  # 'alice'
```

---

## 4.4 一对多（One-to-Many）

### 数据库视角

“多”方持有外键，无唯一约束。

```sql
CREATE TABLE departments (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100)
);
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100),
    department_id INTEGER,
    FOREIGN KEY (department_id) REFERENCES departments(id)
);
```

### 4.5 SQLAlchemy 映射

“一”方定义包含集合的 `relationship`，“多”方定义标量引用。

```python
class Department(Base):
    __tablename__ = 'departments'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    employees = relationship("Employee", back_populates="department")
```

```python
class Employee(Base):
    __tablename__ = 'employees'    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    department_id = Column(Integer, ForeignKey('departments.id'))
    department = relationship("Department", back_populates="employees")
```

### 4.6 使用

```python
dept = Department(name='Engineering')
emp1 = Employee(name='Bob', department=dept)
emp2 = Employee(name='Carol', department=dept)
session.add_all([dept, emp1, emp2])
session.commit()
```

## 从一方访问多方集合

```python
print([e.name for e in dept.employees])  # ['Bob', 'Carol']
```

## 从多方访问一方

```python
print(emp1.department.name)             # 'Engineering'
```

## 也可以通过追加方式添加

```python
dept.employees.append(Employee(name='Dave'))
session.commit()
```

**注意**：始终确保设置了外键拥有方（即 `employee.department`），`back_populates` 会自动同步集合，但若只操作集合而忽略标量方，可能会导致状态不一致。

---

## 4.7多对多（Many-to-Many）

必须通过**中间表**实现。

### 简单多对多（仅存储关系）

#### 数据库

中间表至少包含两个外键列。

```sql
CREATE TABLE students (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100)
);
CREATE TABLE courses (
    id INTEGER PRIMARY KEY,
    title VARCHAR(100)
);
CREATE TABLE enrollments (
    student_id INTEGER,
    course_id INTEGER,
    PRIMARY KEY (student_id, course_id),
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
```

#### SQLAlchemy 映射

使用 `Table` 对象传给 `secondary` 参数。

```python
enrollments = Table('enrollments', Base.metadata,
    Column('student_id', Integer, ForeignKey('students.id'), primary_key=True),
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True)
)
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    courses = relationship("Course", secondary=enrollments, back_populates="students")
```

```python
class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    students = relationship("Student", secondary=enrollments, back_populates="courses")
```

## 操作

```python
student = Student(name='张三')
course = Course(title='Python')
student.courses.append(course)
```

## 或 course.students.append(student)

```python
session.add_all([student, course])
session.commit()
```

## 查询

```python
print(student.courses)       # [<Course 'Python'>]
print(course.students)       # [<Student '张三'>]
```

## 移除关联

```python
student.courses.remove(course)
session.commit()
```

### 4.8 带附加属性的多对多

当中间表需要额外字段（如选课时间、成绩）时，必须将**中间表升级为实体模型**，并将关系拆分为两个一对多。

#### SQLAlchemy 映射

```python
class Enrollment(Base):
    __tablename__ = 'enrollments'
    student_id = Column(Integer, ForeignKey('students.id'), primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), primary_key=True)
    enrolled_at = Column(DateTime, default=func.now())
    grade = Column(String(2))
    student = relationship("Student", back_populates="enrollments")
    course = relationship("Course", back_populates="enrollments")
```

```python
class Student(Base):
    __tablename__ = 'students'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    enrollments = relationship("Enrollment", back_populates="student")
    enrollments = relationship("Enrollment", back_populates="course")
```

#### 操作

必须通过 `Enrollment` 对象操作：

```python
student = Student(name='李四')
course = Course(title='Math')
enr = Enrollment(student=student, course=course, grade='A')
session.add_all([student, course, enr])
session.commit()
```

## 查询某个学生的选课及成绩

```python
for e in student.enrollments:
    print(e.course.title, e.grade)  # Math A
```

## 总结（纯 SQLAlchemy）

| 关系类型    | 数据库实现          | SQLAlchemy 核心参数                    |
| ------- | -------------- | ---------------------------------- |
| 一对一     | 外键 + UNIQUE 约束 | `relationship(..., uselist=False)` |
| 一对多     | 多的一方持有外键       | `ForeignKey` + `relationship`      |
| 多对多     | 中间表（两外键）       | `Table` 对象传给 `secondary`           |
| 带属性的多对多 | 中间表提升为模型       | 拆成两个一对多关系，显式定义中间模型                 |

# 五、性能优化最佳实践

## 5.1 连接池配置优化

连接池是提升性能的核心，创建引擎时优化配置：

```python
async_engine = create_async_engine(
    ASYNC_DB_URL,
    echo=False,  # 生产环境关闭SQL打印
    # 连接池核心配置
    pool_size=10,  # 连接池常驻连接数，根据业务调整，默认5
    max_overflow=20,  # 超出pool_size的最大临时连接数，默认10
    pool_recycle=3600,  # 1小时自动回收连接，避免MySQL 8小时断开连接
    pool_pre_ping=True,  # 每次获取连接前ping，确保连接有效，避免断连报错
    pool_timeout=30,  # 获取连接的超时时间，默认30秒
)
```

**配置建议**：

- 小型项目：pool_size=5，max_overflow=10
- 中型项目：pool_size=10-20，max_overflow=20-50
- 不要设置过大的连接数，MySQL 默认最大连接数是 151，过大反而会降低性能

## 5.2 查询性能优化

1. 只查需要的字段，避免 select ：只查询业务需要的字段，减少数据传输

2. **合理使用索引**：where、order by、group by 的字段必须加索引

3. **避免全表扫描**：不要在索引字段上用函数、计算，否则索引会失效

4. **分页优化**：大数据量分页不要用 offset，用主键过滤分页
   
   ```python
   # 低效：offset 10000，会扫描前10000条
   stmt = select(User).limit(10).offset(10000)
   # 高效：主键过滤，只扫描需要的10条
   stmt = select(User).where(User.id > 10000).limit(10)
   ```

5. **控制关联加载**：只加载需要的关联数据，不要加载无用的关联表

### 5.3 批量操作优化

- 新增 / 更新大量数据时，用`bulk_insert_mappings`/`execute(insert().values())`，不要循环 add
- 批量更新 / 删除用条件语句，不要循环查询再修改 / 删除
- 万级以上数据操作，建议分批次执行，避免长事务锁表

### 5.4 资源释放规范

1. **必须用 async with 上下文管理会话**：自动关闭会话，归还连接到连接池，避免连接泄露
2. **程序退出时关闭引擎**：`await async_engine.dispose()`，释放所有连接
3. **不要长会话占用连接**：会话用完就关闭，不要全局持有一个会话，用完不释放
