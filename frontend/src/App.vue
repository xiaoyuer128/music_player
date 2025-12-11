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
          <el-form label-position="top">
            <el-form-item>
              <el-input v-model="uploadForm.title" placeholder="歌名" prefix-icon="Headset" />
            </el-form-item>
            <el-form-item>
              <el-input v-model="uploadForm.artist" placeholder="歌手" prefix-icon="User" />
            </el-form-item>

            <el-upload
              class="upload-box"
              drag
              action=""
              :http-request="handleUpload"
              :show-file-list="false"
            >
              <el-icon class="el-icon--upload"><upload-filled /></el-icon>
              <div class="el-upload__text">拖拽 mp3 到此处</div>
            </el-upload>
          </el-form>
        </div>
      </el-aside>

      <el-main class="glass-content">
        <div class="content-header">
          <h2>全站歌单 <el-tag effect="dark" round size="small">{{ getModeName() }}</el-tag></h2>
          <el-button circle icon="Refresh" @click="fetchSongs" />
        </div>

        <div class="song-grid">
           <div
             v-for="song in songList"
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
        <el-button circle icon="ArrowLeft" @click="prevSong" />

        <el-button
           circle
           size="large"
           type="primary"
           @click="togglePlay"
           class="play-btn"
        >
          <el-icon size="24">
            <component :is="isPlaying ? 'VideoPause' : 'VideoPlay'" />
          </el-icon>
        </el-button>

        <el-button circle icon="ArrowRight" @click="nextSong(true)" />
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

      <audio
        ref="audioPlayer"
        controls
        autoplay
        :src="currentSong.url"
        class="custom-audio"
        @play="isPlaying = true"
        @pause="isPlaying = false"
        @ended="autoNext"
      ></audio>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'
// 🔥 引入新图标：ArrowLeft, ArrowRight, Sort (顺序), Connection (随机)
import { Headset, User, UploadFilled, VideoPlay, VideoPause, Delete, Refresh, Lock, ArrowLeft, ArrowRight, Sort, Connection } from '@element-plus/icons-vue'

// --- 基础状态 ---
const isLoggedIn = ref(false)
const isRegisterMode = ref(false)
const isLoading = ref(false)
const authForm = ref({ username: '', password: '' })

const songList = ref([])
const uploadForm = ref({ title: '', artist: '' })
const currentSong = ref({})

// --- 播放状态 ---
const isPlaying = ref(false)
const audioPlayer = ref(null)

// 🔥 新增：播放模式 'sequence'(顺序) | 'loop'(单曲循环) | 'random'(随机)
const playMode = ref('sequence')

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

const handleUpload = async (options) => {
  if (!uploadForm.value.title || !uploadForm.value.artist) return ElMessage.warning('请先填写信息')
  const formData = new FormData()
  formData.append('file', options.file)
  formData.append('title', uploadForm.value.title)
  formData.append('artist', uploadForm.value.artist)

  try {
    await axios.post('/songs/', formData)
    ElMessage.success('上传成功')
    uploadForm.value = { title: '', artist: '' }
    fetchSongs()
  } catch (error) {
    ElMessage.error('上传失败')
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
    }
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

/* 播放控制按钮区 */
.player-controls { margin: 0 20px; display: flex; align-items: center; gap: 15px; } /* 增加了 gap 间距 */
.player-actions { margin-right: 20px; }
.play-btn { background: linear-gradient(135deg, #ff9966, #ff5e62); border: none; transition: transform 0.1s; }
.play-btn:active { transform: scale(0.95); }

/* 认证界面 */
.auth-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); backdrop-filter: blur(10px); z-index: 2000; display: flex; justify-content: center; align-items: center; }
.auth-box { width: 350px; background: rgba(30, 30, 40, 0.9); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 40px; text-align: center; }
.auth-box h2 { color: white; margin-bottom: 30px; }
.auth-btn { width: 100%; margin-top: 10px; }
.toggle-text { margin-top: 20px; color: #aaa; font-size: 14px; }
.toggle-text span { color: #409EFF; cursor: pointer; margin-left: 5px; }
.user-info { text-align: center; color: rgba(255,255,255,0.6); margin-bottom: 20px; }
</style>