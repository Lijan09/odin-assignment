import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

const DEFAULT_API_TARGET = 'http://127.0.0.1:8000'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  // loadEnv is used with an empty prefix so the variable does NOT need a VITE_
  // prefix. That is deliberate: this value is read here, in the Node process
  // running the dev server, and is never compiled into the browser bundle.
  // Anything named VITE_* would be, so keeping the prefix off makes it clear
  // this is server-side configuration and keeps the client free of any host.
  const env = loadEnv(mode, process.cwd(), '')
  const target = env.API_PROXY_TARGET || DEFAULT_API_TARGET

  return {
    plugins: [react()],
    server: {
      // Requests to /api/* are forwarded to the FastAPI backend during
      // development, so the browser only ever talks to one origin and CORS
      // never comes up. The prefix is stripped, so the backend sees /tasks.
      proxy: {
        '/api': {
          target,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
        },
      },
    },
  }
})
