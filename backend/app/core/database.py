"""
作者：Zxy
"""
# backend/app/core/database.py

from sqlmodel import SQLModel, create_engine, Session

# 1. 定义数据库连接地址
# sqlite:///music_app.db 表示在当前目录下生成一个名为 music_app.db 的文件
sqlite_file_name = "music_app.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# 2. 创建引擎 (connect_args 是 SQLite 特有的配置，用于允许多线程访问)
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

# 3. 创建一个获取数据库会话的函数（给 API 以后用的）
def get_session():
    with Session(engine) as session:
        yield session

# 4. 初始化数据库的函数
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)