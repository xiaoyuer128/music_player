import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    // 如果你后端改了端口（比如8001），记得把下面所有的 8000 改成 8001
    proxy: {
      // 1. 歌曲相关
      '/songs': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 2. 静态资源 (MP3)
      '/static': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 3. 上传接口 (部分旧代码可能用到)
      '/upload': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      // 🌟🌟🌟 4. 新增：认证接口 (漏掉的就是这个！) 🌟🌟🌟
      '/auth': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
      '/playlists': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    }
  }
})