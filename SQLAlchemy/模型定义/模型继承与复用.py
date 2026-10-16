from sqlalchemy import String,Integer
from sqlalchemy.orm import DeclarativeBase,Mapped,mapped_column


class Base(DeclarativeBase):
    # 抽象基类,不会生成表
    __abstract__ = True
    # 所有表通用字段
    id:Mapped[int] = mapped_column(Integer,primary_key=True,comment='用户ID')
    name:Mapped[str] = mapped_column(String(50),comment='姓名')
    number:Mapped[str] = mapped_column(String(50),comment='号码')


# 继承通用基类，自动拥有id等字段
class User(Base):
    __tablename__ = 'user'
    # 可以添加这个表独有字段
    email:Mapped[str] = mapped_column(String(100), unique=True, nullable=False)

class Book(Base):
    __tablename__ = 'book'
    user_id:Mapped[int] = mapped_column(Integer)

print("User模型字段：", [k for k in User.__mapper__.columns.keys()])
print("Book模型字段：", [k for k in Book.__mapper__.columns.keys()])