import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const frontendDir = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const projectDir = resolve(frontendDir, '..')
const localPython = resolve(projectDir, '.forensic/bin/python')
const venvPython = resolve(projectDir, '.venv/bin/python')
const python = process.env.PYTHON || (existsSync(localPython) ? localPython : existsSync(venvPython) ? venvPython : 'python3')
const children = []
let stopping = false

function stop(code = 0) {
  if (stopping) return
  stopping = true
  for (const child of children) child.kill('SIGTERM')
  setTimeout(() => process.exit(code), 100).unref()
}

async function apiAlreadyRunning() {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/health', { signal: AbortSignal.timeout(1000) })
    return response.ok
  } catch {
    return false
  }
}

function start(command, args, options) {
  const child = spawn(command, args, { stdio: 'inherit', ...options })
  children.push(child)
  child.on('error', (error) => {
    console.error(`Could not start ${command}: ${error.message}`)
    stop(1)
  })
  child.on('exit', (code) => {
    if (!stopping) stop(code || 0)
  })
  return child
}

process.on('SIGINT', () => stop())
process.on('SIGTERM', () => stop())

if (!await apiAlreadyRunning()) {
  console.log(`Starting the local API with ${python}…`)
  start(python, ['-m', 'uvicorn', 'api:app', '--host', '127.0.0.1', '--port', '8000'], { cwd: projectDir })
} else {
  console.log('Using the API already running at http://127.0.0.1:8000')
}

start(process.execPath, [resolve(frontendDir, 'node_modules/vite/bin/vite.js'), '--host', '127.0.0.1'], { cwd: frontendDir })
