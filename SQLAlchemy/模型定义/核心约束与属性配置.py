from sqlalchemy import Integer, String,DateTime,func
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'user'
    # 主键:primary_key = True，必须有一个主键,唯一约束：unique=True，值不能重复
    id:Mapped[int] = mapped_column(Integer,primary_key=True,unique=True,comment='用户ID')
    # 非空约束:nullable=False，不允许为空
    name:Mapped[str] = mapped_column(String(50),nullable=False,comment='姓名')
    # 默认值：default，插入时不赋值则用默认值
    number:Mapped[str] = mapped_column(String(50),nullable=False,default='None',comment='号码')
    # 时间默认值：用func.now()获取数据库当前时间，不用Python的datetime.now()
    created_at:Mapped[datetime] = mapped_column(DateTime, default=func.now(), comment='创建时间')
    # 自动更新时间：onupdate，数据更新时自动刷新时间
    updated_at:Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), comment='更新时间')
