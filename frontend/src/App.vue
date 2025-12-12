<template src="./App.html"></template>

<script setup>


import { ref, onMounted,computed } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox} from 'element-plus'
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
      // ... 注册逻辑不变 ...
      await axios.post('/auth/register', formData)
      ElMessage.success('注册成功')
      isRegisterMode.value = false
    } else {
      // 👇👇👇 修改这里：登录成功的分支 👇👇👇
      const res = await axios.post('/auth/token', formData)
      localStorage.setItem('token', res.data.access_token)
      localStorage.setItem('username', authForm.value.username)

      // 1. 设置登录状态
      isLoggedIn.value = true
      ElMessage.success('登录成功')

      // 2. 获取所有歌曲
      fetchSongs()

      // ✨ 3. 补上这一行：登录后立马获取歌单！✨
      fetchPlaylists()
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    isLoading.value = false
  }
}

// --- 退出登录逻辑 ---
const logout = () => {
  // 1. 清除本地存储
  localStorage.removeItem('token')
  localStorage.removeItem('username')

  // 2. 重置播放器状态 (防止退出后还在响)
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }
  isPlaying.value = false
  currentSong.value = {}
  currentTime.value = 0
  duration.value = 0

  // 3. 重置界面状态
  showLyricsPage.value = false // 关掉歌词页
  isLoggedIn.value = false     // 切换回登录界面

  // 4. 清空表单和数据
  authForm.value = { username: '', password: '' }
  songList.value = []
  myPlaylists.value = []

  ElMessage.success('已退出登录')
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

<style src="./App.css"></style>
