"""
作者：Zxy
"""
# backend/app/models.py

from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime


# --- 1. 关联表 (多对多关系：一个歌单有多首歌，一首歌可以在多个歌单) ---
class PlaylistSongLink(SQLModel, table=True):
    playlist_id: Optional[int] = Field(default=None, foreign_key="playlist.id", primary_key=True)
    song_id: Optional[int] = Field(default=None, foreign_key="song.id", primary_key=True)

# --- 3. 用户表 (User) ---
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)  # 用户名唯一
    email: Optional[str] = None
    hashed_password: str  # 必须存加密后的密码，不能存明文！
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 关联：一个用户可以创建多个歌单
    playlists: List["Playlist"] = Relationship(back_populates="owner")
    songs: List["Song"] = Relationship(back_populates="owner")

# --- 2. 歌曲表 (Song) ---
class Song(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(index=True)  # 歌名，加索引方便搜索
    artist: str = Field(index=True)  # 歌手

    # 核心字段：文件存放路径 (不要存文件本身进数据库！)
    url: str
    cover_image: Optional[str] = None  # 封面图路径
    duration: int = 0  # 时长(秒)

    # 反向关联 (可选，方便查询这首歌在哪些歌单里)
    playlists: List["Playlist"] = Relationship(back_populates="songs", link_model=PlaylistSongLink)
    owner_id: Optional[int] = Field(default=None, foreign_key="user.id")
    # 建立关联：这首歌属于哪个用户
    owner: Optional[User] = Relationship(back_populates="songs")

# --- 4. 歌单表 (Playlist) ---
class Playlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None

    # 外键：歌单属于哪个用户
    owner_id: int = Field(foreign_key="user.id")

    # 关联定义
    owner: Optional[User] = Relationship(back_populates="playlists")
    songs: List[Song] = Relationship(back_populates="playlists", link_model=PlaylistSongLink)