from sqlalchemy import Index,String,Integer
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column

URL = 'mysql+aiomysql://root:123456@localhost:3306/study?charset=utf8mb4'

class Base(DeclarativeBase):
    pass



# 索引定义
class User(Base):
    __tablename__ = 'user'
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    name:Mapped[str] = mapped_column(String(50))
    number:Mapped[str] = mapped_column(String(50))

    # 联合索引
    __table_args__ = (
        # 单字段索引
        Index('ix_user_name','name'),
        Index('ix_user_number','number'),
        # 普通联合索引
        Index('ix_name_number','name','number'),
    )


