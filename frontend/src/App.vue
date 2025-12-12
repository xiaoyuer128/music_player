<template src="./App.html"></template>

<script setup>

import { ref, onMounted, computed, watch, onUnmounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderAdd, Headset, User, UploadFilled, VideoPlay, VideoPause, Delete,
  Refresh, Lock, ArrowLeft, ArrowRight, Sort, Connection, Search,
  Microphone, ArrowDown, Plus, List, Edit, ArrowUp // 👈 补上这个！
} from '@element-plus/icons-vue'

// --- 基础状态 ---
const isLoggedIn = ref(false)
const isRegisterMode = ref(false)
const isLoading = ref(false)
const authForm = ref({ username: '', password: '' })
const isUploading = ref(false)
const songList = ref([])
const currentSong = ref({})

// --- 播放状态 ---
const isPlaying = ref(false)
const audioPlayer = ref(null)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(1.0)
const isDragging = ref(false)

// --- 搜索状态 ---
const isSearchActive = ref(false)
const searchQuery = ref('')

// --- 播放模式 ---
const playMode = ref('sequence')

// --- 歌词状态 ---
const showLyricsPage = ref(false)
const parsedLyrics = ref([])
const currentLyricIndex = ref(-1)
const lyricsContainer = ref(null)

// 🛠️ 手写一个防抖函数 (解决 lodash 报错问题)
const myDebounce = (fn, delay) => {
  let timer = null
  return function(...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 🎧 监听搜索框 (使用我们手写的 myDebounce)
watch(searchQuery, myDebounce((newVal) => {
  fetchSongs(newVal) // 调用后端搜索接口
}, 300))

// ... (后面的 const sampleLRC = ... 以及其他代码保持不变)

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
// const filteredSongList = computed(() => {
//   if (!searchQuery.value) return songList.value
//
//   const query = searchQuery.value.toLowerCase().trim()
//   return songList.value.filter(song => {
//     // 同时也搜索歌手名，体验更好
//     return song.title.toLowerCase().includes(query) ||
//            song.artist.toLowerCase().includes(query)
//   })
// })

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


// --- 🎵 音频可视化逻辑 ---
const visualizerCanvas = ref(null)
let audioContext = null
let analyser = null
let dataArray = null
let animationId = null

// 初始化可视化器 (注意：必须在用户交互后才能初始化 AudioContext，否则浏览器会阻止)
const initVisualizer = () => {
  if (audioContext) return // 防止重复初始化
  if (!audioPlayer.value) return

  // 1. 创建上下文
  audioContext = new (window.AudioContext || window.webkitAudioContext)()

  // 2. 创建分析器
  analyser = audioContext.createAnalyser()
  analyser.fftSize = 512 // 决定了柱子的数量 (512 / 2 = 256根)

  // 3. 连接音频源 (这里有个坑：MediaElementSource 只能连一次，所以要 try-catch 或者由播放触发)
  try {
      const source = audioContext.createMediaElementSource(audioPlayer.value)
      source.connect(analyser)
      analyser.connect(audioContext.destination) // 连回扬声器，不然没声音
  } catch(e) {
      // 如果已经连过了，就忽略错误
  }

  // 4. 准备数据容器
  const bufferLength = analyser.frequencyBinCount
  dataArray = new Uint8Array(bufferLength)

  // 5. 开始绘制
  drawVisualizer()
}

// 绘制循环函数
const drawVisualizer = () => {
  animationId = requestAnimationFrame(drawVisualizer)

  if (!showLyricsPage.value || !visualizerCanvas.value) return

  const canvas = visualizerCanvas.value
  const ctx = canvas.getContext('2d')

  // 1. 适配屏幕宽度，但高度固定为 120 (与 CSS 保持一致)
  canvas.width = window.innerWidth
  canvas.height = 120

  analyser.getByteFrequencyData(dataArray)

  ctx.clearRect(0, 0, canvas.width, canvas.height)

  // 2. 调整柱子宽度和间距
  const barWidth = (canvas.width / dataArray.length) * 2.5
  let barHeight
  let x = 0

  for (let i = 0; i < dataArray.length; i++) {
    // 3. 重新计算高度比例，避免画出界
    // dataArray[i] 最大是 255，我们把它缩放到 canvas.height 以内
    // (dataArray[i] / 255) * canvas.height * 0.8 (乘以0.8是为了留点余地)
    barHeight = (dataArray[i] / 255) * canvas.height * 0.9

    // 渐变色：从底部(热烈)到顶部(透明)
    const gradient = ctx.createLinearGradient(0, canvas.height, 0, canvas.height - barHeight)
    gradient.addColorStop(0, '#ff9966') // 底部颜色
    gradient.addColorStop(1, 'rgba(255, 94, 98, 0.5)') // 顶部颜色半透明

    ctx.fillStyle = gradient

    // 绘制 (让柱子沉底)
    ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight)

    x += barWidth + 1
  }
}

// 🔥 新增：根据当前模式返回不同的颜色
const getModeColor = () => {
    if (playMode.value === 'loop') return '#E6A23C'   // 橙色 (Element Warning色)
    if (playMode.value === 'random') return '#67C23A' // 绿色 (Element Success色)
    return '#FFFFFF' // 白色 (默认)
}

// ... fetchSongs 等代码 ...
// --- 歌曲业务逻辑 ---
// 修改前的 fetchSongs 没有任何参数

// 修改 fetchSongs 支持接收搜索参数
const fetchSongs = async (query = '') => {
  currentPlaylist.value = null
  try {
    // 这里的 params: { q: query } 会把请求变成 /songs/?q=xxx
    // 如果 query 是 Event 对象(某些情况下会发生)，要处理一下，或者确保调用时传的是字符串
    const searchWord = (typeof query === 'string') ? query : ''

    const res = await axios.get('/songs/', { params: { q: searchWord } })
    songList.value = res.data
  } catch (error) {
    console.error(error)
  }
}

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

// --- ✏️ 编辑歌曲逻辑 (新增) ---
const showEditDialog = ref(false)
const editForm = ref({ id: null, title: '', artist: '', coverFile: null })

// 1. 打开编辑窗口 (从右键菜单触发)
const openEditDialog = (song) => {
  editForm.value = {
    id: song.id,
    title: song.title,
    artist: song.artist,
    coverFile: null // 重置文件
  }
  showEditDialog.value = true
}

// 2. 监听文件选择 (封面图)
const handleEditFileChange = (uploadFile) => {
  editForm.value.coverFile = uploadFile.raw
}

// 3. 提交修改
const submitEdit = async () => {
  try {
    const formData = new FormData()
    if (editForm.value.title) formData.append('title', editForm.value.title)
    if (editForm.value.artist) formData.append('artist', editForm.value.artist)
    if (editForm.value.coverFile) formData.append('cover', editForm.value.coverFile)

    await axios.patch(`/songs/${editForm.value.id}`, formData)

    ElMessage.success('修改成功')
    showEditDialog.value = false
    fetchSongs() // 刷新列表看效果

    // 如果正在放这首歌，顺便更新一下播放器显示的文字
    if (currentSong.value.id === editForm.value.id) {
        currentSong.value.title = editForm.value.title
        currentSong.value.artist = editForm.value.artist
        // 封面图因为有缓存，可能不会立马变，暂时忽略
    }
  } catch (e) {
    ElMessage.error('修改失败')
  }
}



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
    showLyricsPage.value = !showLyricsPage.value
    return
  }
  currentSong.value = song
  isPlaying.value = true
  showLyricsPage.value = true

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

// --- ⌨️ 键盘快捷键逻辑 ---
const handleKeydown = (e) => {
  // 1. 如果焦点在输入框里，不要触发快捷键
  if (['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) return

  switch (e.code) {
    case 'Space':
      e.preventDefault() // 防止空格导致页面滚动
      togglePlay()
      break
    case 'ArrowRight':
      // 快进 5秒 (如果有 Ctrl 则切下一首)
      if (e.ctrlKey) {
          nextSong(true)
      } else {
          if (audioPlayer.value) audioPlayer.value.currentTime += 5
          ElMessage.info('快进 5s')
      }
      break
    case 'ArrowLeft':
      // 快退 5秒
      if (e.ctrlKey) {
          prevSong()
      } else {
          if (audioPlayer.value) audioPlayer.value.currentTime -= 5
          ElMessage.info('快退 5s')
      }
      break
    case 'ArrowUp':
      e.preventDefault()
      // 音量 + 10%
      if (volume.value < 1) volume.value = Math.min(1, volume.value + 0.1)
      setVolume(volume.value)
      break
    case 'ArrowDown':
      e.preventDefault()
      // 音量 - 10%
      if (volume.value > 0) volume.value = Math.max(0, volume.value - 0.1)
      setVolume(volume.value)
      break
  }
}

// 在 onMounted 里注册
onMounted(() => {
  // ... 原有代码 ...
  document.addEventListener('keydown', handleKeydown)
})

// 在 onUnmounted 里卸载
onUnmounted(() => {
  // ... 原有代码 ...
  document.removeEventListener('keydown', handleKeydown)
})






</script>

<style src="./App.css"></style>
