# backend/app/main.py

from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select,or_
from typing import List
import shutil
import os
from uuid import uuid4
from jose import JWTError, jwt
# 在顶部 import 区域增加：
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB


# 引入我们刚才写好的模块
from .core.database import create_db_and_tables, get_session
from .models import User, Song, Playlist, PlaylistSongLink
from .core.security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM

app = FastAPI()

# 静态文件和生命周期代码保持不变...
app.mount("/static", StaticFiles(directory="static"), name="static")
UPLOAD_DIR = "static/music"
os.makedirs(UPLOAD_DIR, exist_ok=True)
COVER_DIR = "static/images"
os.makedirs(COVER_DIR, exist_ok=True)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# --- 身份验证核心逻辑 ---

# 定义 Token 来源：告诉 FastAPI，Token 会放在请求头的 Authorization 字段里
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# 依赖函数：根据 Token 获取当前用户 (用来保护接口)
async def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # 解析 Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # 查数据库找用户
    statement = select(User).where(User.username == username)

    user = session.exec(statement).first()
    if user is None:
        raise credentials_exception
    return user


# --- 接口 API ---

# 1. 注册接口
@app.post("/auth/register")
async def register(username: str = Form(...), password: str = Form(...), session: Session = Depends(get_session)):
    # 检查用户名是否已存在
    statement = select(User).where(User.username == username)
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户 (密码加密!)
    new_user = User(username=username, hashed_password=get_password_hash(password))
    session.add(new_user)
    session.commit()
    return {"message": "注册成功"}
    print(f"DEBUG: 接收到的用户名: {username}, 密码长度: {len(password)}, 密码内容: {password}")


# 2. 登录接口 (获取 Token)
@app.post("/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    # 查找用户
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()

    # 验证用户是否存在以及密码是否正确
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 生成 Token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


def extract_metadata(file_path: str):
    """
    从 MP3 文件中提取元数据 (封面、时长、专辑等)
    """
    metadata = {
        "duration": 0.0,
        "album": "未知专辑",
        "cover_url": None,  # 默认没有封面
        "title": None,
        "artist": None
    }

    try:
        audio = MP3(file_path, ID3=ID3)

        # 1. 获取时长 (秒)
        metadata["duration"] = audio.info.length

        # 2. 读取 ID3 标签
        if audio.tags:
            # 提取文本信息 (如果有的话)
            if "TIT2" in audio.tags: metadata["title"] = str(audio.tags["TIT2"])  # 歌名
            if "TPE1" in audio.tags: metadata["artist"] = str(audio.tags["TPE1"])  # 歌手
            if "TALB" in audio.tags: metadata["album"] = str(audio.tags["TALB"])  # 专辑

            # 3. 提取封面图 (APIC 帧)
            # 遍历所有标签查找图片
            for tag in audio.tags.values():
                if isinstance(tag, APIC):
                    # 找到了图片！保存到磁盘
                    cover_filename = f"{uuid4()}.jpg"  # 生成个随机名
                    cover_path = os.path.join(COVER_DIR, cover_filename)

                    with open(cover_path, "wb") as img_file:
                        img_file.write(tag.data)

                    metadata["cover_url"] = f"/{COVER_DIR}/{cover_filename}"
                    break  # 只取一张

    except Exception as e:
        print(f"元数据提取失败: {e}")

    return metadata



# 3. 上传歌曲 (增加了 user 依赖，只有登录才能传)
# backend/app/main.py

@app.post("/songs/")
async def add_song(
        file: UploadFile = File(...),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 1. 验证文件格式
    if not file.filename.endswith((".mp3", ".wav", ".flac")):
        raise HTTPException(status_code=400, detail="格式不支持")

    # 2. 保存文件到硬盘
    file_uuid = str(uuid4())
    file_ext = file.filename.split(".")[-1]
    saved_filename = f"{file_uuid}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. 🌟 核心修改：调用现有的 extract_metadata 函数提取信息
    # 注意：extract_metadata 函数你之前的代码里已经定义好了，直接用即可
    metadata = extract_metadata(file_path)

    # 4. 智能判断：如果提取不到元数据，就用文件名兜底
    # 去掉文件后缀作为默认标题
    filename_no_ext = file.filename.rsplit('.', 1)[0]

    final_title = metadata.get("title") or filename_no_ext
    final_artist = metadata.get("artist") or "未知艺术家"
    final_cover = metadata.get("cover_url")  # 如果提取到了封面，会返回路径
    final_duration = int(metadata.get("duration", 0))

    web_url = f"/static/music/{saved_filename}"

    # 5. 存入数据库
    new_song = Song(
        title=final_title,
        artist=final_artist,
        url=web_url,
        cover_image=final_cover,  # 存入提取到的封面
        duration=final_duration,  # 存入时长
        owner_id=current_user.id
    )

    session.add(new_song)
    session.commit()
    session.refresh(new_song)
    return new_song


# 2. 修改获取歌曲列表接口
@app.get("/songs/", response_model=List[Song])
async def get_songs(
        session: Session = Depends(get_session),
        q: str | None = None  # 👈 新增：接收搜索关键词，默认为空
):
    statement = select(Song)

    # 如果用户传了搜索词，就加筛选条件
    if q:
        # statement.where(or_(条件A, 条件B)) 表示 A 或 B 满足一个即可
        statement = statement.where(
            or_(
                Song.title.contains(q),  # 歌名包含 q
                Song.artist.contains(q)  # 歌手包含 q
            )
        )

    # 执行查询
    songs = session.exec(statement).all()
    return songs

# 5. 删除歌曲 (只有歌曲的主人才能删！)
@app.delete("/songs/{song_id}")
async def delete_song(
        song_id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)  # 依然需要登录权限
):
    # 1. 在数据库中查找歌曲
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="歌曲不存在")

    # 2. 权限验证：必须是“主人”才能删
    if song.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="你没有权限删除这首歌")

    # --- 🗑️ 新增：物理文件删除逻辑 ---
    try:
        # 数据库存的 url 是类似 "/static/music/xxxx.mp3"
        # 实际硬盘路径是 "static/music/xxxx.mp3" (相对路径)
        # 所以我们需要把开头的 "/" 去掉
        file_path = song.url.lstrip("/")

        # 检查文件是否存在，防止文件早就被手动删了导致程序报错
        if os.path.exists(file_path):
            os.remove(file_path)  # <--- 这一句是真正的“删文件”
            print(f"DEBUG: 成功删除物理文件 {file_path}")
        else:
            print(f"DEBUG: 文件 {file_path} 不存在，跳过物理删除")

    except Exception as e:
        # 如果删文件出错了（比如文件被占用），打印错误，但不要阻断数据库删除
        # 我们希望至少把数据库清理干净
        print(f"ERROR: 删除文件失败: {e}")

    # ----------------------------------

    # 3. 删除数据库记录
    session.delete(song)
    session.commit()

    return {"ok": True}


# --- 🎵 歌单管理接口 (新增) ---

# 6. 创建新歌单
@app.post("/playlists/", response_model=Playlist)
async def create_playlist(
        title: str = Form(...),
        description: str = Form(None),
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 创建歌单对象，并标记主人是当前用户
    new_playlist = Playlist(title=title, description=description, owner_id=current_user.id)
    session.add(new_playlist)
    session.commit()
    session.refresh(new_playlist)
    return new_playlist


# 7. 获取“我”的所有歌单
@app.get("/playlists/", response_model=List[Playlist])
async def get_my_playlists(
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 利用 SQLModel 的关系字段，直接返回用户的 playlists
    # 如果报错，说明 relationship 定义有问题，但根据你之前上传的 models.py 应该是没问题的
    return current_user.playlists


# 8. 把歌曲添加到歌单
@app.post("/playlists/{playlist_id}/songs/{song_id}")
async def add_song_to_playlist(
        playlist_id: int,
        song_id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 1. 先找歌单
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="歌单不存在")

    # 2. 只有歌单的主人才能往里加歌
    if playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="你没有权限修改此歌单")

    # 3. 找歌曲
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="歌曲不存在")

    # 4. 检查是否已经在歌单里了 (避免重复添加)
    # 我们查中间表
    statement = select(PlaylistSongLink).where(
        PlaylistSongLink.playlist_id == playlist_id,
        PlaylistSongLink.song_id == song_id
    )
    link = session.exec(statement).first()
    if link:
        return {"message": "歌曲已在歌单中", "ok": True}

    # 5. 添加关联
    new_link = PlaylistSongLink(playlist_id=playlist_id, song_id=song_id)
    session.add(new_link)
    session.commit()

    return {"message": "添加成功", "ok": True}


# 9. 获取某个歌单里的所有歌曲
@app.get("/playlists/{playlist_id}/songs", response_model=List[Song])
async def get_playlist_songs(
        playlist_id: int,
        session: Session = Depends(get_session)
):
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="歌单不存在")

    return playlist.songs


# --- 🗑️ 歌单删除逻辑 (新增) ---

# 10. 删除整个歌单
@app.delete("/playlists/{playlist_id}")
async def delete_playlist(
        playlist_id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 1. 找歌单
    playlist = session.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="歌单不存在")

    # 2. 验证权限
    if playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="你没有权限删除此歌单")

    # 3. 删除歌单内的关联记录 (中间表)
    # 虽然数据库可能有级联删除，但手动清空更安全
    statement = select(PlaylistSongLink).where(PlaylistSongLink.playlist_id == playlist_id)
    links = session.exec(statement).all()
    for link in links:
        session.delete(link)

    # 4. 删除歌单本身
    session.delete(playlist)
    session.commit()
    return {"ok": True}


# 11. 从歌单里移除某一首歌 (注意：不是物理删除歌曲，只是解除关系)
@app.delete("/playlists/{playlist_id}/songs/{song_id}")
async def remove_song_from_playlist(
        playlist_id: int,
        song_id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 1. 验证歌单权限
    playlist = session.get(Playlist, playlist_id)
    if not playlist or playlist.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="没有权限")

    # 2. 找关联记录
    statement = select(PlaylistSongLink).where(
        PlaylistSongLink.playlist_id == playlist_id,
        PlaylistSongLink.song_id == song_id
    )
    link = session.exec(statement).first()

    # 3. 删除关联
    if link:
        session.delete(link)
        session.commit()

    return {"ok": True}


# --- ✏️ 编辑歌曲接口 (新增) ---

@app.patch("/songs/{song_id}")
async def update_song(
        song_id: int,
        title: str = Form(None),  # 允许为空，为空就不改
        artist: str = Form(None),
        cover: UploadFile = File(None),  # 允许上传新封面
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user)
):
    # 1. 找歌
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="歌曲不存在")

    # 2. 验证权限
    if song.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="你没有权限修改这首歌")

    # 3. 更新文本字段
    if title:
        song.title = title
    if artist:
        song.artist = artist

    # 4. 如果上传了新封面，处理图片保存
    if cover:
        # 生成随机文件名
        file_ext = cover.filename.split(".")[-1]
        cover_filename = f"{uuid4()}.{file_ext}"
        cover_path = os.path.join(COVER_DIR, cover_filename)

        # 保存文件
        with open(cover_path, "wb") as buffer:
            shutil.copyfileobj(cover.file, buffer)

        # 更新数据库路径
        song.cover_image = f"/{COVER_DIR}/{cover_filename}"

    # 5. 提交保存
    session.add(song)
    session.commit()
    session.refresh(song)

    return song
