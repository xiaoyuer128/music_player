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

        <div class="playlist-area">
  <div class="playlist-header">
    <h3>我的歌单</h3>
    <el-button circle size="small" icon="Plus" @click="handleAddPlaylist" />
  </div>

  <div class="playlist-list">
    <div class="playlist-item" @click="fetchSongs">
       <el-icon><Headset /></el-icon>
       <span>所有歌曲</span>
    </div>

    <div
        v-for="pl in myPlaylists"
        :key="pl.id"
        class="playlist-item"
        :class="{ 'active-pl': currentPlaylist?.id === pl.id }"
        @click="selectPlaylist(pl)"
    >
      <div class="pl-name">
        <el-icon><List /></el-icon>
        <span>{{ pl.title }}</span>
      </div>

      <el-icon class="del-pl-btn" @click="deletePlaylist(pl, $event)"><Delete /></el-icon>
    </div>
  </div>
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

          <el-button circle icon="Refresh" @click="fetchSongs" class="refresh-btn" />
        </div>

        <div class="song-grid">
           <div
             v-for="song in filteredSongList"
             :key="song.id"
             class="song-card"
             :class="{ 'active-card': currentSong.id === song.id }"
             @click="playMusic(song)"
             @contextmenu="openContextMenu($event, song)"
           >
            <div class="card-cover">
              <div class="placeholder-cover"><el-icon size="40"><Headset /></el-icon></div>
              <div class="play-overlay"><el-icon size="30"><VideoPlay /></el-icon></div>
            </div>
            <div class="card-info">
              <div class="song-title">{{ song.title }}</div>
              <div class="song-artist">{{ song.artist }}</div>
            </div>
<!--             <el-button-->
<!--                 class="add-btn"-->
<!--                 type="warning"-->
<!--                 icon="FolderAdd"-->
<!--                 circle-->
<!--                 size="small"-->
<!--                 @click.stop="openAddToPlaylist(song)"-->
<!--             />-->
<!--            <el-button class="delete-btn" type="danger" icon="Delete" circle size="small" @click.stop="deleteSong(song.id)" />-->
           </div>

           <div v-if="filteredSongList.length === 0" class="empty-state">
              没有找到相关歌曲
           </div>
        </div>
      </el-main>
    </el-container>

    <transition name="slide-up">
      <div v-show="showLyricsPage" class="lyrics-overlay">
        <div class="blur-bg" :style="{ backgroundImage: `url(${currentSong.cover_image || ''})` }"></div>

        <div class="close-lyrics" @click="showLyricsPage = false">
          <el-icon><ArrowDown /></el-icon>
        </div>

        <div class="lyrics-content-layout">
          <div class="left-cover">
             <div class="big-cover-box" :class="{ 'playing': isPlaying }">
                <img v-if="currentSong.cover_image" :src="currentSong.cover_image" />
                <div v-else class="placeholder-disc"><el-icon><Headset /></el-icon></div>
             </div>
             <div class="big-info">
                <h2>{{ currentSong.title }}</h2>
                <p>{{ currentSong.artist }}</p>
             </div>
          </div>

          <div class="right-lyrics" ref="lyricsContainer">
             <div v-if="parsedLyrics.length === 0" class="no-lyrics-text">暂无歌词</div>
             <p
               v-for="(line, index) in parsedLyrics"
               :key="index"
               class="lrc-line"
               :class="{ 'active': currentLyricIndex === index }"
             >
               {{ line.text }}
             </p>
             <div style="height: 50vh;"></div>
          </div>
        </div>
      </div>
    </transition>

    <div class="player-bar" v-if="currentSong.url">

      <div class="player-info" @click="showLyricsPage = !showLyricsPage">
        <div class="spinning-disc" :style="{ animationPlayState: isPlaying ? 'running' : 'paused' }"></div>
        <div>
          <div class="p-title">{{ currentSong.title }}</div>
          <div class="p-artist">{{ currentSong.artist }}</div>
        </div>
        <el-icon class="expand-icon"><ArrowUp /></el-icon>
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
                  <Sort v-if="playMode === 'sequence'" />
                  <Refresh v-else-if="playMode === 'loop'" />
                  <Connection v-else-if="playMode === 'random'" />
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
          <el-icon><Microphone /></el-icon>
          <el-slider v-model="volume" :max="1" :step="0.01" @input="setVolume" style="width: 80px; margin-left: 10px"/>
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

    </div>
        <el-dialog
            v-model="showAddDialog"
            title="收藏到歌单"
            width="300px"
            class="glass-dialog"
            center
        >
          <div class="playlist-select-list">
            <div
                v-for="pl in myPlaylists"
                :key="pl.id"
                class="dialog-item"
                @click="addToPlaylist(pl.id)"
            >
              <el-icon><List /></el-icon>
              <span>{{ pl.title }}</span>
            </div>
            <div v-if="myPlaylists.length === 0" style="text-align:center; color:#999; padding:20px;">
              暂无歌单，请先去左侧新建
            </div>
          </div>
        </el-dialog>
    <div
        v-show="contextMenu.visible"
        class="custom-context-menu"
        :style="{ top: contextMenu.y + 'px', left: contextMenu.x + 'px' }"
        @click.stop
    >
      <div class="menu-header" v-if="contextMenu.song">
        {{ contextMenu.song.title }}
      </div>

      <div class="menu-item" @click="playMusic(contextMenu.song); closeContextMenu()">
        <el-icon><VideoPlay /></el-icon> 立即播放
      </div>

      <div class="menu-item" @click="openAddToPlaylist(contextMenu.song); closeContextMenu()">
        <el-icon><FolderAdd /></el-icon> 收藏到歌单
      </div>

      <div class="menu-divider"></div>

      <div class="menu-item" @click="nextSong(); closeContextMenu()">
        <el-icon><ArrowRight /></el-icon> 切下一首
      </div>

      <div class="menu-divider"></div>

      <div class="menu-item delete" @click="deleteSong(contextMenu.song.id); closeContextMenu()">
        <el-icon><Delete /></el-icon> 删除歌曲
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted,computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox} from 'element-plus'
// 🔥 引入新图标：ArrowLeft, ArrowRight, Sort (顺序), Connection (随机)
// import { Headset, User, UploadFilled, VideoPlay, Search ,ArrowLeft, ArrowRight,  ideoPause} from '@element-plus/icons-vue'
// 找到 src/App.vue 顶部的 icons 引入代码，换成下面这一大段：
import {
  FolderAdd,
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
  Microphone,
  ArrowDown,// 👈 之前音量功能可能用到的
  Plus,
  List
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

const showLyricsPage = ref(false) // 控制遮罩层显示
const parsedLyrics = ref([])      // 解析后的歌词
const currentLyricIndex = ref(-1) // 当前高亮行
const lyricsContainer = ref(null) // DOM 引用


const sampleLRC = `[00:00.00]开始懂了 - 孙燕姿
[00:04.00]词：姚若龙 曲：李偲菘
[00:12.91]我竟然没有调头
[00:15.89]最残忍那一刻
[00:19.46]静静看你走
[00:23.08]一点都不像我
[00:26.54]原来人会变得温柔
[00:30.93]是透彻的懂了
[00:35.31]爱情是流动的 不由人的
[00:41.28]何必激动着要理由
[00:46.59]相信你只是怕伤害我
[00:50.84]不是骗我
[00:53.69]很爱过谁会舍得
[00:57.17]把我的梦摇醒了
[01:00.56]宣布幸福不会来了
[01:06.18]用心酸微笑去原谅了
[01:10.50]也翻越了
[01:13.23]有昨天还是好的
[01:16.85]但明天是自己的
[01:20.15]开始懂了
[01:22.58]快乐是选择`

// 2. 监听音频元数据加载（获取总时长）
const onLoadedMetadata = () => {
  duration.value = audioPlayer.value.duration
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
    fetchPlaylists()
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
  currentPlaylist.value = null
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

// 智能删除：根据当前模式，决定是“物理删除”还是“移出歌单”
const deleteSong = async (id) => {
    try {
        if (currentPlaylist.value) {
            // 模式 A：在歌单里 -> 移出歌单
            await axios.delete(`/playlists/${currentPlaylist.value.id}/songs/${id}`)
            ElMessage.success('已从歌单移除')
            selectPlaylist(currentPlaylist.value)
        } else {
            // 模式 B：在“所有歌曲”里 -> 物理删除
            // 👇👇👇 修正点：这里原来写成了 axios.confirm，必须改回 ElMessageBox.confirm
            await ElMessageBox.confirm(
                '确定要彻底删除这首歌吗？物理文件也将被清除。',
                '警告',
                {
                    confirmButtonText: '确定删除',
                    cancelButtonText: '取消',
                    type: 'warning'
                }
            )

            // 确认后再发请求
            await axios.delete(`/songs/${id}`)
            ElMessage.success('物理删除成功')
            fetchSongs()
        }
    } catch (e) {
        // 如果用户点击取消，e 会等于 'cancel'，这时候不报错
        if (e !== 'cancel') {
            console.error(e) // 打印具体错误到控制台，方便调试
            ElMessage.error('操作失败')
        }
    }
}


// --- 🎵 歌单管理逻辑 (新增) ---
const myPlaylists = ref([]) // 存储我的歌单列表
const currentPlaylist = ref(null)


// 1. 获取歌单列表
const fetchPlaylists = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await axios.get('/playlists/')
    myPlaylists.value = res.data
  } catch (e) {
    console.error("获取歌单失败", e)
  }
}

// 2. 创建新歌单 (弹出输入框)
const handleAddPlaylist = async () => {
  try {
    const { value } = await ElMessageBox.prompt('请输入歌单名称', '新建歌单', {
      confirmButtonText: '创建',
      cancelButtonText: '取消',
      inputPattern: /\S+/,
      inputErrorMessage: '歌单名不能为空'
    })

    const formData = new FormData()
    formData.append('title', value)

    // 发送请求
    await axios.post('/playlists/', formData)
    ElMessage.success('创建成功')
    fetchPlaylists()
  } catch (e) {
    // 💡 修改这里：区分是“取消”还是“报错”
    if (e === 'cancel') {
        console.log('用户取消输入')
    } else {
        console.error(e)
        // 把后端的错误信息弹出来！
        ElMessage.error(e.response?.data?.detail || '创建失败，请检查后端控制台')
    }
  }
}

const deletePlaylist = async (playlist, event) => {
    // 阻止冒泡，不然会触发“进入歌单”
    if(event) event.stopPropagation()

    try {
        await ElMessageBox.confirm(`确定要删除歌单 "${playlist.title}" 吗？`, '提示', {
            type: 'warning'
        })
        await axios.delete(`/playlists/${playlist.id}`)
        ElMessage.success('歌单已删除')

        // 如果当前正看着这个歌单，就跳回首页
        if (currentPlaylist.value?.id === playlist.id) {
            fetchSongs()
        }
        fetchPlaylists() // 刷新侧边栏
    } catch (e) {
        // 取消删除
    }
}



// --- ➕ 添加歌曲到歌单逻辑 (新增) ---
const showAddDialog = ref(false)   // 控制弹窗显示
const songToAdd = ref(null)        // 当前要添加的那首歌

// --- 🖱️ 右键菜单逻辑 (新增) ---
const contextMenu = ref({
  visible: false,
  x: 0,
  y: 0,
  song: null
})

// 1. 打开右键菜单
const openContextMenu = (e, song) => {
  e.preventDefault() // 阻止浏览器默认菜单
  contextMenu.value = {
    visible: true,
    x: e.clientX,
    y: e.clientY,
    song: song
  }
}

// 2. 关闭菜单 (点击页面任何其他地方时触发)
const closeContextMenu = () => {
  contextMenu.value.visible = false
}

// 3. 监听全局点击，关闭菜单
onMounted(() => {
  // ... 原有的 onMounted 内容 ...
  document.addEventListener('click', closeContextMenu)
})

// 别忘了在组件卸载时移除监听，虽然 App.vue 一般不卸载，但这是好习惯
import { onUnmounted } from 'vue' // 记得在顶部引入 onUnmounted
onUnmounted(() => {
  document.removeEventListener('click', closeContextMenu)
})




// 1. 打开选择弹窗
const openAddToPlaylist = (song) => {
  songToAdd.value = song
  showAddDialog.value = true
}

// 2. 执行添加操作
const addToPlaylist = async (playlistId) => {
  try {
    // 调用后端接口: POST /playlists/{pid}/songs/{sid}
    const res = await axios.post(`/playlists/${playlistId}/songs/${songToAdd.value.id}`)

    // 后端返回的 message
    if (res.data.ok) {
        ElMessage.success('已添加到歌单')
        showAddDialog.value = false // 关闭弹窗
    } else {
        ElMessage.warning(res.data.message || '添加失败')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '添加失败')
  }
}



// 3. 点击歌单 (暂时先打印一下，后面做切换逻辑)
const selectPlaylist = async (playlist) => {
  try {
      currentPlaylist.value = playlist // 👈 新增：记录当前在看哪个歌单
     // 获取该歌单下的歌曲
     const res = await axios.get(`/playlists/${playlist.id}/songs`)
     songList.value = res.data
     ElMessage.success(`已切换到歌单: ${playlist.title}`)
  } catch (e) {
     ElMessage.error('获取歌单歌曲失败')
  }
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

const parseLRC = (lrcString) => {
  if (!lrcString) return []
  const lines = lrcString.split('\n')
  const result = []
  const timeReg = /\[(\d{2}):(\d{2})\.(\d{2,3})\]/

  lines.forEach(line => {
    const match = timeReg.exec(line)
    if (match) {
      const min = parseInt(match[1])
      const sec = parseInt(match[2])
      const ms = parseInt(match[3])
      const time = min * 60 + sec + ms / (match[3].length === 3 ? 1000 : 100)
      const text = line.replace(timeReg, '').trim()
      if (text) result.push({ time, text })
    }
  })
  return result
}

// 🔥 4. 修改 playMusic：切歌时加载歌词
const playMusic = (song) => {
  if (currentSong.value.id === song.id) {
    togglePlay()
    return
  }
  currentSong.value = song
  isPlaying.value = true

  // 模拟加载歌词 (真实情况是用 song.lyrics)
  const lrc = song.lyrics || sampleLRC
  parsedLyrics.value = parseLRC(lrc)
  currentLyricIndex.value = -1
}

// 🔥 5. 修改 onTimeUpdate：同步滚动逻辑
const onTimeUpdate = () => {
  if (!isDragging.value && audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime
  }

  // 歌词高亮计算
  if (parsedLyrics.value.length > 0) {
    let activeIndex = -1
    for (let i = 0; i < parsedLyrics.value.length; i++) {
      if (currentTime.value >= parsedLyrics.value[i].time) {
        activeIndex = i
      } else {
        break
      }
    }

    if (activeIndex !== currentLyricIndex.value) {
      currentLyricIndex.value = activeIndex
      scrollToActiveLyric()
    }
  }
}

// 滚动辅助
const scrollToActiveLyric = () => {
  if (lyricsContainer.value && currentLyricIndex.value !== -1) {
    const container = lyricsContainer.value
    // 40是行高，300是容器高度的一半
    container.scrollTo({
      top: currentLyricIndex.value * 40 - 200,
      behavior: 'smooth'
    })
  }
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

/* 刷新按钮样式优化 */
.refresh-btn {
  background: rgb(69, 158, 34) !important; /* 半透明背景 */
  border: 1px solid rgba(19, 221, 52, 0.1) !important; /* 淡淡的边框 */
  color: #ef3e09 !important; /* 图标白色 */
  transition: all 0.3s;
  margin-left: 15px; /* 给左边的搜索框留点距离 */
}

.refresh-btn:hover {
  background: rgba(255, 255, 255, 0.2) !important; /* 悬停稍微变亮 */
  transform: rotate(360deg); /* 🌟 增加一个旋转动画，更有趣 */
}

/* src/App.vue <style> */

/* --- 🎵 底部触发区域优化 --- */
.player-info {
  width: 200px;
  display: flex;
  align-items: center;
  cursor: pointer; /* 变手指 */
  transition: opacity 0.3s;
  position: relative;
}
.player-info:hover {
  opacity: 0.8;
}
.expand-icon {
  margin-left: 10px;
  opacity: 0;
  transition: all 0.3s;
  transform: translateY(5px);
}
.player-info:hover .expand-icon {
  opacity: 1;
  transform: translateY(0);
}


/* --- 🎤 全屏歌词遮罩层样式 --- */
.lyrics-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: calc(100vh - 80px); /* 留出底部播放条的高度 */
  background: #1e1e2e;
  z-index: 900; /* 在播放条下面，但在列表上面 */
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 动态背景 */
.blur-bg {
  position: absolute;
  top: 0; left: 0; width: 100%; height: 100%;
  background-size: cover;
  background-position: center;
  filter: blur(60px) brightness(0.4);
  z-index: -1;
  transition: background-image 0.5s ease;
}

/* 关闭按钮 */
.close-lyrics {
  position: absolute;
  top: 20px;
  left: 30px;
  cursor: pointer;
  z-index: 10;
  padding: 10px;
  border-radius: 50%;
  background: rgba(255,255,255,0.1);
  color: white;
  transition: all 0.3s;
}
.close-lyrics:hover {
  background: rgba(255,255,255,0.2);
  transform: rotate(180deg);
}

/* 布局：左右分栏 */
.lyrics-content-layout {
  display: flex;
  height: 100%;
  padding-top: 60px; /* 避开关闭按钮 */
}

/* 左侧封面区 */
.left-cover {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.big-cover-box {
  width: 350px;
  height: 350px;
  border-radius: 50%;
  overflow: hidden;
  box-shadow: 0 0 30px rgba(0,0,0,0.5);
  border: 8px solid rgba(255,255,255,0.1);
  animation: spin 20s linear infinite; /* 旋转 */
  animation-play-state: paused;
}
.big-cover-box.playing {
  animation-play-state: running;
}
.big-cover-box img {
  width: 100%; height: 100%; object-fit: cover;
}
.placeholder-disc {
  width: 100%; height: 100%;
  background: #333;
  display: flex; align-items: center; justify-content: center;
  font-size: 80px; color: #555;
}
.big-info {
  margin-top: 40px;
  text-align: center;
}
.big-info h2 { font-size: 32px; margin-bottom: 10px; }
.big-info p { font-size: 18px; color: #aaa; }


/* 右侧歌词区 */
.right-lyrics {
  flex: 1;
  overflow-y: auto;
  text-align: center;
  padding: 20px 0;
  mask-image: linear-gradient(to bottom, transparent 0%, black 15%, black 85%, transparent 100%);
  -webkit-mask-image: linear-gradient(to bottom, transparent 0%, black 15%, black 85%, transparent 100%);
  scrollbar-width: none;
}
.right-lyrics::-webkit-scrollbar { display: none; }

.lrc-line {
  color: rgba(255,255,255,0.4);
  font-size: 16px;
  margin: 24px 0;
  transition: all 0.4s ease;
  cursor: default;
}
.lrc-line.active {
  color: #fff;
  font-size: 28px;
  font-weight: bold;
  text-shadow: 0 0 20px rgba(255,255,255,0.6);
}

/* 进出场动画 (Slide Up) */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%); /* 默认藏在屏幕下面 */
}
/* --- 🎵 侧边栏歌单样式 --- */
.playlist-area {
  margin-top: 30px;
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 20px;
}

.playlist-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}
.playlist-header h3 {
  margin: 0;
  font-size: 14px;
  color: rgba(255,255,255,0.6);
}

.playlist-list {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.playlist-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: rgba(255,255,255,0.8);
  font-size: 14px;
}
.playlist-item:hover {
  background: rgba(255,255,255,0.1);
  color: white;
}
.playlist-item .el-icon {
  margin-right: 10px;
  font-size: 16px;
}

/* --- ➕ 收藏按钮与弹窗样式 --- */

/* 1. 收藏按钮位置 (在卡片左上角，或者并在删除按钮旁边) */
.add-btn {
  position: absolute;
  top: 5px;
  right: 40px; /* 放在删除按钮(right:5px)的左边 */
  opacity: 0;
  transition: opacity 0.2s;
  z-index: 10;
}
.song-card:hover .add-btn {
  opacity: 1;
}

/* 2. 弹窗列表样式 */
.playlist-select-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.dialog-item {
  padding: 12px;
  background: rgba(0,0,0,0.05);
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.2s;
  color: #333; /* 弹窗默认是白底黑字，这里用深色文字 */
}
.dialog-item:hover {
  background: #ff9966; /* 悬停变橙色 */
  color: white;
}
.dialog-item .el-icon {
  margin-right: 10px;
}

/* (可选) 强制弹窗变为暗黑风格，如果你想的话 */
.glass-dialog {
  background: #2d2d42 !important;
}
.glass-dialog .el-dialog__title {
  color: white !important;
}

/* 歌单列表项布局优化 */
.playlist-item {
  display: flex;
  justify-content: space-between; /*以此把名字和删除按钮撑开*/
  align-items: center;
  /* ...原有的 padding 等样式保留... */
}

/* 高亮当前选中的歌单 */
.active-pl {
  background: rgba(255, 153, 102, 0.2) !important;
  color: #ff9966 !important;
  border-left: 3px solid #ff9966;
}

.pl-name {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 删除图标默认隐藏 */
.del-pl-btn {
  opacity: 0;
  transition: opacity 0.2s;
  color: #ff4d4f;
  padding: 5px;
}
.del-pl-btn:hover {
  background: rgba(255, 77, 79, 0.2);
  border-radius: 4px;
}

/* 鼠标悬停在整行时，显示删除图标 */
.playlist-item:hover .del-pl-btn {
  opacity: 1;
}

/* --- 🖱️ 右键菜单样式 --- */
.custom-context-menu {
  position: fixed;
  z-index: 9999; /* 必须极高，盖住所有东西 */
  background: rgba(40, 40, 50, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
  padding: 5px 0;
  min-width: 160px;
  animation: fadeIn 0.1s ease-out;
}

.menu-header {
  padding: 8px 15px;
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  border-bottom: 1px solid rgba(255,255,255,0.1);
  margin-bottom: 5px;
  max-width: 180px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.menu-item {
  padding: 10px 15px;
  font-size: 14px;
  color: #eee;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: background 0.2s;
}

.menu-item:hover {
  background: #ff9966; /* 悬停变橙色 */
  color: white;
}

.menu-item .el-icon {
  margin-right: 10px;
  font-size: 16px;
}

.menu-item.delete:hover {
  background: #ff4d4f; /* 删除项悬停变红 */
}

.menu-divider {
  height: 1px;
  background: rgba(255,255,255,0.1);
  margin: 5px 0;
}

@keyframes fadeIn {
  from { opacity: 0; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1); }
}




</style>
