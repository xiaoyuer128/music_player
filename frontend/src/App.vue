<template>
  <div class="main-layout">
    <div class="background-animation"></div>

    <div v-if="!isLoggedIn" class="auth-overlay">
      <div class="auth-box glass-content">
        <h2>{{ isRegisterMode ? '注册账户' : '欢迎登录' }}</h2>
        <el-form label-position="top">
          <el-form-item label="用户名">
            <el-input v-model="authForm.username" prefix-icon="User" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input v-model="authForm.password" type="password" prefix-icon="Lock" />
          </el-form-item>
          <el-button
            type="primary"
            native-type="button"
            class="auth-btn"
            @click.prevent="handleAuth"
            :loading="isLoading"
          >
            {{ isRegisterMode ? '立即注册' : '登录' }}
          </el-button>
          <div class="toggle-text">
            {{ isRegisterMode ? '已有账号？' : '还没有账号？' }}
            <span @click="isRegisterMode = !isRegisterMode">
              {{ isRegisterMode ? '去登录' : '去注册' }}
            </span>
          </div>
        </el-form>
      </div>
    </div>

    <el-container style="height: 100vh;" v-else>
      <el-aside width="250px" class="glass-sidebar">
        <div class="logo-area">
          <h2>🎧 小鱼儿音乐</h2>
          <div class="user-info">
             👋 {{ authForm.username }}
             <el-button link type="danger" size="small" @click="logout">退出</el-button>
          </div>
        </div>

        <div class="upload-area">
  <h3>上传新歌</h3>
  <el-upload
    class="upload-box"
    drag
    action=""
    :http-request="handleUpload"
    :show-file-list="false"
    :disabled="isUploading"
  >
    <el-icon class="el-icon--upload"><upload-filled /></el-icon>
    <div class="el-upload__text">
       {{ isUploading ? '正在分析...' : '拖拽 MP3 自动识别' }}
    </div>
  </el-upload>
</div>
      </el-aside>

      <el-main class="glass-content">
        <div class="content-header">
    <h2>全站歌单 <el-tag effect="dark" round size="small">{{ getModeName() }}</el-tag></h2>

    <div class="header-center">
      <div class="search-wrapper" :class="{ 'active': isSearchActive }">
        <div class="search-icon-btn" @click="isSearchActive = !isSearchActive">
           <el-icon :size="20"><Search /></el-icon>
        </div>
        <input
           v-model="searchQuery"
           class="search-input"
           type="text"
           placeholder="搜索歌名或歌手..."
        />
        <span v-if="searchQuery" class="clear-btn" @click="searchQuery = ''">×</span>
      </div>
    </div>

    <el-button circle icon="Refresh" @click="fetchSongs" />
  </div>


        <div class="song-grid">
           <div
             v-for="song in filteredSongList"
             :key="song.id"
             class="song-card"
             :class="{ 'active-card': currentSong.id === song.id }"
             @click="playMusic(song)"
           >
            <div class="card-cover">
              <div class="placeholder-cover"><el-icon size="40"><Headset /></el-icon></div>
              <div class="play-overlay"><el-icon size="30"><VideoPlay /></el-icon></div>
            </div>
            <div class="card-info">
              <div class="song-title">{{ song.title }}</div>
              <div class="song-artist">{{ song.artist }}</div>
            </div>
            <el-button class="delete-btn" type="danger" icon="Delete" circle size="small" @click.stop="deleteSong(song.id)" />

           </div>
          <div v-if="filteredSongList.length === 0" class="empty-state">
        没有找到相关歌曲
     </div>
        </div>
      </el-main>
    </el-container>

    <div class="player-bar" v-if="currentSong.url">
      <div class="player-info">
        <div class="spinning-disc" :style="{ animationPlayState: isPlaying ? 'running' : 'paused' }"></div>
        <div>
          <div class="p-title">{{ currentSong.title }}</div>
          <div class="p-artist">{{ currentSong.artist }}</div>
        </div>
      </div>

     <div class="player-controls">

  <el-button circle size="default" @click="prevSong" class="control-btn">
    <el-icon :size="18"><ArrowLeft /></el-icon>
  </el-button>

  <el-button
   circle
   size="large"
   type="primary"
   @click="togglePlay"
   class="play-btn"
>
  <el-icon v-if="isPlaying" :size="28" color="#fff">
    <VideoPause />
  </el-icon>

  <el-icon v-else :size="28" color="#fff">
    <VideoPlay />
  </el-icon>
</el-button>

  <el-button circle size="default" @click="nextSong(true)" class="control-btn">
    <el-icon :size="18"><ArrowRight /></el-icon>
  </el-button>

</div>

      <div class="player-actions">
        <el-tooltip :content="getModeName()" placement="top">
            <el-button
                circle
                size="default"
                @click="toggleMode"
                style="background: rgba(255,255,255,0.1); border: none;"
            >
                <el-icon :size="20" :color="getModeColor()">
                    <component :is="playMode === 'sequence' ? 'Sort' : playMode === 'loop' ? 'Refresh' : 'Connection'" />
                </el-icon>
            </el-button>
        </el-tooltip>
      </div>
      <div class="progress-box">
  <span class="time-text">{{ formatTime(currentTime) }}</span>

  <el-slider
    v-model="currentTime"
    :max="duration"
    @change="seekAudio"
    @input="isDragging = true"
    :show-tooltip="false"
    size="small"
  />

  <span class="time-text">{{ formatTime(duration) }}</span>
</div>

<div class="volume-box">
    <el-icon><Microphone /></el-icon> <el-slider v-model="volume" :max="1" :step="0.01" @input="setVolume" style="width: 80px; margin-left: 10px"/>
</div>

<audio
  ref="audioPlayer"
  :src="currentSong.url"
  autoplay
  style="display: none;"
  @play="isPlaying = true"
  @pause="isPlaying = false"
  @ended="autoNext"
  @timeupdate="onTimeUpdate"
  @loadedmetadata="onLoadedMetadata"
></audio>


<!--      <audio-->
<!--        ref="audioPlayer"-->
<!--        controls-->
<!--        autoplay-->
<!--        :src="currentSong.url"-->
<!--        class="custom-audio"-->
<!--        @play="isPlaying = true"-->
<!--        @pause="isPlaying = false"-->
<!--        @ended="autoNext"-->
<!--      ></audio>-->
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted,computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
// 🔥 引入新图标：ArrowLeft, ArrowRight, Sort (顺序), Connection (随机)
// import { Headset, User, UploadFilled, VideoPlay, Search ,ArrowLeft, ArrowRight,  ideoPause} from '@element-plus/icons-vue'
// 找到 src/App.vue 顶部的 icons 引入代码，换成下面这一大段：
import {
  Headset,
  User,
  UploadFilled,
  VideoPlay,
  VideoPause,
  Delete,
  Refresh,
  Lock,
  ArrowLeft,   // 👈 这次用到的
  ArrowRight,  // 👈 这次用到的
  Sort,
  Connection,
  Search,      // 👈 上次搜索功能用到的
  Microphone   // 👈 之前音量功能可能用到的
} from '@element-plus/icons-vue'



// --- 基础状态 ---
const isLoggedIn = ref(false)
const isRegisterMode = ref(false)
const isLoading = ref(false)
const authForm = ref({ username: '', password: '' })
const isUploading = ref(false)
const songList = ref([])
// const uploadForm = ref({ title: '', artist: '' })
const currentSong = ref({})
// --- 播放状态 ---
const isPlaying = ref(false)
const audioPlayer = ref(null)
const currentTime = ref(0) // 当前播放秒数
const duration = ref(0)    // 总时长秒数
const volume = ref(1.0)    // 音量 0.0 ~ 1.0
const isDragging = ref(false) // 防止拖拽时进度条乱跳

const isSearchActive = ref(false) // 控制搜索框是否展开
const searchQuery = ref('')       // 搜索关键词

// 🔥 新增：播放模式 'sequence'(顺序) | 'loop'(单曲循环) | 'random'(随机)
const playMode = ref('sequence')



// 2. 监听音频元数据加载（获取总时长）
const onLoadedMetadata = () => {
  duration.value = audioPlayer.value.duration
}


// 3. 监听播放进度更新
const onTimeUpdate = () => {
  // 如果用户正在拖拽，就不要自动更新进度条，否则会闪烁
  if (!isDragging.value) {
    currentTime.value = audioPlayer.value.currentTime
  }
}


// 创建一个计算属性：如果有搜索词，就过滤列表；否则显示全部
const filteredSongList = computed(() => {
  if (!searchQuery.value) return songList.value

  const query = searchQuery.value.toLowerCase().trim()
  return songList.value.filter(song => {
    // 同时也搜索歌手名，体验更好
    return song.title.toLowerCase().includes(query) ||
           song.artist.toLowerCase().includes(query)
  })
})



// 4. 用户拖拽进度条结束时触发
const seekAudio = (val) => {
  audioPlayer.value.currentTime = val
  isDragging.value = false
}


// 5. 调节音量
const setVolume = (val) => {
  audioPlayer.value.volume = val
}


// 6. 时间格式化工具 (把 125秒 变成 "02:05")
const formatTime = (seconds) => {
  if (!seconds) return '00:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
}


// --- 认证逻辑 (保持不变) ---
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
}, error => Promise.reject(error))

axios.interceptors.response.use(res => res, error => {
  if (error.response && error.response.status === 401) {
    ElMessage.error('登录过期')
    localStorage.removeItem('token')
    isLoggedIn.value = false
  }
  return Promise.reject(error)
})

const handleAuth = async () => {
  if(!authForm.value.username || !authForm.value.password) return ElMessage.warning('请输入账号密码')
  isLoading.value = true
  try {
    const formData = new FormData()
    formData.append('username', authForm.value.username)
    formData.append('password', authForm.value.password)

    if (isRegisterMode.value) {
      await axios.post('/auth/register', formData)
      ElMessage.success('注册成功')
      isRegisterMode.value = false
    } else {
      const res = await axios.post('/auth/token', formData)
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('username', authForm.value.username)
      isLoggedIn.value = true
      ElMessage.success('登录成功')
      fetchSongs()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    isLoading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('token')
  isLoggedIn.value = false
  currentSong.value = {}
  isPlaying.value = false
}

onMounted(() => {
  if (localStorage.getItem('token')) {
    isLoggedIn.value = true
    authForm.value.username = localStorage.getItem('username')
    fetchSongs()
  }
})
// ... 其他代码 ...

// 🔥 新增：根据当前模式返回不同的颜色
const getModeColor = () => {
    if (playMode.value === 'loop') return '#E6A23C'   // 橙色 (Element Warning色)
    if (playMode.value === 'random') return '#67C23A' // 绿色 (Element Success色)
    return '#FFFFFF' // 白色 (默认)
}

// ... fetchSongs 等代码 ...
// --- 歌曲业务逻辑 ---
const fetchSongs = async () => {
  try {
    const res = await axios.get('/songs/')
    songList.value = res.data
  } catch (error) {
    console.error(error)
  }
}
// src/App.vue <script setup> 内部



// 2.  handleUpload 函数
const handleUpload = async (options) => {
  isUploading.value = true // 开始转圈圈或显示状态

  const formData = new FormData()
  formData.append('file', options.file)
  // 注意：这里不再 append title 和 artist 了，后端会自己搞定

  try {
    await axios.post('/songs/', formData)
    ElMessage.success('上传成功！已自动识别歌曲信息')
    fetchSongs() // 刷新列表
  } catch (error) {
    console.error(error)
    ElMessage.error(error.response?.data?.detail || '上传失败')
  } finally {
    isUploading.value = false // 结束状态
  }
}

const deleteSong = async (id) => {
    try {
        await axios.delete(`/songs/${id}`)
        ElMessage.success('删除成功')
        fetchSongs()
    } catch (e) {
        ElMessage.error('删除失败')
    }
}

// --- 🔥 核心播放控制逻辑 🔥 ---

const playMusic = (song) => {
  if (currentSong.value.id === song.id) {
    togglePlay()
    return
  }
  currentSong.value = song
  isPlaying.value = true
}

const togglePlay = () => {
  if (isPlaying.value) audioPlayer.value.pause()
  else audioPlayer.value.play()
}

// 切换模式：顺序 -> 单曲 -> 随机 -> 顺序
const toggleMode = () => {
    const modes = ['sequence', 'loop', 'random']
    const nextIndex = (modes.indexOf(playMode.value) + 1) % modes.length
    playMode.value = modes[nextIndex]
}

// 获取模式名称 (用于显示)
const getModeName = () => {
    const map = { 'sequence': '顺序播放', 'loop': '单曲循环', 'random': '随机播放' }
    return map[playMode.value]
}

// 自动切歌 (当播放结束 @ended 时触发)
const autoNext = () => {
    if (playMode.value === 'loop') {
        // 单曲循环：重置时间，重新播放
        audioPlayer.value.currentTime = 0
        audioPlayer.value.play()
    } else {
        // 其他模式：切下一首
        nextSong()
    }//测试
}

// 下一曲
const nextSong = (manual = false) => {
    if (songList.value.length === 0) return

    let nextIndex = 0
    const currentIndex = songList.value.findIndex(s => s.id === currentSong.value.id)

    if (playMode.value === 'random') {
        // 随机模式：在列表里瞎选一个 (防止随到自己，简单处理)
        do {
            nextIndex = Math.floor(Math.random() * songList.value.length)
        } while (songList.value.length > 1 && nextIndex === currentIndex)
    } else {
        // 顺序模式 (或手动点击下一曲时忽略单曲循环)
        nextIndex = (currentIndex + 1) % songList.value.length
    }

    currentSong.value = songList.value[nextIndex]
    isPlaying.value = true
}

// 上一曲
const prevSong = () => {
    if (songList.value.length === 0) return

    let prevIndex = 0
    const currentIndex = songList.value.findIndex(s => s.id === currentSong.value.id)

    if (playMode.value === 'random') {
        // 随机模式：上一曲也是随机
        prevIndex = Math.floor(Math.random() * songList.value.length)
    } else {
        // 顺序模式：当前-1，如果是第一个就跳到最后一个
        prevIndex = (currentIndex - 1 + songList.value.length) % songList.value.length
    }

    currentSong.value = songList.value[prevIndex]
    isPlaying.value = true
}
</script>

<style>




/* 保持原有基础样式不变 */
body { margin: 0; font-family: sans-serif; background-color: #121212; color: white; overflow: hidden; }
.main-layout { position: relative; height: 100vh; width: 100vw; background: linear-gradient(135deg, #1e1e2e 0%, #2d2d42 100%); }
.glass-sidebar { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(20px); border-right: 1px solid rgba(255, 255, 255, 0.1); padding: 20px; display: flex; flex-direction: column; }
.logo-area h2 { color: #fff; margin-bottom: 30px; text-align: center; background: linear-gradient(45deg, #ff6b6b, #f06595); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.upload-area h3 { color: rgba(255,255,255,0.7); font-size: 14px; margin-bottom: 15px; }
.el-input__wrapper { background-color: rgba(0,0,0,0.2) !important; box-shadow: none !important; border: 1px solid rgba(255,255,255,0.1); }
.el-input__inner { color: white !important; }
.glass-content { padding: 30px; overflow-y: auto; padding-bottom: 100px; }
.content-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.song-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 20px; }
.song-card { background: rgba(255, 255, 255, 0.05); border-radius: 12px; padding: 15px; cursor: pointer; transition: all 0.3s ease; position: relative; }
.song-card:hover { background: rgba(255, 255, 255, 0.1); transform: translateY(-5px); }

/* 🔥 高亮当前播放的卡片 */
.active-card { border: 1px solid #ff9966; background: rgba(255, 153, 102, 0.1); }

.card-cover { width: 100%; aspect-ratio: 1/1; background: linear-gradient(120deg, #84fab0 0%, #8fd3f4 100%); border-radius: 8px; margin-bottom: 10px; position: relative; display: flex; align-items: center; justify-content: center; }
.play-overlay { position: absolute; opacity: 0; transition: opacity 0.3s; }
.song-card:hover .play-overlay { opacity: 1; }
.song-title { font-weight: bold; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-bottom: 5px; }
.song-artist { font-size: 12px; color: rgba(255,255,255,0.6); }
.delete-btn { position: absolute; top: 5px; right: 5px; opacity: 0; transition: opacity 0.2s; }
.song-card:hover .delete-btn { opacity: 1; }

/* 底部播放条样式更新 */
.player-bar { position: fixed; bottom: 0; left: 0; width: 100%; height: 80px; background: rgba(30, 30, 46, 0.9); backdrop-filter: blur(15px); border-top: 1px solid rgba(255, 255, 255, 0.1); display: flex; align-items: center; padding: 0 30px; z-index: 1000; box-sizing: border-box; }
.player-info { width: 200px; display: flex; align-items: center; }
.spinning-disc { width: 40px; height: 40px; border-radius: 50%; background: linear-gradient(to right, #ff9966, #ff5e62); margin-right: 15px; animation: spin 3s linear infinite; }
@keyframes spin { 100% { transform: rotate(360deg); } }
.p-title { font-weight: bold; font-size: 14px; }
.p-artist { font-size: 12px; color: #aaa; }
.custom-audio { flex: 1; height: 40px; outline: none; margin-left: 20px; }
/* 进度条区域 */
.progress-box {
  flex: 1; /* 占据剩余空间 */
  display: flex;
  align-items: center;
  margin: 0 20px;
}
.time-text {
  font-size: 12px;
  color: #ccc;
  width: 40px;
  text-align: center;
  margin: 0 10px;
}
/* 音量区域 */
.volume-box {
    display: flex;
    align-items: center;
    margin-right: 20px;
}
/* 覆盖 Element Slider 默认样式，让它更细更精致（可选） */
.el-slider__bar {
    background-color: #ff9966; /* 你的主题橙色 */
}
.el-slider__button {
    border-color: #ff9966;
}
/* 播放控制按钮区 */
.control-btn {
  background: rgba(255, 255, 255, 0.1) !important; /* 强制半透明背景 */
  border: none !important;
  color: #fff !important; /* 强制图标白色 */
  transition: all 0.2s;
}
.control-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important;
  transform: scale(1.1);
}

.player-controls { margin: 0 20px; display: flex; align-items: center; gap: 15px; } /* 增加了 gap 间距 */
.player-actions { margin-right: 20px; }
.play-btn {
  background: linear-gradient(135deg, #1f1f2e, #1f1f2f) !important;
  border: none !important;
  transform: scale(1.2); /* 让它比旁边的稍微大一点 */
  margin: 0 15px; /* 给左右留点距离 */
  box-shadow: 0 4px 10px rgb(40, 40, 59);
}
.play-btn:active {
  transform: scale(1.1); /* 点击时的按压效果 */
}

/* 认证界面 */
.auth-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); z-index: 2000; display: flex; justify-content: center; align-items: center; }
.auth-box { width: 350px; background: rgba(30, 30, 40, 0.9); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 40px; text-align: center; }
.auth-box h2 { color: white; margin-bottom: 30px; }
.auth-btn { width: 100%; margin-top: 10px; }
.toggle-text { margin-top: 20px; color: #aaa; font-size: 14px; }
.toggle-text span { color: #409EFF; cursor: pointer; margin-left: 5px; }
.user-info { text-align: center; color: rgba(255,255,255,0.6); margin-bottom: 20px; }

/* --- 🔍 顶部搜索框样式 --- */

/* 让头部布局变成：左(标题)-中(搜索)-右(刷新) */
.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  position: relative; /* 只要相对定位即可 */
}

/* 中间区域容器 */
.header-center {
  flex: 1;
  display: flex;
  justify-content: center; /* 居中显示 */
}

/* 搜索条外壳：初始状态是一个圆形的图标按钮大小 */
.search-wrapper {
  display: flex;
  align-items: center;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 5px;
  width: 40px; /* 初始宽度只有图标宽 */
  height: 40px;
  transition: all 0.4s cubic-bezier(0.18, 0.89, 0.32, 1.28); /* 弹性动画 */
  overflow: hidden;
  border: 1px solid transparent;
}

/* 激活状态：变宽 */
.search-wrapper.active {
  width: 300px; /* 展开后的宽度 */
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

/* 搜索图标 */
.search-icon-btn {
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #fff;
  flex-shrink: 0; /* 防止被压缩 */
}

/* 输入框：隐藏原生样式 */
.search-input {
  background: transparent;
  border: none;
  color: white;
  outline: none;
  font-size: 14px;
  margin-left: 10px;
  width: 100%;
  opacity: 0; /* 没展开时隐藏文字 */
  transition: opacity 0.3s ease;
}

/* 展开时显示输入框 */
.search-wrapper.active .search-input {
  opacity: 1;
}

/* 占位符颜色 */
.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

/* 清除按钮 */
.clear-btn {
  color: #999;
  cursor: pointer;
  padding: 0 8px;
  font-size: 18px;
}
.clear-btn:hover { color: white; }

/* 空状态提示 */
.empty-state {
  grid-column: 1 / -1; /* 跨越所有列 */
  text-align: center;
  color: rgba(255,255,255,0.4);
  padding: 50px;
}

</style>
