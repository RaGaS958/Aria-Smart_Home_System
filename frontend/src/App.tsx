/**
 * ARIA — Advanced Responsive Intelligence Assistant
 * Enhanced Frontend v3.0 | Realistic room · Holographic face · Smart home controls
 */

import { useState, useEffect, useRef, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import * as THREE from 'three'
import {
  Send, X, Moon, Sun, Cloud, CloudRain, Zap, Wind,
  Star, Volume2, VolumeX, Home, Info, Power, Cpu,
  Loader, Lightbulb, Wind as FanIcon, Tv, Music2,
  Thermometer, Blinds, ChevronUp, ChevronDown,
  WifiOff, Wifi, Mic, MicOff,
} from 'lucide-react'

// ─────────────────────────────────────────────────────────────────────────────
// CONFIG
// ─────────────────────────────────────────────────────────────────────────────
/* eslint-disable @typescript-eslint/no-explicit-any */
const _env         = (import.meta as any).env as Record<string, string | undefined>
const API          = _env.VITE_API_URL          || 'http://localhost:8000'
const WS_URL       = _env.VITE_WS_URL           || 'ws://localhost:8000/ws/agent'
const DEFAULT_CITY = _env.VITE_DEFAULT_CITY     || 'London'

// ─────────────────────────────────────────────────────────────────────────────
// SMART HOME STATE
// ─────────────────────────────────────────────────────────────────────────────
interface HomeState {
  lampOn: boolean
  lampBrightness: number   // 0–100
  curtainsOpen: boolean
  fanOn: boolean
  fanSpeed: number         // 1–3
  tvOn: boolean
  musicOn: boolean
  thermostat: number       // celsius
}

const DEFAULT_HOME: HomeState = {
  lampOn: true, lampBrightness: 100,
  curtainsOpen: true,
  fanOn: false, fanSpeed: 2,
  tvOn: false, musicOn: false,
  thermostat: 22,
}

// Parse ARIA responses to infer home state changes
function inferHomeState(msg: string, prev: HomeState): HomeState {
  const t = msg.toLowerCase()
  const next = { ...prev }
  if (/lights?.*(on|turned on|switched on)/i.test(t))  next.lampOn = true
  if (/lights?.*(off|turned off)/i.test(t))            next.lampOn = false
  if (/brightness.*?(\d+)/i.test(t)) {
    const m = t.match(/brightness.*?(\d+)/i); if (m) next.lampBrightness = Math.min(100, +m[1])
  }
  if (/curtains?.*(open|opened)/i.test(t))             next.curtainsOpen = true
  if (/curtains?.*(clos|pulled)/i.test(t))             next.curtainsOpen = false
  if (/fan.*(on|started|running)/i.test(t))            next.fanOn = true
  if (/fan.*(off|stopped)/i.test(t))                   next.fanOn = false
  if (/speed.*?(\d)/i.test(t)) { const m = t.match(/speed.*?(\d)/i); if (m) next.fanSpeed = Math.min(3, +m[1]) }
  if (/tv.*(on|turned on)/i.test(t))                   next.tvOn = true
  if (/tv.*(off|turned off)/i.test(t))                 next.tvOn = false
  if (/music.*(playing|started|on)/i.test(t) || /now playing/i.test(t) || /playing.*music/i.test(t)) next.musicOn = true
  if (/music.*(stopped|off|paused)/i.test(t))          next.musicOn = false
  if (/thermostat.*?(\d+)/i.test(t)) { const m = t.match(/(\d+)\s*°?c/i); if (m) next.thermostat = +m[1] }
  return next
}

// ─────────────────────────────────────────────────────────────────────────────
// PIXEL FACE DATA  (20×14 grid)
// ─────────────────────────────────────────────────────────────────────────────
const parseFace = (s: string): boolean[][] =>
  s.trim().split('\n').map(l => l.trim().padEnd(20, '.').split('').map(c => c === 'X'))

const FACES: Record<string, boolean[][]> = {
  idle: parseFace(`
....................
....................
.....XXXX..XXXX.....
.....XXXX..XXXX.....
.....X..X..X..X.....
.....XXXX..XXXX.....
.....XXXX..XXXX.....
....................
....................
.....X........X.....
.....XX......XX.....
......XXXXXXXX......
....................
....................
....................`),
happy: parseFace(`
....................
....................
....................
...XXXXXX..XXXXXXX..
...XXXXXXXXXXXXXXX..
.....XXXXX..XXXX....
......XXXX..XXXX....
....................
.....X..........X...
......XXXXXXXXXX....
........XXXXXX......
....................
....................
....................`),
  thinking: parseFace(`
....................
.................X..
.....XX....XX...X.X.
.....X.X...X.X...X..
......X.....X......
...................
....................
....................
...........XXX......
......XXXXXXXX......
.....XXXXXXX........
....XX..............
....................
....................`),
  speaking: parseFace(`
....................
....................
....XXXX..XXXX......
....X..X..X..X......
....X..X..X..X......
....XXXX..XXXX......
....................
..............XXX...
..... XXXX....XXXXX..
.... X....X..XXXXXXX.
.... X....X.X.XXXXX..
.... X....X..........
..... XXXX...........
....................`),
  surprised: parseFace(`
....................
... ..XX.....XX......
... .X..X...X..X.....
... ..XX.....XX......
.....................
........XXXX.........
.......X....X........
......X......X.......
......X......X.......
......X......X.......
......X......X.......
......X......X.......
.......X....X........
........XXXX.........`),
  sad: parseFace(`
.....................
.....................
.....................
... XXX.....XXX......
....XXX...  XXX......
... XXX.....XXX......
.....................
.....................
.....................
......XXXXXXXX.......
.....X........X......
....X..........X.....
.....................
....................`),
  excited: parseFace(`
....................
...X.X.X.... X.X.X..
....XXX.....  XXX....
..XX.X.XX.  XX.X.XX..
....XXX.....  XXX....
...X.X.X.... X.X.X...
....................
....................
....................
..XXXXXXXXXXXXXXXXX.
...XXXXXXXXXXXXXXX..
....XXXXXXXXXXXXX...
....................
....................
....................
....................`),
  sleeping: parseFace(`
.................XX....
..................X....
..................XX...
................XX.....
...XXX.....XXX...X.....
....X.......X....XX....
.......................
................XX.....
............XX...X.....
........X....X...XX....
.......X.X...XX........
........X..............
......................
....................`),
}

const EMOTION_CFG: Record<string, { color: string; glow: string; label: string; accent: string }> = {
  idle:      { color: '#00ffaa', glow: '0,255,170',    label: 'STANDBY',  accent: '#00cc88' },
  happy:     { color: '#ffd97d', glow: '255,217,125',  label: 'HAPPY',    accent: '#f0c050' },
  thinking:  { color: '#63c3ff', glow: '99,195,255',   label: 'THINKING', accent: '#3a9fdd' },
  speaking:  { color: '#c4b5fd', glow: '196,181,253',  label: 'SPEAKING', accent: '#a78bfa' },
  surprised: { color: '#fb923c', glow: '251,146,60',   label: 'SURPRISE', accent: '#e07020' },
  sad:       { color: '#93c5fd', glow: '147,197,253',  label: 'EMPATHIC', accent: '#60a5fa' },
  excited:   { color: '#f0abfc', glow: '240,171,252',  label: 'EXCITED',  accent: '#d070e0' },
  sleeping:  { color: '#6b7280', glow: '107,114,128',  label: 'RESTING',  accent: '#4b5563' },
}
type EmotionKey = keyof typeof EMOTION_CFG

// ─────────────────────────────────────────────────────────────────────────────
// TYPES
// ─────────────────────────────────────────────────────────────────────────────
interface WeatherData { temp: number; description: string; condition: string; humidity: number; wind_speed: number; city: string }
interface NewsItem    { title: string; url: string; snippet?: string }
interface Message     { role: 'user' | 'assistant'; content: string; emotion?: EmotionKey; ts: number }

// ─────────────────────────────────────────────────────────────────────────────
// HOOK: useAgent
// ─────────────────────────────────────────────────────────────────────────────
function useAgent(onHomeUpdate: (msg: string) => void, userCity: string = "") {
  const wsRef      = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const [emotion,   setEmotion]   = useState<EmotionKey>('idle')
  const [speaking,  setSpeaking]  = useState(false)
  const [messages,  setMessages]  = useState<Message[]>([])
  const [news,      setNews]      = useState<NewsItem[]>([])
  const [loading,   setLoading]   = useState(false)
  const historyRef = useRef<{role:string;content:string}[]>([])

  const addMsg = useCallback((m: Message) => {
    setMessages(prev => [...prev.slice(-30), m])
    if (m.role === 'assistant') {
      historyRef.current = [...historyRef.current.slice(-10),
        { role: 'assistant', content: m.content }]
      onHomeUpdate(m.content)
    } else {
      historyRef.current = [...historyRef.current.slice(-10),
        { role: 'user', content: m.content }]
    }
  }, [onHomeUpdate])

  const connect = useCallback(() => {
    try {
      const s = new WebSocket(WS_URL)
      s.onopen  = () => {
        setConnected(true)
        // Send city immediately so backend knows location for all subsequent messages
        if (userCity) {
          s.send(JSON.stringify({ type: 'set_city', city: userCity }))
        }
      }
      s.onclose = () => { setConnected(false); setTimeout(connect, 3000) }
      s.onerror = () => s.close()
      s.onmessage = e => {
        const d = JSON.parse(e.data)
        if (d.type === 'news_update')  setNews(d.data || [])
        else if (d.type === 'emotion') setEmotion(d.emotion)
        else if (d.type === 'response') {
          setEmotion(d.emotion)
          addMsg({ role:'assistant', content:d.message, emotion:d.emotion, ts:Date.now() })
          setSpeaking(true)
          setTimeout(() => { setSpeaking(false); setEmotion('idle') },
            Math.min(d.message.length * 55, 9000))
          setLoading(false)
        }
      }
      wsRef.current = s
    } catch { setConnected(false) }
  }, [addMsg])

  useEffect(() => { connect(); return () => wsRef.current?.close() }, [connect])

  // Re-send city whenever it resolves (geolocation comes in async after WS connects)
  useEffect(() => {
    if (userCity && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'set_city', city: userCity }))
    }
  }, [userCity])

  const sendMessage = useCallback(async (text: string) => {
    if (!text.trim()) return
    addMsg({ role:'user', content:text, ts:Date.now() })
    setLoading(true); setEmotion('thinking')
    if (connected && wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type:'chat', message:text, city:userCity }))
    } else {
      try {
        // REST fallback when WebSocket is unavailable
        const res  = await fetch(`${API}/api/chat`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({ message:text, history:historyRef.current.slice(-6), city:userCity })
        })
        const data = await res.json()
        setEmotion(data.emotion)
        addMsg({ role:'assistant', content:data.response, emotion:data.emotion, ts:Date.now() })
        setSpeaking(true)
        setTimeout(() => { setSpeaking(false); setEmotion('idle') }, 6000)
      } catch {
        addMsg({ role:'assistant', content:"Can't reach my backend. Check if the server is running.", emotion:'sad', ts:Date.now() })
        setEmotion('sad')
      }
      setLoading(false)
    }
  }, [connected, addMsg])

  return { connected, emotion, speaking, messages, news, loading, sendMessage }
}

// ─────────────────────────────────────────────────────────────────────────────
// HOOK: useWeather
// ─────────────────────────────────────────────────────────────────────────────
function useWeather(city: string) {
  const [weather, setWeather] = useState<WeatherData | null>(null)
  useEffect(() => {
    const load = async () => {
      try { setWeather(await (await fetch(`${API}/api/weather/${encodeURIComponent(city)}`)).json()) } catch {}
    }
    load()
    const id = setInterval(load, 600_000)
    return () => clearInterval(id)
  }, [city])
  return weather
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: HoloFace — refined ARIA face display
// ─────────────────────────────────────────────────────────────────────────────
function HoloFace({ emotion = 'idle' as EmotionKey, speaking = false, size = 200 }) {
  const [blink,     setBlink]     = useState(false)
  const [mouthAmp,  setMouthAmp]  = useState(0.5)
  const [scanLine,  setScanLine]  = useState(0)
  const cfg  = EMOTION_CFG[emotion] || EMOTION_CFG.idle
  const face = FACES[emotion]        || FACES.idle
  const CW   = size / 20
  const CH   = (size * 14/20) / 14

  // Blink
  useEffect(() => {
    const rate = emotion === 'thinking' ? 600 : emotion === 'sleeping' ? 10000 : 3200
    const id = setInterval(() => { setBlink(true); setTimeout(() => setBlink(false), 130) }, rate)
    return () => clearInterval(id)
  }, [emotion])

  // Mouth animate when speaking
  useEffect(() => {
    if (!speaking) { setMouthAmp(0.5); return }
    const id = setInterval(() => setMouthAmp(0.2 + Math.random() * 0.8), 90)
    return () => clearInterval(id)
  }, [speaking])

  // Scan line
  useEffect(() => {
    const id = setInterval(() => setScanLine(v => (v + 1) % (size * 14/20)), 14)
    return () => clearInterval(id)
  }, [size])

  const faceH = size * 14/20

  return (
    <div style={{ position: 'relative', width: size, height: faceH + 40 }}>
      {/* Corner brackets */}
      {[
        { top: 0,       left: 0,      borderTop: 2, borderLeft: 2 },
        { top: 0,       right: 0,     borderTop: 2, borderRight: 2 },
        { bottom: 40,   left: 0,      borderBottom: 2, borderLeft: 2 },
        { bottom: 40,   right: 0,     borderBottom: 2, borderRight: 2 },
      ].map((s, i) => (
        <div key={i} style={{
          position: 'absolute', width: 16, height: 16,
          ...Object.fromEntries(Object.entries(s).map(([k,v]) =>
            [k, typeof v === 'number' ? v : v]
          )),
          borderColor: cfg.color, borderStyle: 'solid',
          borderTopWidth: 0, borderRightWidth: 0, borderBottomWidth: 0, borderLeftWidth: 0,
          ...s,
          opacity: 0.7,
        }}/>
      ))}

      {/* Outer glow ring */}
      <div style={{
        position: 'absolute', inset: -6, top: -6, bottom: 34,
        borderRadius: 6,
        boxShadow: `0 0 12px rgba(${cfg.glow},0.25), inset 0 0 20px rgba(${cfg.glow},0.05)`,
        border: `1px solid rgba(${cfg.glow},0.2)`,
        pointerEvents: 'none',
      }}/>

      {/* Face grid */}
      <svg width={size} height={faceH} style={{
        filter: `drop-shadow(0 0 5px ${cfg.color}) drop-shadow(0 0 16px rgba(${cfg.glow},0.5))`,
      }}>
        {/* Grid background dots */}
        {Array.from({ length: 14 }, (_, y) =>
          Array.from({ length: 20 }, (_, x) => (
            <rect key={`g${x}${y}`}
              x={x*CW+CW*0.3} y={y*CH+CH*0.3}
              width={CW*0.15} height={CH*0.15}
              rx={1} fill={`rgba(${cfg.glow},0.08)`}
            />
          ))
        )}

        {/* Lit pixels */}
        {face.map((row, y) =>
          row.map((lit, x) => {
            if (!lit) return null
            const isEyeRow = y >= 2 && y <= 6
            const isMouthRow = y >= 8 && y <= 11
            let sy = 1
            if (blink && isEyeRow) {
              if (y === 4) sy = 0.05
              else if (y === 3 || y === 5) sy = 0.25
            }
            const opacity = isMouthRow && speaking
              ? 0.4 + mouthAmp * 0.6
              : 1

            return (
              <rect key={`${x}-${y}`}
                x={x*CW + 0.8}
                y={y*CH + (CH*(1-sy)/2) + 0.5}
                width={CW - 1.6}
                height={Math.max((CH - 1)*sy, 0.5)}
                rx={Math.max(2, CW * 0.18)}
                fill={cfg.color}
                opacity={opacity}
              />
            )
          })
        )}

        {/* Scan line */}
        <rect x={0} y={scanLine} width={size} height={2}
          fill={`rgba(${cfg.glow},0.15)`}/>

        {/* Scanlines overlay */}
        {Array.from({ length: Math.ceil(faceH / 4) }, (_, i) => (
          <rect key={`sl${i}`} x={0} y={i*4} width={size} height={1}
            fill="rgba(0,0,0,0.07)"/>
        ))}
      </svg>

      {/* Emotion label */}
      <div style={{
        textAlign: 'center', marginTop: 8,
        fontFamily: '"Courier New", monospace', fontSize: 11,
        color: cfg.color, letterSpacing: 4, opacity: 0.85,
      }}>
        {speaking
          ? Array.from({ length: 3 }, (_, i) => (
              <motion.span key={i}
                animate={{ opacity: [0.2, 1, 0.2] }}
                transition={{ duration: 0.6, delay: i*0.2, repeat: Infinity }}>
                ◈
              </motion.span>
            ))
          : cfg.label
        }
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: ThreeRoom — full PBR scene with smart home state
// ─────────────────────────────────────────────────────────────────────────────
function ThreeRoom({
  emotion, weather, homeState
}: {
  emotion: EmotionKey
  weather: WeatherData | null
  homeState: HomeState
}) {
  const mountRef      = useRef<HTMLDivElement>(null)
  const rendererRef   = useRef<THREE.WebGLRenderer | null>(null)
  const frameRef      = useRef<number>(0)
  const clockRef      = useRef(new THREE.Clock())

  // Dynamic scene refs
  const lampLightRef      = useRef<THREE.PointLight | null>(null)
  const lampSphereRef     = useRef<THREE.Mesh | null>(null)
  const ariaOrbRef        = useRef<THREE.Mesh | null>(null)
  const ariaGlowRef       = useRef<THREE.PointLight | null>(null)
  const fanBladesRef      = useRef<THREE.Group | null>(null)
  const tvScreenRef       = useRef<THREE.Mesh | null>(null)
  const tvLightRef        = useRef<THREE.PointLight | null>(null)
  const windowLightRef    = useRef<THREE.PointLight | null>(null)
  const curtainLeftRef    = useRef<THREE.Mesh | null>(null)
  const curtainRightRef   = useRef<THREE.Mesh | null>(null)
  const curtainLLRef      = useRef<THREE.Mesh | null>(null)  // lining panels
  const curtainRLRef      = useRef<THREE.Mesh | null>(null)
  const musicParticlesRef  = useRef<THREE.Points | null>(null)
  const musicSpriteRefs    = useRef<THREE.Mesh[]>([])
  const stereoLightRef     = useRef<THREE.PointLight | null>(null)
  const tableFanRef        = useRef<THREE.Group | null>(null)
  const tvScanRef          = useRef<THREE.Mesh | null>(null)
  const ambientRef         = useRef<THREE.AmbientLight | null>(null)
  const homeRef           = useRef(homeState)
  const emotionRef        = useRef(emotion)

  // Mouse-orbit state (stored in refs to avoid re-render)
  const mouseRef = useRef({
    // Orbit
    isDown: false,
    button: 0,               // 0=left(orbit) 1=middle 2=right(pan)
    lastX: 0, lastY: 0,
    yaw: 0, pitch: 0,
    yawTarget: 0, pitchTarget: 0,
    // Zoom
    radius: 6.8,             // current orbit radius
    radiusTarget: 6.8,       // lerp target
    // Pan (look-at offset)
    panX: 0.4, panY: 0.7,   // current lookAt X/Y
    panXTarget: 0.4, panYTarget: 0.7,
    // Touch pinch
    lastPinchDist: 0,
    isPinching: false,
  })

  useEffect(() => { homeRef.current = homeState }, [homeState])
  useEffect(() => { emotionRef.current = emotion }, [emotion])

  useEffect(() => {
    if (!mountRef.current) return
    const W = mountRef.current.clientWidth
    const H = mountRef.current.clientHeight

    // ── Renderer ──────────────────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false })
    renderer.setSize(W, H)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 0.95
    renderer.setClearColor(0xf2e0c0, 1)
    mountRef.current.appendChild(renderer.domElement)
    rendererRef.current = renderer

    // ── Scene ─────────────────────────────────────────────────────────────
    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0xf2e0c0)
    scene.fog = new THREE.FogExp2(0xf2e0c0, 0.028)

    // ── Camera ────────────────────────────────────────────────────────────
    const camera = new THREE.PerspectiveCamera(62, W/H, 0.1, 50)
    camera.position.set(0, 1.7, 6.8)
    camera.lookAt(0.4, 0.7, -0.5)

    // ── MATERIALS (PBR) ───────────────────────────────────────────────────
    const M = (color: number, roughness = 0.85, metalness = 0) =>
      new THREE.MeshStandardMaterial({ color, roughness, metalness })
    const MS = (color: number, roughness = 0.3, metalness = 0.7) =>
      new THREE.MeshStandardMaterial({ color, roughness, metalness })

    const wallMat      = M(0xf4e8d0)         // warm cream walls
    const accentMat    = M(0xebd9b8)         // slightly darker accent
    const floorMat     = M(0xb8824a, 0.9)    // warm oak floor
    const ceilMat      = M(0xfaf5e8)         // near-white ceiling
    const woodMat      = M(0xa06830, 0.9)    // desk/furniture wood
    const darkWoodMat  = M(0x6b4420, 0.95)   // dark walnut
    const sofaMat      = M(0xd8c8a8, 0.95)   // linen
    const sofaDarkMat  = M(0xc0aa88, 0.95)   // linen dark
    const cushRust     = M(0x9a5535, 0.9)    // rust cushion
    const cushSage     = M(0x527a50, 0.9)    // sage cushion
    const potMat       = M(0xe8dcc8, 0.7)    // ceramic
    const stemMat      = M(0x3a5a25, 0.95)   // stem green
    const leafMat      = new THREE.MeshStandardMaterial({ color: 0x4a7f33, roughness: 0.85, side: THREE.DoubleSide })
    const leafDarkMat  = new THREE.MeshStandardMaterial({ color: 0x2e5a1e, roughness: 0.85, side: THREE.DoubleSide })
    const rugMat       = M(0xc04a30, 0.98)   // terracotta rug
    const rugBorderMat = M(0x8a2a18, 0.98)
    const brassMat     = MS(0xd4a840, 0.3, 0.8) // brass metal
    const steelMat     = MS(0x909090, 0.2, 0.9)
    const shadeMat     = new THREE.MeshStandardMaterial({ color: 0xffe8b0, roughness: 0.7, transparent: true, opacity: 0.88, side: THREE.DoubleSide, emissive: 0x442200, emissiveIntensity: 0 })
    const glassMat     = new THREE.MeshStandardMaterial({ color: 0xc8e8ff, roughness: 0, metalness: 0.1, transparent: true, opacity: 0.28 })
    const frameMat     = M(0xf8f4e8, 0.6)   // window frame white
    const curtainMat   = new THREE.MeshStandardMaterial({ color: 0xd4c8a8, roughness: 0.95, side: THREE.DoubleSide })
    const bookMats     = [M(0xc0392b),M(0x27ae60),M(0x2980b9),M(0xe67e22),M(0x8e44ad),M(0x1abc9c)]
    const tvMat        = M(0x151515, 0.1, 0.9)

    // ── LIGHTS ───────────────────────────────────────────────────────────
    const ambient = new THREE.AmbientLight(0xfff8e8, 0.7)
    scene.add(ambient)
    ambientRef.current = ambient

    // Window sunlight
    const winLight = new THREE.DirectionalLight(0xffffff, 25)
    winLight.position.set(-8, 8, 2)
    winLight.castShadow = true
    winLight.shadow.mapSize.set(1024, 1024)
    winLight.shadow.camera.near = 0.1
    winLight.shadow.camera.far  = 30
    winLight.shadow.camera.left = winLight.shadow.camera.bottom = -8
    winLight.shadow.camera.right = winLight.shadow.camera.top  =  8
    winLight.shadow.bias = -0.001
    scene.add(winLight)
    windowLightRef.current = winLight as any  // reuse ref slot

    // Ceiling fill
    const ceilLight = new THREE.DirectionalLight(0xffeedd, 0.6)
    ceilLight.position.set(0, 6, 0)
    scene.add(ceilLight)

    // Floor lamp (warm amber)
    const lampLight = new THREE.PointLight(0xffcc70, 200, 200)
    lampLight.position.set(-2.8, 1.85, 0.8)
    lampLight.castShadow = true
    lampLight.shadow.mapSize.set(512, 512)
    scene.add(lampLight)
    lampLightRef.current = lampLight

    // ARIA glow
    const ariaGlow = new THREE.PointLight(0x00aaaa, 20, 30)
    ariaGlow.position.set(2.0, 0.55, 0.9)
    scene.add(ariaGlow)
    ariaGlowRef.current = ariaGlow

    // TV backlight
    const tvLight = new THREE.PointLight(0x4488ff, 30, 3)
    tvLight.position.set(3.1, 1.9, -3.8)
    scene.add(tvLight)
    tvLightRef.current = tvLight

    // ── FLOOR ─────────────────────────────────────────────────────────────
    const floor = new THREE.Mesh(new THREE.BoxGeometry(14, 0.1, 14), floorMat)
    floor.position.set(0, -0.05, 0)
    floor.receiveShadow = true
    scene.add(floor)
    // Plank lines
    for (let i = -20; i <= 20; i++) {
      const p = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.11, 14), darkWoodMat)
      p.position.set(i * 0.95, -0.05, 0)
      scene.add(p)
    }

    // Rug
    const rug = new THREE.Mesh(new THREE.BoxGeometry(3.4, 0.018, 2.2), rugMat)
    rug.position.set(-0.4, 0.009, 1.8)
    rug.receiveShadow = true
    scene.add(rug)
    const rugB = new THREE.Mesh(new THREE.BoxGeometry(3.2, 0.022, 2.0), rugBorderMat)
    rugB.position.set(-0.4, 0.011, 1.8)
    scene.add(rugB)
    const rugI = new THREE.Mesh(new THREE.BoxGeometry(2.9, 0.026, 1.7), rugMat)
    rugI.position.set(-0.4, 0.013, 1.8)
    scene.add(rugI)

    // ── WALLS ─────────────────────────────────────────────────────────────
    const backWall = new THREE.Mesh(new THREE.BoxGeometry(14, 7, 0.15), wallMat)
    backWall.position.set(0, 3.5, -4.5)
    backWall.receiveShadow = true
    scene.add(backWall)

    const leftWall = new THREE.Mesh(new THREE.BoxGeometry(0.15, 7, 14), accentMat)
    leftWall.position.set(-5, 3.5, 0)
    scene.add(leftWall)

    const rightWall = new THREE.Mesh(new THREE.BoxGeometry(0.15, 7, 14), wallMat)
    rightWall.position.set(5, 3.5, 0)
    scene.add(rightWall)

    const ceiling = new THREE.Mesh(new THREE.BoxGeometry(14, 0.1, 14), ceilMat)
    ceiling.position.set(0, 7.05, 0)
    scene.add(ceiling)

    // Wall molding
    const moldH = new THREE.Mesh(new THREE.BoxGeometry(14, 0.08, 0.06), ceilMat)
    ;[-4.4, 4.4].forEach(z => { const m = moldH.clone(); m.position.set(0, 6.95, z); scene.add(m) })
    const moldV = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.08, 14), ceilMat)
    ;[-4.95, 4.95].forEach(x => { const m = moldV.clone(); m.position.set(x, 6.95, 0); scene.add(m) })

    // Baseboard
    const baseboard = new THREE.Mesh(new THREE.BoxGeometry(14, 0.12, 0.04), accentMat)
    ;[{ p: [0, 0.06, -4.47] }, { p: [0, 0.06, 4.47] }].forEach(({ p }) => {
      const b = baseboard.clone(); b.position.set(...p as [number,number,number]); scene.add(b)
    })

    // ── SKY OUTSIDE WINDOW ────────────────────────────────────────────────
    const skyGeo = new THREE.PlaneGeometry(4, 3)
    const skyMat = new THREE.MeshBasicMaterial({
      color: weather?.condition?.match(/rain|thunder/i) ? 0x8899bb :
             weather?.condition?.match(/cloud/i)       ? 0xaabbcc : 0x87ceeb
    })
    const sky = new THREE.Mesh(skyGeo, skyMat)
    sky.position.set(-4.95, 2.8, -1.5)
    sky.rotation.y = Math.PI / 2
    scene.add(sky)

    // ── WINDOW ────────────────────────────────────────────────────────────
    const winG = new THREE.Group()
    winG.position.set(-4.92, 2.8, -1.5)

    const winOuter = new THREE.Mesh(new THREE.BoxGeometry(0.1, 2.6, 2.2), frameMat)
    winG.add(winOuter)
    const winGlass = new THREE.Mesh(new THREE.BoxGeometry(0.04, 2.2, 1.8), glassMat)
    winGlass.position.x = 0.04
    winG.add(winGlass)
    // Crossbars
    const crossH2 = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.05, 2.2), frameMat)
    winG.add(crossH2)
    const crossV2 = new THREE.Mesh(new THREE.BoxGeometry(0.08, 2.6, 0.05), frameMat)
    winG.add(crossV2)
    // Sill
    const sill2 = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.06, 2.4), frameMat)
    sill2.position.set(0.08, -1.32, 0)
    winG.add(sill2)
    scene.add(winG)

    // ── CURTAINS — rich velvet with deep folds ────────────────────────────
    // Rich burgundy-rose velvet material with sheen
    const curtainRichMat = new THREE.MeshStandardMaterial({
      color: 0x8b2a3a, roughness: 0.92, metalness: 0.04, side: THREE.DoubleSide
    })
    const curtainLinMat = new THREE.MeshStandardMaterial({
      color: 0xd4b896, roughness: 0.95, side: THREE.DoubleSide  // warm linen lining
    })

    // Build a panel with deep sinusoidal folds (4 cols, 16 rows for smooth pleats)
    const makePleatCurtain = (foldOffset: number) => {
      const geo = new THREE.PlaneGeometry(1.0, 2.85, 5, 18)
      const pos = geo.attributes.position as THREE.BufferAttribute
      for (let vi = 0; vi < pos.count; vi++) {
        const xv: number = pos.getX(vi)
        const yv: number = pos.getY(vi)
        // Multiple overlapping folds for fabric depth
        const fold = Math.sin((xv * 7 + foldOffset) * 1.1) * 0.055
                   + Math.sin((xv * 13 + foldOffset * 0.5)) * 0.022
        pos.setX(vi, xv + fold)
        // Slight sag at bottom
        pos.setZ(vi, Math.abs(xv) * 0.04 - (1.4 + yv) * 0.008)
      }
      geo.computeVertexNormals()
      return geo
    }

    // Each curtain = 2 overlapping panels (rich + lining) for thickness
    const curtainGroup = new THREE.Group()

    const cLP = new THREE.Mesh(makePleatCurtain(0),   curtainRichMat)
    const cLL = new THREE.Mesh(makePleatCurtain(0.4), curtainLinMat)
    cLP.position.set(-4.82, 2.8, -2.62); cLP.rotation.y = Math.PI/2; cLP.castShadow = true
    cLL.position.set(-4.84, 2.8, -2.62); cLL.rotation.y = Math.PI/2

    const cRP = new THREE.Mesh(makePleatCurtain(Math.PI), curtainRichMat)
    const cRL = new THREE.Mesh(makePleatCurtain(Math.PI+0.4), curtainLinMat)
    cRP.position.set(-4.82, 2.8, -0.38); cRP.rotation.y = Math.PI/2; cRP.castShadow = true
    cRL.position.set(-4.84, 2.8, -0.38); cRL.rotation.y = Math.PI/2

    curtainGroup.add(cLP, cLL, cRP, cRL)
    scene.add(curtainGroup)

    // Curtain top swag valance
    const valance = new THREE.Mesh(new THREE.BoxGeometry(0.08, 0.22, 3.2), curtainRichMat)
    valance.position.set(-4.83, 4.28, -1.5)
    scene.add(valance)

    // Tieback rings on each curtain
    ;[[-2.62], [-0.38]].forEach(([z]) => {
      const tb = new THREE.Mesh(new THREE.TorusGeometry(0.06, 0.012, 6, 16), brassMat)
      tb.position.set(-4.82, 2.0, z); tb.rotation.y = Math.PI/2
      scene.add(tb)
    })

    // Track all 4 panels for sliding animation
    curtainLeftRef.current  = cLP
    curtainRightRef.current = cRP
    curtainLLRef.current    = cLL
    curtainRLRef.current    = cRL

    // Curtain rod
    const rod = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 3.4, 12), brassMat)
    rod.rotation.x = Math.PI / 2
    rod.position.set(-4.85, 4.28, -1.5)
    scene.add(rod)
    ;[-1.7, 1.7].forEach(dz => {
      const f = new THREE.Mesh(new THREE.SphereGeometry(0.038, 10, 10), brassMat)
      f.position.set(-4.85, 4.28, -1.5 + dz); scene.add(f)
    })

    // Monstera plant (window sill)
    const plantG = new THREE.Group()
    plantG.position.set(-4.5, 0, -4)
    // Pot
    const potBody = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.17, 0.38, 10), potMat)
    potBody.position.y = 0.19
    plantG.add(potBody)
    const potRim = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.22, 0.04, 10), potMat)
    potRim.position.y = 0.38
    plantG.add(potRim)
    const soil = new THREE.Mesh(new THREE.CylinderGeometry(0.21, 0.21, 0.02, 10), M(0x3a2810, 0.99))
    soil.position.y = 0.37
    plantG.add(soil)
    // Stems and leaves
    const stems = [
      { rot: [0, 0, 0.3],  h: 0.9,  lScale: 1.0, lRot: [0.2, 0, 0.4] },
      { rot: [0, 1.5, 0.1], h: 0.75, lScale: 0.8, lRot: [0.3, 1.5, -0.2] },
      { rot: [0, -1, 0.4],  h: 0.65, lScale: 0.7, lRot: [0.1, -0.8, 0.5] },
      { rot: [0, 0.7, -0.2],h: 0.82, lScale: 0.9, lRot: [0.25, 0.7, 0.1] },
    ]
    stems.forEach(({ rot, h, lScale, lRot }) => {
      const s = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.018, h, 5), stemMat)
      s.position.y = 0.38 + h/2
      s.rotation.set(...rot as [number,number,number])
      plantG.add(s)
      const tip = new THREE.Object3D()
      tip.position.set(
        Math.sin(rot[2]) * h * 0.9,
        0.38 + h * 0.9 - Math.abs(rot[0])*0.2,
        Math.sin(rot[1]) * h * 0.6
      )
      // Monstera leaf shape — wavy PlaneGeometry
      const lGeo = new THREE.PlaneGeometry(0.36 * lScale, 0.28 * lScale, 3, 3)
      const p2 = lGeo.attributes.position as THREE.BufferAttribute
      for (let k = 0; k < p2.count; k++) {
        const xv: number = p2.getX(k)
        const yv: number = p2.getY(k)
        p2.setZ(k, Math.sin(xv * 3 + yv * 2) * 0.025)
      }
      lGeo.computeVertexNormals()
      const leaf = new THREE.Mesh(lGeo, Math.random() > 0.5 ? leafMat : leafDarkMat)
      leaf.position.copy(tip.position)
      leaf.rotation.set(...lRot as [number, number, number])
      plantG.add(leaf)
    })
    plantG.castShadow = true
    scene.add(plantG)

    // ── SOFA ──────────────────────────────────────────────────────────────
    const sofaG = new THREE.Group()
    sofaG.position.set(-1.0, 0, -3.0)

    const sofaBase = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.44, 1.0), sofaMat)
    sofaBase.position.y = 0.22; sofaBase.castShadow = sofaBase.receiveShadow = true
    sofaG.add(sofaBase)

    for (let i = -1; i <= 1; i++) {
      const seat = new THREE.Mesh(new THREE.BoxGeometry(0.92, 0.14, 0.92), sofaDarkMat)
      seat.position.set(i * 0.92, 0.51, 0.02)
      sofaG.add(seat)
    }
    const sofaBack = new THREE.Mesh(new THREE.BoxGeometry(3.0, 0.78, 0.2), sofaMat)
    sofaBack.position.set(0, 0.83, -0.4); sofaBack.castShadow = true
    sofaG.add(sofaBack)
    ;[-1.5, 1.5].forEach(x => {
      const arm = new THREE.Mesh(new THREE.BoxGeometry(0.22, 0.62, 1.0), sofaMat)
      arm.position.set(x, 0.53, 0)
      sofaG.add(arm)
    })
    // Cushions
    const c1 = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.44, 0.08), cushRust)
    c1.position.set(-0.7, 0.82, -0.25); c1.rotation.y = 0.15; sofaG.add(c1)
    const c2 = new THREE.Mesh(new THREE.BoxGeometry(0.44, 0.44, 0.08), cushSage)
    c2.position.set(0.6, 0.80, -0.26); c2.rotation.y = -0.12; sofaG.add(c2)

    ;[[-1.3,-0.42],[1.3,-0.42],[-1.3,0.42],[1.3,0.42]].forEach(([lx,lz]) => {
      const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.035, 0.14, 6), darkWoodMat)
      leg.position.set(lx, 0.07, lz); sofaG.add(leg)
    })
    scene.add(sofaG)

    // ── COFFEE TABLE ──────────────────────────────────────────────────────
    const ctG = new THREE.Group()
    ctG.position.set(-0.8, 0, 0.8)
    const ctTop = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.055, 0.8), woodMat)
    ctTop.position.y = 0.46; ctTop.castShadow = true; ctG.add(ctTop)
    ;[[-0.55,-0.3],[0.55,-0.3],[-0.55,0.3],[0.55,0.3]].forEach(([lx,lz]) => {
      const l = new THREE.Mesh(new THREE.CylinderGeometry(0.025,0.022,0.46,6), darkWoodMat)
      l.position.set(lx, 0.23, lz); ctG.add(l)
    })
    // Small coaster under where music player sits
    const coaster = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.008, 12), M(0x6a4a20, 0.95))
    coaster.position.set(0.22, 0.468, -0.1); ctG.add(coaster)
    // Remote control
    const remote = new THREE.Mesh(new THREE.BoxGeometry(0.06, 0.012, 0.16), M(0x1a1a1a, 0.3, 0.5))
    remote.position.set(-0.28, 0.467, 0.08); remote.rotation.y = 0.3; ctG.add(remote)
    scene.add(ctG)

    // ── BOOKSHELF (right back) ────────────────────────────────────────────
    const bsG = new THREE.Group()
    bsG.position.set(4.6, 0, 0.5)   // right wall

    const bsBack = new THREE.Mesh(new THREE.BoxGeometry(2.0, 3.6, 0.28), darkWoodMat)
    bsBack.position.y = 1.8; bsG.add(bsBack)
    const bsSide = new THREE.Mesh(new THREE.BoxGeometry(0.06, 3.6, 0.7), darkWoodMat)
    ;[-0.97, 0.97].forEach(x => { const s = bsSide.clone(); s.position.set(x, 1.8, 0.2); bsG.add(s) })
    // Shelves
    ;[0.6, 1.3, 2.0, 2.7].forEach((y: number) => {
      const sh = new THREE.Mesh(new THREE.BoxGeometry(2.0, 0.04, 0.7), darkWoodMat)
      sh.position.set(0, y, 0.2); bsG.add(sh)
    })
    // Books
    let bx = -0.85
    ;[0.6, 1.3, 2.0].forEach((shelf: number) => {
      bx = -0.8
      bookMats.forEach((mat: THREE.MeshStandardMaterial) => {
        const bw = 0.07 + Math.random()*0.05
        const bh = 0.25 + Math.random()*0.12
        const book = new THREE.Mesh(new THREE.BoxGeometry(bw, bh, 0.5), mat)
        book.position.set(bx + bw/2, shelf + bh/2 + 0.04, 0.2)
        book.rotation.y = (Math.random()-0.5)*0.05
        bsG.add(book); bx += bw + 0.015
        if (bx > 0.85) return
      })
    })
    bsG.rotation.y = -Math.PI / 2   // face into room
    bsG.castShadow = true
    scene.add(bsG)

    // ── DESK + ARIA ────────────────────────────────────────────────────────
    const deskG = new THREE.Group()
    deskG.position.set(2.2, 0, 0.8)

    const dTop = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.055, 1.0), woodMat)
    dTop.position.y = 0.82; dTop.castShadow = dTop.receiveShadow = true; deskG.add(dTop)
    const dLip = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.03, 0.03), darkWoodMat)
    dLip.position.set(0, 0.835, 0.515); deskG.add(dLip)
    ;[[-0.95,-0.42],[0.95,-0.42],[-0.95,0.42],[0.95,0.42]].forEach(([lx,lz]) => {
      const l = new THREE.Mesh(new THREE.CylinderGeometry(0.03,0.027,0.82,8), darkWoodMat)
      l.position.set(lx,0.41,lz); deskG.add(l)
    })
    // Drawer
    // const dr = new THREE.Mesh(new THREE.BoxGeometry(0,0,0), darkWoodMat)
    // dr.position.set(-0.35,0.65,0.51); deskG.add(dr)
    // const drH = new THREE.Mesh(new THREE.BoxGeometry(0.1,0.025,0.035), brassMat)
    // drH.position.set(-0.35,0.65,0.528); deskG.add(drH)
    // // Keyboard / notebook
    // const kb = new THREE.Mesh(new THREE.BoxGeometry(0.52,0.015,0.24), M(0x303030,0.1,0.6))
    // kb.position.set(-0.3,0.848,0.1); deskG.add(kb)
    // const nb = new THREE.Mesh(new THREE.BoxGeometry(0.25,0.018,0.32), bookMats[3])
    // nb.position.set(0.3,0.848,0.05); nb.rotation.y = 0.1; deskG.add(nb)
    // Mug
    const mug = new THREE.Mesh(new THREE.CylinderGeometry(0.145,0.04,0.2,10), M(0xf0f0f0,0.7))
    mug.position.set(0.3,0.875,0.15); deskG.add(mug)
    scene.add(deskG)

    // ARIA orb on desk
    const orbG = new THREE.Group()
    orbG.position.set(2.0, 0.9, 0.85)

    // Orb base
    const orbBase = new THREE.Mesh(new THREE.CylinderGeometry(0.08,0.1,0.04,12), steelMat)
    orbG.add(orbBase)
    const orbStem = new THREE.Mesh(new THREE.CylinderGeometry(0.015,0.015,0.2,8), steelMat)
    orbStem.position.y = 0.12; orbG.add(orbStem)

    // Orb sphere
    const orbMat = new THREE.MeshStandardMaterial({
      color: 0x00ffaa, emissive: 0x00ffaa, emissiveIntensity: 1.2,
      roughness: 0.0, metalness: 0.2, transparent: true, opacity: 0.88
    })
    const orb = new THREE.Mesh(new THREE.SphereGeometry(0.18, 32, 32), orbMat)
    orb.position.y = 0.32
    orbG.add(orb)
    ariaOrbRef.current = orb

    // Outer halo ring
    const haloMat = new THREE.MeshBasicMaterial({ color: 0x00ffaa, transparent: true, opacity: 0.3, side: THREE.DoubleSide })
    const halo = new THREE.Mesh(new THREE.TorusGeometry(0.26, 0.012, 8, 48), haloMat)
    halo.position.y = 0.32
    halo.rotation.x = Math.PI / 2
    orbG.add(halo)

    // Inner ring
    const innerHalo = new THREE.Mesh(new THREE.TorusGeometry(0.20, 0.006, 8, 36), haloMat)
    innerHalo.position.y = 0.32
    innerHalo.rotation.x = Math.PI / 3
    orbG.add(innerHalo)

    scene.add(orbG)

    // ── FLOOR LAMP — proper arc lamp ─────────────────────────────────────
    const lampG = new THREE.Group()
    lampG.position.set(-2.8, 0, 0.4)

    // Heavy circular base
    const lampBase2 = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.24, 0.05, 16), steelMat)
    lampBase2.position.y = 0.025
    lampG.add(lampBase2)

    // Weight knob on base
    const lampBaseKnob = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.1, 0.04, 12), steelMat)
    lampBaseKnob.position.y = 0.065; lampG.add(lampBaseKnob)

    // Tall straight vertical pole (1.72m)
    const lampPole = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.022, 1.72, 10), steelMat)
    lampPole.position.y = 0.86 + 0.05; lampG.add(lampPole)

    // Curved arm segments: pole top → arch → shade position
    // Segment 1: angled outward from pole top
    const arm1 = new THREE.Mesh(new THREE.CylinderGeometry(0.013, 0.013, 0.38, 8), steelMat)
    arm1.rotation.z = -Math.PI * 0.18   // lean right ~32°
    arm1.position.set(0.04, 1.79, 0); lampG.add(arm1)

    // Segment 2: curves down gently to hold shade
    const arm2 = new THREE.Mesh(new THREE.CylinderGeometry(0.011, 0.013, 0.22, 8), steelMat)
    arm2.rotation.z = Math.PI * 4.4    // angle down
    arm2.position.set(0.22,1.9, 0); lampG.add(arm2)

    // Shade housing (small cylinder at top of shade)
    const shadeSocket = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.04, 10), steelMat)
    shadeSocket.position.set(0.37, 1.8, 0); lampG.add(shadeSocket)

    // Lamp shade — wide-mouth cone, open bottom (proper reading lamp shape)
    const shadeGeo = new THREE.CylinderGeometry(0.06, 0.28, 0.32, 20, 1, true)
    const lampShade = new THREE.Mesh(shadeGeo, shadeMat)
    lampShade.position.set(0.36, 1.7, 0)  // shade hangs below socket
    lampG.add(lampShade)
    lampSphereRef.current = lampShade as any

    // Inner shade cap (top, closed)
    const shadeTop = new THREE.Mesh(new THREE.CircleGeometry(0.06, 16), shadeMat)
    shadeTop.rotation.x = -Math.PI/2
    shadeTop.position.set(0.35, 1.86, 0); lampG.add(shadeTop)

    // Bulb (inside shade)
    const bulb = new THREE.Mesh(new THREE.SphereGeometry(0.042, 12, 12),
      new THREE.MeshStandardMaterial({ color: 0xffffcc, emissive: 0xffffcc, emissiveIntensity: 2.5, roughness: 0 }))
    bulb.position.set(0.38, 1.78, 0); lampG.add(bulb)

    scene.add(lampG)

    // ── CEILING FAN ────────────────────────────────────────────────────────
    const fanG = new THREE.Group()
    fanG.position.set(-0.5, 6.92, -0.5)

    const fanHub = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.13, 14), steelMat)
    fanG.add(fanHub)
    const fanDown = new THREE.Mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.55, 8), steelMat)
    fanDown.position.y = -0.33; fanG.add(fanDown)

    const bladesG = new THREE.Group()
    bladesG.position.y = -0.6
    ;[0, 90, 180, 270].forEach(deg => {
      const b = new THREE.Mesh(new THREE.BoxGeometry(1.58, 0.022, 0.2), darkWoodMat)
      b.position.set(0, 0, 0); b.rotation.y = THREE.MathUtils.degToRad(deg)
      bladesG.add(b)
    })
    fanG.add(bladesG)
    fanBladesRef.current = bladesG
    const fanCap = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.04, 14), M(0xf0f0f0))
    fanCap.position.y = 0.09; fanG.add(fanCap)
    scene.add(fanG)

    // ── TABLE FAN on desk (right side) ────────────────────────────────────
    const tfG = new THREE.Group()
    tfG.position.set(2.9, 0.87, 1.1)   // on desk surface

    // Base
    const tfBase = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.08, 0.028, 14), steelMat)
    tfG.add(tfBase)
    // Pole
    const tfPole = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 0.24, 8), steelMat)
    tfPole.position.y = 0.13; tfG.add(tfPole)
    // Tilt joint
    const tfJoint = new THREE.Mesh(new THREE.SphereGeometry(0.028, 10, 10), steelMat)
    tfJoint.position.y = 0.255; tfG.add(tfJoint)
    // Fan guard cage (flattened torus rings)
    const cageMat2 = new THREE.MeshStandardMaterial({ color: 0xc0c0c0, roughness:0.3, metalness:0.8, wireframe:false })
    ;[0, 0.028, -0.028].forEach(dz => {
      const ring = new THREE.Mesh(new THREE.TorusGeometry(0.088, 0.005, 0, 0), cageMat2)
      ring.position.set(0, 0.255, dz); ring.rotation.x = Math.PI/2
      tfG.add(ring)
    })
    // Cage spokes
    for (let s = 0; s < 8; s++) {
      const spoke = new THREE.Mesh(new THREE.CylinderGeometry(0.003,0.003,0.17,4), cageMat2)
      spoke.position.set(0, 0.255, 0)
      spoke.rotation.z = (s/8) * Math.PI * 2
      spoke.position.x = 0; spoke.position.y = 0.255
      const a = (s/8)*Math.PI*2
      spoke.position.x = Math.sin(a) * 0.044
      spoke.position.y = 0.255 + Math.cos(a) * 0.044
      spoke.rotation.z = a
      tfG.add(spoke)
    }
    // Blades group (3 blades, rapid spin)
    const tfBladesG = new THREE.Group()
    tfBladesG.position.set(0, 0.255, 0.03)
    ;[0, 120, 240].forEach(deg => {
      const blade = new THREE.Mesh(new THREE.BoxGeometry(0.4, 0.03, 0.022),
        new THREE.MeshStandardMaterial({ color: 0xe8e0d0, roughness:0.7 }))
      blade.position.set(0, 0, 0)
      blade.rotation.z = THREE.MathUtils.degToRad(deg)
      tfBladesG.add(blade)
    })
    tfG.add(tfBladesG)
    tableFanRef.current = tfBladesG
    scene.add(tfG)

    // ── TV UNIT — big wall-mounted TV ────────────────────────────────────
    const tvUnitG = new THREE.Group()
    tvUnitG.position.set(3.1, 0, -4.38)   // slightly right of centre

    // TV media console below
    const tvCab = new THREE.Mesh(new THREE.BoxGeometry(2.4, 0.44, 0.42), darkWoodMat)
    tvCab.position.y = 0.22; tvCab.castShadow = tvCab.receiveShadow = true; tvUnitG.add(tvCab)
    // Cabinet doors
    ;[-0.6, 0.6].forEach(dx => {
      const door = new THREE.Mesh(new THREE.BoxGeometry(0.72, 0.36, 0.01), M(0x8a5e2a, 0.9))
      door.position.set(dx, 0.22, 0.22); tvUnitG.add(door)
      const knob = new THREE.Mesh(new THREE.SphereGeometry(0.018, 8, 8), brassMat)
      knob.position.set(dx + 0.25, 0.22, 0.232); tvUnitG.add(knob)
    })
    // Console legs
    ;[[-1.1,0.18],[-1.1,-0.18],[1.1,0.18],[1.1,-0.18]].forEach(([lx,lz]) => {
      const l = new THREE.Mesh(new THREE.CylinderGeometry(0.02,0.02,0.12,6), steelMat)
      l.position.set(lx, 0.06, lz); tvUnitG.add(l)
    })

    // TV body (wall-mounted, slim)
    const tvBody = new THREE.Mesh(new THREE.BoxGeometry(2.1, 1.22, 0.055), tvMat)
    tvBody.position.y = 1.72; tvBody.castShadow = true; tvUnitG.add(tvBody)

    // TV bezels (ultra-thin)
    const bezelMat2 = M(0x0d0d0d, 0.05, 0.95)
    ;[
      [0, 1.72+0.615, 0, 2.1, 0.02, 0.06],   // top
      [0, 1.72-0.615, 0, 2.1, 0.02, 0.06],   // bottom
      [-1.06, 1.72, 0, 0.02, 1.22, 0.06],    // left
      [ 1.06, 1.72, 0, 0.02, 1.22, 0.06],    // right
    ].forEach(([x,y,z,w,h,d]) => {
      const b = new THREE.Mesh(new THREE.BoxGeometry(w,h,d), bezelMat2)
      b.position.set(x,y,z+0.03); tvUnitG.add(b)
    })

    // TV screen — with emissive color bands (simulates content)
    const tvScreenMat = new THREE.MeshStandardMaterial({
      color: 0x081828, emissive: 0x1133aa, emissiveIntensity: 0,
      roughness: 0.02, metalness: 0.15
    })
    const tvScreen = new THREE.Mesh(new THREE.BoxGeometry(1.98, 1.10, 0.008), tvScreenMat)
    tvScreen.position.set(0, 1.72, 0.032); tvUnitG.add(tvScreen)
    tvScreenRef.current = tvScreen

    // Scanline overlay mesh (semi-transparent horizontal stripes)
    const scanGeo = new THREE.PlaneGeometry(1.98, 1.10, 1, 40)
    const scanMat = new THREE.MeshBasicMaterial({
      color: 0x000000, transparent: true, opacity: 0, depthWrite: false
    })
    const scanMesh = new THREE.Mesh(scanGeo, scanMat)
    scanMesh.position.set(0, 1.72, 0.038); tvUnitG.add(scanMesh)
    tvScanRef.current = scanMesh

    // Status LED under screen
    const led = new THREE.Mesh(new THREE.BoxGeometry(0.022, 0.008, 0.01),
      new THREE.MeshStandardMaterial({ color: 0xff0000, emissive: 0xff0000, emissiveIntensity: 1 }))
    led.position.set(0.92, 0.99, 0.034); tvUnitG.add(led)

    // Wall mount bracket
    const bracket = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.3, 0.05), steelMat)
    bracket.position.set(0, 1.72, -0.055); tvUnitG.add(bracket)

    scene.add(tvUnitG)

    // ── RETRO MUSIC PLAYER — compact unit on coffee table ────────────────
    // Coffee table is at ctG.position = (-0.8, 0, 0.8), top at y=0.515
    const stereoG = new THREE.Group()
    stereoG.position.set(-0.55, 0.515, 0.72)  // on coffee table surface

    // Main body — rounded brick shape (Tivoli/retro radio style)
    const recvMat = new THREE.MeshStandardMaterial({ color: 0x2a1f0e, roughness: 0.5, metalness: 0.2 })
    const recv = new THREE.Mesh(new THREE.BoxGeometry(0.28, 0.11, 0.14), recvMat)
    stereoG.add(recv)

    // Wood-grain side panels
    const sidePanelMat = M(0x8a5c2a, 0.85)
    ;[-0.145, 0.145].forEach(dx => {
      const sp = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.11, 0.14), sidePanelMat)
      sp.position.x = dx; stereoG.add(sp)
    })

    // Front grille fabric (oval speaker area)
    const grilleMat = new THREE.MeshStandardMaterial({ color: 0x1a1008, roughness: 0.98 })
    const grille = new THREE.Mesh(new THREE.BoxGeometry(0.16, 0.082, 0.008), grilleMat)
    grille.position.set(-0.04, 0, 0.074); stereoG.add(grille)
    // Grille dots pattern (3×4 array)
    for (let gx = -1; gx <= 1; gx++) for (let gy = -1; gy <= 1; gy++) {
      const dot = new THREE.Mesh(new THREE.CircleGeometry(0.006, 6),
        new THREE.MeshStandardMaterial({ color: 0x3a3020 }))
      dot.position.set(-0.04 + gx*0.04, gy*0.022, 0.079)
      stereoG.add(dot)
    }

    // Brushed aluminium faceplate strip (right side)
    const faceplateMat = new THREE.MeshStandardMaterial({ color: 0xc8b88a, roughness: 0.15, metalness: 0.9 })
    const faceplate = new THREE.Mesh(new THREE.BoxGeometry(0.095, 0.09, 0.008), faceplateMat)
    faceplate.position.set(0.09, 0, 0.074); stereoG.add(faceplate)

    // VU meter — amber glowing display
    const vuMat = new THREE.MeshStandardMaterial({
      color: 0x402000, emissive: 0xffaa00, emissiveIntensity: 0,
      roughness: 0.1, transparent: true, opacity: 0.95
    })
    const vuMeter = new THREE.Mesh(new THREE.BoxGeometry(0.055, 0.035, 0.002), vuMat)
    vuMeter.position.set(0.075, 0.018, 0.079); stereoG.add(vuMeter)

    // Large tuner dial (classic retro look)
    const tunerRing = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 0.012, 20), faceplateMat)
    tunerRing.rotation.x = Math.PI/2; tunerRing.position.set(0.09, -0.01, 0.079); stereoG.add(tunerRing)
    const tunerInner = new THREE.Mesh(new THREE.CylinderGeometry(0.019, 0.019, 0.014, 16), recvMat)
    tunerInner.rotation.x = Math.PI/2; tunerInner.position.set(0.09, -0.01, 0.081); stereoG.add(tunerInner)

    // Volume knob
    const volKnob = new THREE.Mesh(new THREE.CylinderGeometry(0.013, 0.013, 0.012, 12), recvMat)
    volKnob.rotation.x = Math.PI/2; volKnob.position.set(0.09, 0.028, 0.079); stereoG.add(volKnob)

    // Power LED (green dot)
    const pwrLed = new THREE.Mesh(new THREE.SphereGeometry(0.005, 8, 8),
      new THREE.MeshStandardMaterial({ color: 0x00ff44, emissive: 0x00ff44, emissiveIntensity: 0 }))
    pwrLed.position.set(-0.125, 0.04, 0.076); stereoG.add(pwrLed)
    ;(stereoG as any).pwrLed = pwrLed

    // Antenna (retractable style — thin rod up from top)
    const antenna = new THREE.Mesh(new THREE.CylinderGeometry(0.003, 0.004, 0.22, 6), steelMat)
    antenna.position.set(0.125, 0.165, 0.04)
    antenna.rotation.z = 0.08   // slight tilt
    stereoG.add(antenna)
    const antennaTip = new THREE.Mesh(new THREE.SphereGeometry(0.005, 6, 6), steelMat)
    antennaTip.position.set(0.128, 0.278, 0.04); stereoG.add(antennaTip)

    // Store vuMat ref
    ;(stereoG as any).vuMat = vuMat

    scene.add(stereoG)

    // Amber glow light from stereo (small, local)
    const stereoLight = new THREE.PointLight(0xffaa00, 0, 1.2)
    stereoLight.position.set(-0.55, 0.7, 0.72)
    scene.add(stereoLight)
    stereoLightRef.current = stereoLight
    ;(scene as any).stereoG = stereoG
    ;(stereoG as any).vuMat  = vuMat

    // ── MUSIC NOTE SPRITES (float from stereo) ────────────────────────────
    // Create 12 note sprites as flat circular meshes with emissive color
    const noteColors = [0xf0abfc, 0xc084fc, 0xa855f7, 0x818cf8, 0x38bdf8]
    const noteSprites: THREE.Mesh[] = []
    for (let n = 0; n < 12; n++) {
      const nMat = new THREE.MeshBasicMaterial({
        color: noteColors[n % noteColors.length],
        transparent: true, opacity: 0, depthWrite: false
      })
      // Use a small disc + thin rectangle to approximate a music note shape
      const noteMesh = new THREE.Mesh(new THREE.CircleGeometry(0.018, 10), nMat)
      noteMesh.position.set(
        -0.55 + (Math.random()-0.5)*0.25,
        0.62 + Math.random()*0.1,
        0.72
      )
      noteMesh.userData = {
        baseX: -0.55 + (Math.random()-0.5)*0.3,
        baseY: 0.62,
        t: Math.random() * Math.PI * 2,   // phase offset
        speed: 0.008 + Math.random()*0.006,
        drift: (Math.random()-0.5)*0.4,
      }
      scene.add(noteMesh)
      noteSprites.push(noteMesh)
    }
    musicSpriteRefs.current = noteSprites

    // ── PAINTING (back wall) ──────────────────────────────────────────────
    const paintG = new THREE.Group()
    paintG.position.set(-3.2, 2.4, -4.42)
    const pFrame = new THREE.Mesh(new THREE.BoxGeometry(1.4, 0.95, 0.06), M(0xb8900a, 0.5, 0.7))
    paintG.add(pFrame)
    const pCanvas = new THREE.Mesh(new THREE.BoxGeometry(1.25, 0.8, 0.01),
      new THREE.MeshStandardMaterial({ color: 0x7ab8d4, roughness: 0.8, emissive: 0x224466, emissiveIntensity: 0.12 }))
    pCanvas.position.z = 0.035; paintG.add(pCanvas)
    // Simple landscape (hills)
    const hillMat = M(0x4a8a40, 0.9)
    const hill1 = new THREE.Mesh(new THREE.SphereGeometry(0.22, 12, 8), hillMat)
    hill1.scale.set(1.2, 0.55, 0.5); hill1.position.set(-0.25, -0.22, 0.05); paintG.add(hill1)
    const hill2 = new THREE.Mesh(new THREE.SphereGeometry(0.18, 12, 8), M(0x3a7030, 0.9))
    hill2.scale.set(1.0, 0.5, 0.5); hill2.position.set(0.2, -0.28, 0.06); paintG.add(hill2)
    scene.add(paintG)

    // ── WALL CLOCK ────────────────────────────────────────────────────────
    const clockG = new THREE.Group()
    clockG.position.set(1.5, 2.6, -4.42)
    const clockFace = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.035, 32), M(0xf8f4e4, 0.8))
    clockFace.rotation.x = Math.PI/2; clockG.add(clockFace)
    const clockRim = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.025, 8, 32), steelMat)
    clockG.add(clockRim)
    // Hour markers
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2
      const mk = new THREE.Mesh(new THREE.BoxGeometry(0.015, 0.04, 0.01), M(0x333322, 0.5))
      mk.position.set(Math.sin(a)*0.2, Math.cos(a)*0.2, 0.02); clockG.add(mk)
    }
    scene.add(clockG)

    // Music particles ref unused — note sprites used instead
    musicParticlesRef.current = null

    // ── ANIMATE LOOP ──────────────────────────────────────────────────────
    // Reset camera on custom event
    const onResetCamera = () => {
      const mo = mouseRef.current
      mo.yawTarget = 0; mo.pitchTarget = 0
      mo.radiusTarget = 6.8
      mo.panXTarget = 0.4; mo.panYTarget = 0.7
    }
    renderer.domElement.addEventListener('resetcamera', onResetCamera)

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate)
      const t   = clockRef.current.getElapsedTime()
      const hs  = homeRef.current
      const em  = emotionRef.current
      const emCfg = EMOTION_CFG[em] || EMOTION_CFG.idle
      const [er,eg,eb] = emCfg.glow.split(',').map(Number)

      // ARIA orb: color + pulse
      const orbMesh = ariaOrbRef.current
      if (orbMesh) {
        const mat = orbMesh.material as THREE.MeshStandardMaterial
        const pulse = 0.9 + Math.sin(t * (em === 'thinking' ? 4 : em === 'excited' ? 6 : 2)) * 0.1
        const c = new THREE.Color(`rgb(${er},${eg},${eb})`)
        mat.color.set(c); mat.emissive.set(c)
        mat.emissiveIntensity = pulse * 1.2
        orbMesh.scale.setScalar(1 + Math.sin(t*2)*0.02)
      }

      // ARIA glow light
      if (ariaGlowRef.current) {
        const g = ariaGlowRef.current
        g.color.setRGB(er/255, eg/255, eb/255)
        g.intensity = (em === 'speaking' ? 2.0 : em === 'excited' ? 2.5 : 1.4)
          * (0.85 + Math.sin(t*3)*0.15)
      }

      // Floor lamp
      if (lampLightRef.current) {
        const targetI = hs.lampOn ? (hs.lampBrightness/100) * 4.5 : 0
        lampLightRef.current.intensity += (targetI - lampLightRef.current.intensity) * 0.08
        if (lampSphereRef.current) {
          const sm = lampSphereRef.current.material as THREE.MeshStandardMaterial
          sm.emissiveIntensity = hs.lampOn ? (hs.lampBrightness/100)*0.8 : 0
          if (!sm.emissive || sm.emissive.getHex() === 0) sm.emissive = new THREE.Color(0xffcc70)
        }
      }

      // Curtains: smoothly slide
      // Window spans z=-2.4 to z=-0.6 (width 1.8). Each panel width=1.0.
      // Closed: left center=-1.9 (covers -2.4→-1.4), right center=-1.1 (covers -1.6→-0.6)
      // Overlap zone -1.6→-1.4 ensures full coverage with no gap.
      const targetCLZ = hs.curtainsOpen ? -3.05 : -1.9
      const targetCRZ = hs.curtainsOpen ? -0.05 : -1.1
      if (curtainLeftRef.current) {
        curtainLeftRef.current.position.z  += (targetCLZ - curtainLeftRef.current.position.z)  * 0.07
        if (curtainLLRef.current) curtainLLRef.current.position.z = curtainLeftRef.current.position.z
      }
      if (curtainRightRef.current) {
        curtainRightRef.current.position.z += (targetCRZ - curtainRightRef.current.position.z) * 0.07
        if (curtainRLRef.current) curtainRLRef.current.position.z = curtainRightRef.current.position.z
      }

      // Window light adjusts with curtains
      if (windowLightRef.current) {
        const wTarget = hs.curtainsOpen ? 2.2 : 0.5
        ;(windowLightRef.current as any).intensity += (wTarget - (windowLightRef.current as any).intensity) * 0.04
      }

      // Fan blades spin
      if (fanBladesRef.current) {
        const targetRPS = hs.fanOn ? hs.fanSpeed * 0.04 : 0
        const curRPS    = fanBladesRef.current.userData.speed ?? 0
        const newRPS    = curRPS + (targetRPS - curRPS) * 0.06
        fanBladesRef.current.userData.speed = newRPS
        fanBladesRef.current.rotation.y += newRPS
      }

      // TV screen glow
      if (tvScreenRef.current) {
        const tm = tvScreenRef.current.material as THREE.MeshStandardMaterial
        const targetEI = hs.tvOn ? 0.6 + Math.sin(t * 8) * 0.05 : 0
        tm.emissiveIntensity += (targetEI - tm.emissiveIntensity) * 0.1
        if (hs.tvOn && tm.emissive.getHex() === 0x0a1a2a) {
          tm.emissive.set(0x2244aa)
        } else if (!hs.tvOn) {
          tm.emissive.set(0x0a1a2a)
        }
      }
      if (tvLightRef.current) {
        const targetTL = hs.tvOn ? 1.5 : 0
        tvLightRef.current.intensity += (targetTL - tvLightRef.current.intensity) * 0.08
      }

      // Table fan spin (faster than ceiling, 3 blades)
      if (tableFanRef.current) {
        const spd = hs.fanOn ? hs.fanSpeed * 0.09 : 0
        const cur = tableFanRef.current.userData.tspd ?? 0
        tableFanRef.current.userData.tspd = cur + (spd - cur) * 0.07
        tableFanRef.current.rotation.z += tableFanRef.current.userData.tspd
      }

      // TV screen: dynamic color content + scanlines
      if (tvScreenRef.current) {
        const tm = tvScreenRef.current.material as THREE.MeshStandardMaterial
        const targetEI = hs.tvOn ? 1.8 : 0   // brighter target so screen glows
        tm.emissiveIntensity += (targetEI - tm.emissiveIntensity) * 0.08
        if (hs.tvOn) {
          // Cycle through hues — faster + more saturated for visible glow
          const hue = (t * 0.06) % 1
          const col = new THREE.Color().setHSL(hue, 0.9, 0.45)
          tm.emissive.lerp(col, 0.05)
        } else {
          tm.emissive.lerp(new THREE.Color(0x000000), 0.12)
          tm.emissiveIntensity += (0 - tm.emissiveIntensity) * 0.1
        }
      }
      // Scanline overlay pulsing opacity
      if (tvScanRef.current) {
        const sm = tvScanRef.current.material as THREE.MeshBasicMaterial
        const tgt = hs.tvOn ? 0.08 + Math.sin(t * 30) * 0.02 : 0
        sm.opacity += (tgt - sm.opacity) * 0.15
      }
      if (tvLightRef.current) {
        const targetTL = hs.tvOn ? 4.0 : 0
        tvLightRef.current.intensity += (targetTL - tvLightRef.current.intensity) * 0.06
      }

      // Retro stereo VU meter + note sprites
      const sg = (scene as any).stereoG
      if (sg) {
        const vm = sg.vuMat as THREE.MeshStandardMaterial
        const pl = sg.pwrLed as THREE.Mesh
        if (hs.musicOn) {
          // VU bars bounce to "music"
          const vu = 0.4 + Math.abs(Math.sin(t * 5.5)) * 0.55
                   + Math.abs(Math.sin(t * 8.2)) * 0.3
          vm.emissiveIntensity = Math.min(vu, 1.0)
          ;(pl.material as THREE.MeshStandardMaterial).emissiveIntensity = 1.2
        } else {
          vm.emissiveIntensity += (0 - vm.emissiveIntensity) * 0.08
          ;(pl.material as THREE.MeshStandardMaterial).emissiveIntensity += (0 - (pl.material as THREE.MeshStandardMaterial).emissiveIntensity) * 0.08
        }
      }
      if (stereoLightRef.current) {
        const tgt = hs.musicOn ? 1.2 + Math.sin(t*4)*0.3 : 0
        stereoLightRef.current.intensity += (tgt - stereoLightRef.current.intensity) * 0.06
      }

      // Floating music note sprites
      musicSpriteRefs.current.forEach((note, ni) => {
        const ud = note.userData
        const nm = note.material as THREE.MeshBasicMaterial
        if (hs.musicOn) {
          ud.t += ud.speed
          // Float up from stereo position with gentle drift
          note.position.x = ud.baseX + Math.sin(ud.t * 1.2 + ni) * 0.18 + ud.drift * 0.3
          note.position.y = ud.baseY + ((ud.t * 0.22) % 1.4)
          note.position.z = 0.72 + Math.sin(ud.t + ni * 0.8) * 0.1
          note.rotation.z = Math.sin(ud.t * 2) * 0.4
          // Fade in then out as they float up
          const lifePhase = (ud.t * 0.28) % 1.6
          nm.opacity = lifePhase < 0.3
            ? lifePhase / 0.3
            : lifePhase > 1.1
            ? (1.6 - lifePhase) / 0.5
            : 0.85
        } else {
          nm.opacity += (0 - nm.opacity) * 0.08
        }
      })

      // Ambient room light responds to lamp state
      if (ambientRef.current) {
        const targetA = hs.lampOn ? 0.55 + (hs.lampBrightness/100)*0.35 : 0.3
        ambientRef.current.intensity += (targetA - ambientRef.current.intensity) * 0.04
      }

      // ── Camera: zoom + pan + orbit all lerped ────────────────
      const mo = mouseRef.current

      // Lerp all targets
      mo.yaw    += (mo.yawTarget    - mo.yaw)    * 0.10
      mo.pitch  += (mo.pitchTarget  - mo.pitch)  * 0.10
      mo.radius += (mo.radiusTarget - mo.radius) * 0.12
      mo.panX   += (mo.panXTarget   - mo.panX)   * 0.10
      mo.panY   += (mo.panYTarget   - mo.panY)   * 0.10

      // Gentle breathing when idle
      const breathY = !mo.isDown ? Math.sin(t * 0.18) * 0.006 : 0
      const BASE_Y  = 1.55

      // Orbit position
      camera.position.x = Math.sin(mo.yaw) * mo.radius
      camera.position.z = Math.cos(mo.yaw) * mo.radius
      camera.position.y = BASE_Y - mo.pitch * 1.6 + breathY

      // LookAt follows pan offset
      camera.lookAt(mo.panX, mo.panY, 0)

      renderer.render(scene, camera)
    }
    animate()

    // Resize
    const onResize = () => {
      if (!mountRef.current) return
      const w2 = mountRef.current.clientWidth
      const h2 = mountRef.current.clientHeight
      camera.aspect = w2/h2
      camera.updateProjectionMatrix()
      renderer.setSize(w2, h2)
    }
    window.addEventListener('resize', onResize)

    // ── Camera controls: orbit (left drag) · pan (right drag) · zoom (scroll/pinch) ──
    const el = renderer.domElement
    const mo = mouseRef.current

    // ─ Mouse down ─────────────────────────────────────────────
    const onMouseDown = (e: MouseEvent) => {
      mo.isDown = true
      mo.button = e.button
      mo.lastX  = e.clientX
      mo.lastY  = e.clientY
      el.style.cursor = e.button === 2 ? 'move' : 'grabbing'
      if (e.button === 2) e.preventDefault()
    }
    const onMouseUp = () => {
      mo.isDown = false
      el.style.cursor = 'grab'
    }

    // ─ Mouse move: left=orbit, right=pan ──────────────────────
    const onMouseMove = (e: MouseEvent) => {
      if (!mo.isDown) return
      const dx = e.clientX - mo.lastX
      const dy = e.clientY - mo.lastY
      mo.lastX = e.clientX
      mo.lastY = e.clientY

      if (mo.button === 2) {
        // Right drag — pan lookAt point
        const panSpeed = mo.radius * 0.0012
        mo.panXTarget = Math.max(-4, Math.min(4,   mo.panXTarget - dx * panSpeed))
        mo.panYTarget = Math.max(0,  Math.min(3.5, mo.panYTarget - dy * panSpeed))
      } else {
        // Left drag — orbit
        mo.yawTarget   = Math.max(-Math.PI, Math.min(Math.PI, mo.yawTarget   - dx * 0.0028))
        mo.pitchTarget = Math.max(-0.28,    Math.min(0.28,    mo.pitchTarget + dy * 0.0022))
      }
    }

    // ─ Scroll wheel: zoom ─────────────────────────────────────
    const onWheel = (e: WheelEvent) => {
      e.preventDefault()
      const delta = e.deltaY > 0 ? 1.08 : 0.93   // zoom out/in factor
      mo.radiusTarget = Math.max(1.5, Math.min(12.0, mo.radiusTarget * delta))
    }

    // ─ Context menu: suppress right-click menu on canvas ──────
    const onContextMenu = (e: Event) => e.preventDefault()

    // ─ Touch: single finger=orbit, two fingers=zoom+pan ───────
    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        mo.isPinching = true
        mo.isDown     = false
        const dx = e.touches[0].clientX - e.touches[1].clientX
        const dy = e.touches[0].clientY - e.touches[1].clientY
        mo.lastPinchDist = Math.sqrt(dx*dx + dy*dy)
      } else {
        mo.isDown       = true
        mo.isPinching   = false
        mo.button       = 0
        mo.lastX        = e.touches[0].clientX
        mo.lastY        = e.touches[0].clientY
      }
    }
    const onTouchEnd = (e: TouchEvent) => {
      if (e.touches.length < 2) mo.isPinching = false
      if (e.touches.length === 0) mo.isDown = false
    }
    const onTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2 && mo.isPinching) {
        // Pinch zoom
        const dx = e.touches[0].clientX - e.touches[1].clientX
        const dy = e.touches[0].clientY - e.touches[1].clientY
        const dist = Math.sqrt(dx*dx + dy*dy)
        const scale = mo.lastPinchDist / dist
        mo.radiusTarget = Math.max(1.5, Math.min(12.0, mo.radiusTarget * scale))
        mo.lastPinchDist = dist
        return
      }
      if (!mo.isDown || e.touches.length !== 1) return
      const dx = e.touches[0].clientX - mo.lastX
      const dy = e.touches[0].clientY - mo.lastY
      mo.lastX = e.touches[0].clientX
      mo.lastY = e.touches[0].clientY
      mo.yawTarget   = Math.max(-Math.PI, Math.min(Math.PI, mo.yawTarget   - dx * 0.003))
      mo.pitchTarget = Math.max(-0.28,    Math.min(0.28,    mo.pitchTarget + dy * 0.0025))
    }

    el.style.cursor = 'grab'
    el.addEventListener('mousedown',   onMouseDown)
    el.addEventListener('wheel',       onWheel,       { passive: false })
    el.addEventListener('contextmenu', onContextMenu)
    window.addEventListener('mouseup',    onMouseUp)
    window.addEventListener('mousemove',  onMouseMove)
    el.addEventListener('touchstart',  onTouchStart,  { passive: true })
    el.addEventListener('touchend',    onTouchEnd,    { passive: true })
    el.addEventListener('touchmove',   onTouchMove,   { passive: false })

    return () => {
      cancelAnimationFrame(frameRef.current)
      window.removeEventListener('resize',    onResize)
      window.removeEventListener('mouseup',   onMouseUp)
      window.removeEventListener('mousemove', onMouseMove)
      el.removeEventListener('wheel',       onWheel)
      el.removeEventListener('contextmenu', onContextMenu)
      renderer.dispose()
      mountRef.current?.removeChild(renderer.domElement)
    }
  }, [weather]) // only re-mount on weather change

  return <div ref={mountRef} style={{ width:'100%', height:'100%' }}/>
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: WeatherOverlay
// ─────────────────────────────────────────────────────────────────────────────
function WeatherOverlay({ condition = 'Clear' }: { condition?: string }) {
  const particles = useMemo(() => Array.from({ length: 60 }, (_, i) => ({
    id: i, x: Math.random()*100, delay: Math.random()*3,
    dur: 0.7 + Math.random()*1.3, size: Math.random()*2+1,
  })), [])

  const isRain  = /rain|drizzle/i.test(condition)
  const isSnow  = /snow/i.test(condition)
  const isStorm = /thunder/i.test(condition)

  if (!isRain && !isSnow && !isStorm) return null

  return (
    <div style={{ position:'absolute', inset:0, pointerEvents:'none', overflow:'hidden' }}>
      {isStorm && <div style={{ position:'absolute', inset:0, animation:'lightning 4s infinite', background:'rgba(200,220,255,0.12)' }}/>}
      {particles.map(p => (
        <div key={p.id} style={{
          position:'absolute', left:`${p.x}%`, top:'-20px',
          width: isSnow ? p.size*3 : p.size,
          height: isSnow ? p.size*3 : p.size*12,
          borderRadius: isSnow ? '50%' : 0,
          background: isSnow ? 'rgba(255,255,255,0.8)' : 'rgba(180,220,255,0.5)',
          animation: `${isSnow?'snowDrift':'rainDrop'} ${p.dur}s ${p.delay}s linear infinite`,
        }}/>
      ))}
      <style>{`
        @keyframes rainDrop{from{transform:translateY(-20px) rotate(12deg);opacity:.7}to{transform:translateY(100vh) translateX(-30px) rotate(12deg);opacity:0}}
        @keyframes snowDrift{from{transform:translateY(-20px) translateX(0);opacity:.8}to{transform:translateY(100vh) translateX(40px);opacity:0}}
        @keyframes lightning{0%,92%,100%{opacity:0}93%,96%{opacity:1}94%,95%{opacity:0}}
      `}</style>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: SmartHomePanel — visual controls
// ─────────────────────────────────────────────────────────────────────────────
function SmartHomePanel({
  homeState, onCommand, onDebouncedCmd, onToggle
}: {
  homeState: HomeState
  onCommand: (msg: string) => void
  onDebouncedCmd: (msg: string) => void
  onToggle: (key: keyof HomeState, value: any) => void
}) {
  const controls = [
    {
      key: 'lampOn' as keyof HomeState,
      icon: <Lightbulb size={14}/>,
      label: 'Lamp',
      active: homeState.lampOn,
      color: '#ffd97d',
      onActivate: () => onCommand(homeState.lampOn ? 'Turn off the living room lights' : 'Turn on the living room lights'),
      extra: homeState.lampOn ? (
        <div onClick={e => e.stopPropagation()} style={{ display:'flex', alignItems:'center', gap:4, marginTop:4 }}>
          <input type="range" min={10} max={100} value={homeState.lampBrightness}
            style={{ width:64, accentColor:'#ffd97d' }}
            onChange={e => onToggle('lampBrightness', +e.target.value)}
            onMouseUp={e  => onDebouncedCmd(`Set the lights to ${(e.target as HTMLInputElement).value}% brightness`)}
            onTouchEnd={e => onDebouncedCmd(`Set the lights to ${homeState.lampBrightness}% brightness`)}
          />
          <span style={{ fontSize:9, color:'#8a7040', fontFamily:'monospace' }}>{homeState.lampBrightness}%</span>
        </div>
      ) : null,
    },
    {
      key: 'curtainsOpen' as keyof HomeState,
      icon: <Blinds size={14}/>,
      label: 'Curtains',
      active: homeState.curtainsOpen,
      color: '#c4b5fd',
      onActivate: () => onCommand(homeState.curtainsOpen ? 'Close the curtains' : 'Open the curtains'),
    },
    {
      key: 'fanOn' as keyof HomeState,
      icon: <FanIcon size={14}/>,
      label: 'Fan',
      active: homeState.fanOn,
      color: '#63c3ff',
      onActivate: () => onCommand(homeState.fanOn ? 'Turn off the fan' : 'Turn on the fan'),
      extra: homeState.fanOn ? (
        <div onClick={e => e.stopPropagation()} style={{ display:'flex', gap:3, marginTop:4 }}>
          {[1,2,3].map(s => (
            <button key={s} onClick={() => onCommand(`Set fan speed to ${s}`)}
              style={{
                width:18, height:18, borderRadius:4, border:'none', cursor:'pointer', fontSize:9,
                background: homeState.fanSpeed===s ? '#63c3ff' : 'rgba(99,195,255,0.15)',
                color: homeState.fanSpeed===s ? '#000' : '#63c3ff',
              }}>{s}</button>
          ))}
        </div>
      ) : null,
    },
    {
      key: 'tvOn' as keyof HomeState,
      icon: <Tv size={14}/>,
      label: 'TV',
      active: homeState.tvOn,
      color: '#00ffaa',
      onActivate: () => onCommand(homeState.tvOn ? 'Turn off the TV' : 'Turn on the TV'),
    },
    {
      key: 'musicOn' as keyof HomeState,
      icon: <Music2 size={14}/>,
      label: 'Music',
      active: homeState.musicOn,
      color: '#f0abfc',
      onActivate: () => onCommand(homeState.musicOn ? 'Stop the music' : 'Play some chill music'),
    },
    {
      key: 'thermostat' as keyof HomeState,
      icon: <Thermometer size={14}/>,
      label: `${homeState.thermostat}°C`,
      active: true,
      color: '#fb923c',
      onActivate: () => {},
      extra: (
        <div onClick={e => e.stopPropagation()} style={{ display:'flex', gap:3, marginTop:4 }}>
          <button onClick={() => { onToggle('thermostat', homeState.thermostat - 1); onDebouncedCmd(`Set thermostat to ${homeState.thermostat - 1} degrees`) }}
            style={{ background:'rgba(251,146,60,0.15)', border:'none', color:'#fb923c', cursor:'pointer', borderRadius:4, padding:'1px 5px', fontSize:11 }}>−</button>
          <button onClick={() => { onToggle('thermostat', homeState.thermostat + 1); onDebouncedCmd(`Set thermostat to ${homeState.thermostat + 1} degrees`) }}
            style={{ background:'rgba(251,146,60,0.15)', border:'none', color:'#fb923c', cursor:'pointer', borderRadius:4, padding:'1px 5px', fontSize:11 }}>+</button>
        </div>
      ),
    },
  ]

  return (
    <div style={{
      display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6,
      padding: '10px 14px',
      borderBottom: '1px solid rgba(255,255,255,0.05)',
    }}>
      {controls.map(ctrl => (
        <div key={String(ctrl.key)} style={{
          background: ctrl.active && ctrl.key !== 'thermostat'
            ? `rgba(${hexToRgb(ctrl.color)},0.12)`
            : 'rgba(255,255,255,0.03)',
          border: `1px solid ${ctrl.active && ctrl.key !== 'thermostat' ? `rgba(${hexToRgb(ctrl.color)},0.3)` : 'rgba(255,255,255,0.06)'}`,
          borderRadius: 8, padding: '7px 9px',
          transition: 'all 0.25s',
        }}>
          <div onClick={ctrl.onActivate} style={{ display:'flex', alignItems:'center', gap:5, marginBottom:2, cursor:'pointer' }}>
            <span style={{ color: ctrl.active ? ctrl.color : '#3a5060' }}>{ctrl.icon}</span>
            <span style={{
              fontSize: 10, fontFamily: 'monospace', letterSpacing:0.5,
              color: ctrl.active ? ctrl.color : '#3a5060',
            }}>{ctrl.label}</span>
            {ctrl.key !== 'thermostat' && (
              <div style={{
                marginLeft:'auto', width:7, height:7, borderRadius:'50%',
                background: ctrl.active ? ctrl.color : '#2a3a40',
                boxShadow: ctrl.active ? `0 0 6px ${ctrl.color}` : 'none',
                transition: 'all 0.3s',
              }}/>
            )}
          </div>
          {ctrl.extra}
        </div>
      ))}
    </div>
  )
}

function hexToRgb(hex: string): string {
  const r = parseInt(hex.slice(1,3),16)
  const g = parseInt(hex.slice(3,5),16)
  const b = parseInt(hex.slice(5,7),16)
  return `${r},${g},${b}`
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: ChatPanel
// ─────────────────────────────────────────────────────────────────────────────
function ChatPanel({ messages, loading, onSend, connected, emotion }: {
  messages: Message[]; loading: boolean; onSend: (t: string) => void
  connected: boolean; emotion: EmotionKey
}) {
  const [input,     setInput]     = useState('')
  const [listening, setListening] = useState(false)
  const [voiceErr,  setVoiceErr]  = useState('')
  const recognRef  = useRef<any>(null)
  const endRef     = useRef<HTMLDivElement>(null)
  const inputRef   = useRef<HTMLTextAreaElement>(null)
  const emCfg      = EMOTION_CFG[emotion] || EMOTION_CFG.idle
  const MAX        = 300

  // Web Speech API voice recognition
  const toggleVoice = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (!SpeechRecognition) { setVoiceErr('Voice not supported in this browser'); return }

    if (listening) {
      recognRef.current?.stop()
      setListening(false)
      return
    }

    const recog = new SpeechRecognition()
    recog.lang = 'en-US'
    recog.interimResults = false
    recog.maxAlternatives = 1
    recog.continuous = false

    recog.onstart  = () => { setListening(true); setVoiceErr('') }
    recog.onend    = () => setListening(false)
    recog.onerror  = (e: any) => { setListening(false); setVoiceErr(e.error === 'not-allowed' ? 'Mic access denied' : 'Voice error') }
    recog.onresult = (e: any) => {
      const transcript = e.results[0][0].transcript.trim()
      if (transcript) {
        setInput('')
        onSend(transcript)          // send directly — no staging
      }
      setListening(false)
    }

    recognRef.current = recog
    recog.start()
  }, [listening, onSend])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior:'smooth' }) }, [messages, loading])

  const handleSend = useCallback(() => {
    const t = input.trim(); if (!t || loading) return
    onSend(t); setInput('')
  }, [input, loading, onSend])

  const suggestions = [
    "What's the weather?", "Tell me a joke", "Open the curtains",
    "Play some jazz", "What time is it?", "Turn on the lights",
  ]

  return (
    <div style={{ display:'flex', flexDirection:'column', height:'100%' }}>
      {/* Messages */}
      <div style={{ flex:1, overflowY:'auto', padding:'8px 0' }}>
        {messages.length === 0 ? (
          <div style={{ padding:'12px 4px' }}>
            <div style={{
              background:'rgba(0,255,170,0.04)', border:'1px solid rgba(0,255,170,0.12)',
              borderRadius:10, padding:'12px 14px', marginBottom:12,
            }}>
              <div style={{ fontSize:12, color:'#00ffaa', fontFamily:'monospace', marginBottom:6 }}>◈ ARIA READY</div>
              <div style={{ fontSize:12, color:'#5a8090', lineHeight:1.6 }}>
                Ask me anything — weather, news, time, or control your smart home.
              </div>
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:5 }}>
              {suggestions.map(s => (
                <button key={s} onClick={() => onSend(s)} style={{
                  background:'rgba(255,255,255,0.03)', border:'1px solid rgba(255,255,255,0.07)',
                  borderRadius:7, padding:'7px 10px', cursor:'pointer',
                  color:'#5a7888', fontSize:11, textAlign:'left',
                  transition:'all 0.2s',
                }}
                onMouseEnter={e => { e.currentTarget.style.borderColor='rgba(0,255,170,0.25)'; e.currentTarget.style.color='#00cc88' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor='rgba(255,255,255,0.07)'; e.currentTarget.style.color='#5a7888' }}
                >{s}</button>
              ))}
            </div>
          </div>
        ) : (
          messages.map((msg, i) => {
            const isUser     = msg.role === 'user'
            const prevSame   = i > 0 && messages[i-1].role === msg.role
            const mEmCfg     = EMOTION_CFG[msg.emotion ?? 'speaking'] || EMOTION_CFG.speaking
            const ts         = new Date(msg.ts).toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' })
            return (
              <motion.div key={msg.ts + i}
                initial={{ opacity:0, y:8, scale:0.97 }}
                animate={{ opacity:1, y:0, scale:1 }}
                transition={{ type:'spring', stiffness:320, damping:28 }}
                style={{ marginBottom: prevSame ? 4 : 10, display:'flex', flexDirection:'column',
                  alignItems: isUser ? 'flex-end' : 'flex-start' }}
              >
                {!isUser && !prevSame && (
                  <div style={{ display:'flex', alignItems:'center', gap:5, marginBottom:3 }}>
                    <div style={{
                      width:18, height:18, borderRadius:4,
                      background:`rgba(${mEmCfg.glow},0.2)`,
                      border:`1px solid rgba(${mEmCfg.glow},0.4)`,
                      display:'flex', alignItems:'center', justifyContent:'center',
                    }}>
                      <Cpu size={10} color={mEmCfg.color}/>
                    </div>
                    <span style={{
                      fontSize:9, fontFamily:'monospace', letterSpacing:2,
                      color: mEmCfg.color, opacity:0.7,
                    }}>{mEmCfg.label}</span>
                  </div>
                )}
                <div style={{
                  maxWidth:'85%', padding:'9px 12px', borderRadius:10,
                  background: isUser
                    ? 'rgba(99,195,255,0.12)'
                    : 'rgba(255,255,255,0.04)',
                  border: isUser
                    ? '1px solid rgba(99,195,255,0.2)'
                    : `1px solid rgba(${mEmCfg.glow},0.12)`,
                  borderLeft: isUser ? undefined : `2px solid ${mEmCfg.color}`,
                  color: '#d0dde8', fontSize:13, lineHeight:1.55,
                }}>
                  {msg.content}
                </div>
                <span style={{ fontSize:9, color:'#2a4050', marginTop:2, fontFamily:'monospace' }}>{ts}</span>
              </motion.div>
            )
          })
        )}
        {loading && (
          <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} style={{ display:'flex', alignItems:'center', gap:6, padding:'4px 2px' }}>
            <div style={{ display:'flex', gap:3 }}>
              {[0,1,2].map(i => (
                <motion.div key={i}
                  animate={{ y:[0,-5,0] }}
                  transition={{ duration:0.5, delay:i*0.12, repeat:Infinity }}
                  style={{ width:5, height:5, borderRadius:'50%', background:emCfg.color }}
                />
              ))}
            </div>
            <span style={{ fontSize:10, color:'#3a5060', fontFamily:'monospace' }}>ARIA thinking…</span>
          </motion.div>
        )}
        <div ref={endRef}/>
      </div>

      {/* Input */}
      <div style={{
        borderTop:'1px solid rgba(255,255,255,0.06)',
        paddingTop:10, paddingBottom:4,
      }}>
        {/* Voice error */}
        {voiceErr && (
          <div style={{ fontSize:10, color:'#fb923c', fontFamily:'monospace', marginBottom:4, paddingLeft:2 }}>
            ⚠ {voiceErr}
          </div>
        )}

        {/* Input row */}
        <div style={{ display:'flex', gap:6, alignItems:'flex-end' }}>
          {/* Mic button */}
          <motion.button
            onClick={toggleVoice}
            animate={listening ? { scale:[1,1.12,1], boxShadow:['0 0 0px #ef4444','0 0 14px #ef4444','0 0 0px #ef4444'] } : {}}
            transition={{ duration:0.8, repeat:Infinity }}
            title={listening ? 'Stop listening' : 'Voice input'}
            style={{
              flexShrink:0, width:38, height:38, borderRadius:10, cursor:'pointer',
              background: listening ? 'rgba(239,68,68,0.18)' : 'rgba(255,255,255,0.05)',
              border: listening ? '1px solid rgba(239,68,68,0.5)' : '1px solid rgba(255,255,255,0.08)',
              color: listening ? '#ef4444' : '#3a5a68',
              display:'flex', alignItems:'center', justifyContent:'center',
              transition:'background 0.2s, border 0.2s',
              outline:'none',
            }}>
            {listening
              ? <motion.div animate={{ opacity:[1,0.3,1] }} transition={{ duration:0.6, repeat:Infinity }}>
                  <MicOff size={16}/>
                </motion.div>
              : <Mic size={16}/>
            }
          </motion.button>

          {/* Text input */}
          <div style={{
            flex:1, position:'relative',
            background: listening ? 'rgba(239,68,68,0.05)' : 'rgba(255,255,255,0.04)',
            border:`1px solid ${listening ? 'rgba(239,68,68,0.3)' : input ? `rgba(${emCfg.glow},0.3)` : 'rgba(255,255,255,0.08)'}`,
            borderRadius:10, overflow:'hidden', transition:'all 0.2s',
          }}>
            {listening && (
              <div style={{
                position:'absolute', left:12, top:'50%', transform:'translateY(-50%)',
                display:'flex', gap:3, alignItems:'center', pointerEvents:'none',
              }}>
                {[0,1,2,3,4].map(i => (
                  <motion.div key={i}
                    animate={{ scaleY:[0.3,1,0.3] }}
                    transition={{ duration:0.5, delay:i*0.08, repeat:Infinity }}
                    style={{ width:3, height:14, background:'#ef4444', borderRadius:2 }}
                  />
                ))}
                <span style={{ fontSize:11, color:'#ef4444', marginLeft:4, fontFamily:'monospace' }}>Listening…</span>
              </div>
            )}
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value.slice(0, MAX))}
              onKeyDown={e => { if (e.key==='Enter' && !e.shiftKey) { e.preventDefault(); handleSend() } }}
              placeholder={listening ? '' : 'Ask ARIA anything…'}
              rows={1}
              style={{
                width:'100%', background:'transparent', border:'none', outline:'none',
                color: listening ? 'transparent' : '#c8d8e4',
                fontSize:13, padding:'10px 40px 10px 12px',
                resize:'none', fontFamily:'inherit', lineHeight:1.5,
              }}
            />
            <button onClick={handleSend} disabled={(!input.trim() && !listening) || loading}
              style={{
                position:'absolute', right:6, top:'50%', transform:'translateY(-50%)',
                width:28, height:28, borderRadius:7, border:'none', cursor:'pointer',
                background: input.trim() ? emCfg.color : 'rgba(255,255,255,0.06)',
                color: input.trim() ? '#000' : '#3a5060',
                display:'flex', alignItems:'center', justifyContent:'center',
                transition:'all 0.2s',
              }}>
              {loading ? <Loader size={13} style={{ animation:'spin 1s linear infinite' }}/> : <Send size={13}/>}
            </button>
          </div>
        </div>

        {/* Footer hints */}
        <div style={{ display:'flex', justifyContent:'space-between', marginTop:5, padding:'0 2px' }}>
          <span style={{ fontSize:9, color:'#2a4050', fontFamily:'monospace' }}>
            {listening ? '🔴 Say your command · click mic to stop' : 'ENTER · SHIFT+ENTER newline'}
          </span>
          <div style={{ display:'flex', alignItems:'center', gap:4 }}>
            {input.length > MAX*0.85 && (
              <span style={{ fontSize:9, color:'#fb923c', fontFamily:'monospace' }}>{MAX-input.length}</span>
            )}
            <div style={{ width:6, height:6, borderRadius:'50%',
              background: connected ? '#00ffaa' : '#ff5050',
              boxShadow: `0 0 5px ${connected ? '#00ffaa' : '#ff5050'}` }}/>
            <span style={{ fontSize:9, color:'#2a4050', fontFamily:'monospace' }}>
              {connected ? 'WS' : 'REST'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: NewsTicker
// ─────────────────────────────────────────────────────────────────────────────
function NewsTicker({ items }: { items: NewsItem[] }) {
  if (!items.length) return null
  const text = items.map(n => `◆ ${n.title}`).join('   ')
  return (
    <div style={{
      height:28, background:'rgba(6,10,18,0.95)',
      borderTop:'1px solid rgba(99,195,255,0.08)',
      overflow:'hidden', display:'flex', alignItems:'center',
    }}>
      <div style={{
        fontSize:11, color:'#2a5060', whiteSpace:'nowrap',
        fontFamily:'"Courier New", monospace',
        animation:'ticker 40s linear infinite',
      }}>
        {text}{'  '}{text}
      </div>
      <style>{`@keyframes ticker{from{transform:translateX(100vw)}to{transform:translateX(-200%)}}`}</style>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: LoadingScreen
// ─────────────────────────────────────────────────────────────────────────────
function LoadingScreen({ onDone }: { onDone: () => void }) {
  const [phase, setPhase] = useState(0)
  const [progress, setProgress] = useState(0)
  const [log, setLog] = useState<string[]>([])
  const LOGS = [
    'Initialising ARIA core...', 'Loading emotion engine...', 'Calibrating pixel face...',
    'Connecting to Mistral AI...', 'Building 3D scene...', 'Syncing smart home...', 'ARIA online.',
  ]

  useEffect(() => {
    let i = 0
    const id = setInterval(() => {
      if (i < LOGS.length) {
        setLog(l => [...l, LOGS[i]])
        setProgress(Math.round(((i+1)/LOGS.length)*100))
        i++
      } else {
        clearInterval(id)
        setTimeout(onDone, 600)
      }
    }, 380)
    return () => clearInterval(id)
  }, [onDone])

  return (
    <div style={{
      width:'100%', height:'100%', background:'#04080f',
      display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      gap:32,
    }}>
      <HoloFace emotion="thinking" size={180}/>
      <div style={{ width:280 }}>
        <div style={{
          height:2, background:'rgba(255,255,255,0.06)', borderRadius:2, marginBottom:16, overflow:'hidden'
        }}>
          <motion.div animate={{ width:`${progress}%` }} transition={{ duration:0.3 }}
            style={{ height:'100%', background:'#00ffaa', borderRadius:2,
              boxShadow:'0 0 8px #00ffaa' }}/>
        </div>
        <div style={{ fontFamily:'"Courier New", monospace', fontSize:11, color:'#2a5060' }}>
          {log.map((l,i) => (
            <motion.div key={i} initial={{ opacity:0 }} animate={{ opacity:1 }}
              style={{ marginBottom:3, color: i===log.length-1 ? '#00ffaa' : '#2a4050' }}>
              {i===log.length-1 ? '▶ ' : '✓ '}{l}
            </motion.div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: HomePage
// ─────────────────────────────────────────────────────────────────────────────
function HomePage({ onEnter }: { onEnter: () => void }) {
  return (
    <div style={{
      width:'100%', height:'100%', background:'#04080f',
      display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center',
      gap:40, position:'relative', overflow:'hidden',
    }}>
      {/* Background grid */}
      <div style={{
        position:'absolute', inset:0,
        backgroundImage:`
          linear-gradient(rgba(0,255,170,0.03) 1px, transparent 1px),
          linear-gradient(90deg, rgba(0,255,170,0.03) 1px, transparent 1px)
        `,
        backgroundSize:'40px 40px',
      }}/>
      <div style={{
        position:'absolute', inset:0,
        background:'radial-gradient(ellipse 60% 60% at 50% 50%, rgba(0,255,170,0.04), transparent)',
      }}/>

      <motion.div initial={{ opacity:0, y:30 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.8 }}
        style={{ position:'relative', zIndex:1, textAlign:'center' }}>
        <HoloFace emotion="idle" size={200}/>
      </motion.div>

      <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ delay:0.4 }}
        style={{ position:'relative', zIndex:1, textAlign:'center' }}>
        <h1 style={{
          fontFamily:'"Courier New", monospace', fontSize:38, fontWeight:700,
          color:'#00ffaa', letterSpacing:8, marginBottom:8,
          textShadow:'0 0 30px rgba(0,255,170,0.4)',
        }}>ARIA</h1>
        <p style={{ fontSize:13, color:'#3a5060', letterSpacing:3, fontFamily:'monospace' }}>
          ADVANCED RESPONSIVE INTELLIGENCE ASSISTANT
        </p>
      </motion.div>

      <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} transition={{ delay:0.8 }}
        style={{ position:'relative', zIndex:1, display:'flex', gap:20, flexWrap:'wrap', justifyContent:'center' }}>
        {['AI Chat', 'Smart Home', 'Live Weather', 'Real-time News'].map((f: string) => (
          <div key={f} style={{
            padding:'7px 16px', borderRadius:20,
            background:'rgba(0,255,170,0.05)',
            border:'1px solid rgba(0,255,170,0.15)',
            fontSize:11, color:'#2a6050', fontFamily:'monospace', letterSpacing:1,
          }}>{f}</div>
        ))}
      </motion.div>

      <motion.button
        initial={{ opacity:0, scale:0.9 }} animate={{ opacity:1, scale:1 }} transition={{ delay:1 }}
        onClick={onEnter}
        whileHover={{ scale:1.04, boxShadow:'0 0 24px rgba(0,255,170,0.35)' }}
        whileTap={{ scale:0.97 }}
        style={{
          position:'relative', zIndex:1,
          padding:'14px 40px', borderRadius:30, border:'1px solid rgba(0,255,170,0.4)',
          background:'rgba(0,255,170,0.08)', color:'#00ffaa', cursor:'pointer',
          fontSize:13, fontFamily:'monospace', letterSpacing:4,
        }}>
        ENTER ROOM
      </motion.button>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: RoomPage
// ─────────────────────────────────────────────────────────────────────────────
function RoomPage() {
  const [homeState, setHomeState] = useState<HomeState>(DEFAULT_HOME)
  const [muted,     setMuted]     = useState(false)
  const [time,      setTime]      = useState(new Date())
  const [city, setCity]           = useState(DEFAULT_CITY)

  // Auto-detect city from browser geolocation on mount
  useEffect(() => {
    if (!navigator.geolocation) return
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          const { latitude, longitude } = pos.coords
          // Reverse geocode using open-meteo's free geocoding (no API key)
          const r = await fetch(
            `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`,
            { headers: { 'Accept-Language': 'en' } }
          )
          const d = await r.json()
          const detected =
            d?.address?.city ||
            d?.address?.town ||
            d?.address?.village ||
            d?.address?.county ||
            DEFAULT_CITY
          setCity(detected)
        } catch { /* keep default */ }
      },
      () => { /* permission denied — keep default */ },
      { timeout: 6000 }
    )
  }, [])
  const weather                   = useWeather(city)
  const [showControls, setShowControls] = useState(true)

  const handleHomeUpdate = useCallback((msg: string) => {
    setHomeState(prev => inferHomeState(msg, prev))
  }, [])

  const { connected, emotion, speaking, messages, news, loading, sendMessage } =
    useAgent(handleHomeUpdate, city)

  const handleToggle = useCallback((key: keyof HomeState, value: any) => {
    setHomeState(prev => ({ ...prev, [key]: value }))
  }, [])

  const handleCommand = useCallback((cmd: string) => {
    sendMessage(cmd)
  }, [sendMessage])

  // City is now sent via useAgent on every message (WS: set_city / REST: city field)
  // sendWithCity is kept as alias for backward compatibility
  const sendWithCity = useCallback((text: string) => {
    sendMessage(text)
  }, [sendMessage])

  // Debounced command — fires only after 2 s of inactivity (for sliders/steppers)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const handleDebouncedCmd = useCallback((cmd: string) => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      sendMessage(cmd)
    }, 2000)
  }, [sendMessage])

  useEffect(() => {
    const id = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(id)
  }, [])

  const emCfg = EMOTION_CFG[emotion] || EMOTION_CFG.idle
  const weatherIcon = () => {
    const c = (weather?.condition ?? '').toLowerCase()
    if (/thunder/.test(c)) return <Zap size={14} color="#fbbf24"/>
    if (/rain|drizzle/.test(c)) return <CloudRain size={14} color="#60a5fa"/>
    if (/cloud/.test(c))  return <Cloud size={14} color="#9ca3af"/>
    if (/snow/.test(c))   return <Star size={14} color="#bfdbfe"/>
    return <Sun size={14} color="#fde68a"/>
  }

  return (
    <div style={{ width:'100%', height:'100%', background:'#04080f', display:'flex', flexDirection:'column' }}>
      {/* Top bar */}
      <div style={{
        display:'flex', alignItems:'center', justifyContent:'space-between',
        padding:'0 20px', height:46, flexShrink:0,
        background:'rgba(4,8,15,0.95)', backdropFilter:'blur(12px)',
        borderBottom:'1px solid rgba(0,255,170,0.08)',
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <motion.div
            animate={{ boxShadow: connected ? ['0 0 4px #00ffaa','0 0 12px #00ffaa','0 0 4px #00ffaa'] : '0 0 4px #ff5050' }}
            transition={{ duration:2, repeat:Infinity }}
            style={{ width:7, height:7, borderRadius:'50%', background: connected ? '#00ffaa' : '#ff5050' }}/>
          <span style={{ fontFamily:'"Courier New", monospace', fontSize:13, color:'#00ffaa', fontWeight:700, letterSpacing:3 }}>
            ARIA
          </span>
          <span style={{ fontSize:10, color:'#1a3040', fontFamily:'monospace', letterSpacing:2 }}>
            {connected ? 'ONLINE' : 'OFFLINE'}
          </span>
        </div>

        <div style={{ display:'flex', alignItems:'center', gap:18 }}>
          {weather && (
            <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:12, color:'#4a6070' }}>
              {weatherIcon()}
              <span>{Math.round(weather.temp)}°C</span>
              <span style={{ color:'#1a3040' }}>{weather.city}</span>
            </div>
          )}
          <span style={{ fontFamily:'monospace', fontSize:12, color:'#2a4050' }}>
            {time.toLocaleTimeString('en-US', { hour:'2-digit', minute:'2-digit' })}
          </span>
          <button onClick={() => setMuted(m => !m)} style={{ background:'none', border:'none', cursor:'pointer', color:'#2a4050', padding:4 }}>
            {muted ? <VolumeX size={13}/> : <Volume2 size={13}/>}
          </button>
        </div>
      </div>

      {/* Main */}
      <div style={{ flex:1, display:'flex', overflow:'hidden', minHeight:0 }}>

        {/* 3D Room */}
        <div style={{ flex:'0 0 68%', position:'relative', overflow:'hidden' }}>
          <ThreeRoom emotion={emotion} weather={weather} homeState={homeState}/>
          <WeatherOverlay condition={weather?.condition}/>

          {/* Emotion badge */}
          <motion.div
            animate={{ borderColor:`rgba(${emCfg.glow},0.4)` }}
            style={{
              position:'absolute', top:14, left:14,
              background:'rgba(4,8,15,0.75)', backdropFilter:'blur(8px)',
              border:`1px solid rgba(${emCfg.glow},0.3)`,
              borderRadius:7, padding:'5px 11px',
              fontFamily:'monospace', fontSize:10, color:emCfg.color, letterSpacing:2,
              display:'flex', alignItems:'center', gap:5,
            }}>
            <motion.div
              animate={{ opacity:[0.4,1,0.4], scale:[0.9,1.1,0.9] }}
              transition={{ duration:1.5, repeat:Infinity }}
              style={{ width:5, height:5, borderRadius:'50%', background:emCfg.color }}/>
            {emCfg.label}
          </motion.div>

          {/* Home state quick-read overlay */}
          <div style={{
            position:'absolute', bottom:14, left:14,
            display:'flex', gap:5, flexWrap:'wrap',
          }}>
            {[
              { icon:'💡', on:homeState.lampOn,      label:`${homeState.lampBrightness}%` },
              { icon:'🪟', on:homeState.curtainsOpen, label:homeState.curtainsOpen?'OPEN':'SHUT' },
              { icon:'💨', on:homeState.fanOn,        label:`SP${homeState.fanSpeed}` },
              { icon:'📺', on:homeState.tvOn,         label:'TV' },
              { icon:'🎵', on:homeState.musicOn,      label:'MUSIC' },
            ].map(({ icon, on, label }) => (
              <div key={label} style={{
                background: on ? 'rgba(0,255,170,0.1)' : 'rgba(207, 214, 225, 0.6)',
                border:`1px solid ${on ? 'rgba(0,255,170,0.25)' : 'rgba(255,255,255,0.05)'}`,
                borderRadius:5, padding:'3px 7px', fontSize:10,
                fontFamily:'monospace', color: on ? '#00cc88' : '#2a3a40',
                display:'flex', gap:4, alignItems:'center',
              }}>
                <span>{icon}</span><span>{label}</span>
              </div>
            ))}
          </div>

          {/* Reset camera button */}
          <button
            title="Reset camera view"
            onClick={() => {
              const mo = (document.querySelector('canvas') as any)?._mouseRef
              // Reset via a custom event the ThreeRoom canvas listens to
              const el = document.querySelector('canvas')
              if (el) el.dispatchEvent(new CustomEvent('resetcamera'))
            }}
            style={{
              position:'absolute', top:46, right:14,
              background:'rgba(227, 233, 243, 0.75)', backdropFilter:'blur(8px)',
              border:'1px solid rgba(255,255,255,0.1)', borderRadius:7,
              color:'#4a6070', fontSize:10, fontFamily:'monospace', cursor:'pointer',
              padding:'5px 11px', display:'flex', alignItems:'center', gap:5,
            }}>
            ⌖ RESET
          </button>

          {/* Zoom hint */}
          <div style={{
            position:'absolute', bottom:50, right:14,
            background:'rgba(219, 224, 231, 0.6)', borderRadius:6,
            padding:'4px 8px', fontSize:9, color:'#2a4050', fontFamily:'monospace',
            display:'flex', flexDirection:'column', gap:2, alignItems:'flex-end',
          }}>
            <span>🖱 Left drag — orbit</span>
            <span>🖱 Right drag — pan</span>
            <span>🖱 Scroll — zoom</span>
            <span>📱 Pinch — zoom</span>
          </div>

          {/* Controls toggle */}
          <button onClick={() => setShowControls(s => !s)} style={{
            position:'absolute', top:14, right:14,
            background:'rgba(207, 210, 216, 0.75)', backdropFilter:'blur(8px)',
            border:'1px solid rgba(255,255,255,0.1)', borderRadius:7,
            color:'#4a6070', fontSize:10, fontFamily:'monospace', cursor:'pointer',
            padding:'5px 11px', display:'flex', alignItems:'center', gap:5,
          }}>
            <Lightbulb size={11}/> CONTROLS
          </button>
        </div>

        {/* Right panel */}
        <div style={{
          flex:'0 0 32%', display:'flex', flexDirection:'column',
          background:'rgba(4,8,15,0.97)', borderLeft:'1px solid rgba(0,255,170,0.06)',
          overflow:'hidden',
        }}>
          {/* ARIA face section */}
          <div style={{
            display:'flex', flexDirection:'column', alignItems:'center',
            padding:'16px 16px 10px',
            background:'radial-gradient(ellipse 80% 55% at 50% 50%, rgba(0,255,170,0.04), transparent)',
            borderBottom:'1px solid rgba(255,255,255,0.05)', flexShrink:0,
          }}>
            <div style={{ position:'relative' }}>
              <HoloFace emotion={emotion} speaking={speaking} size={170}/>
              {speaking && (
                <>
                  <motion.div
                    animate={{ scale:[1,1.08,1], opacity:[0.3,0,0.3] }}
                    transition={{ duration:1.4, repeat:Infinity }}
                    style={{
                      position:'absolute', inset:-10, borderRadius:8,
                      border:`1px solid rgba(${emCfg.glow},0.4)`,
                      pointerEvents:'none',
                    }}/>
                  <motion.div
                    animate={{ scale:[1,1.15,1], opacity:[0.2,0,0.2] }}
                    transition={{ duration:1.4, delay:0.3, repeat:Infinity }}
                    style={{
                      position:'absolute', inset:-20, borderRadius:10,
                      border:`1px solid rgba(${emCfg.glow},0.2)`,
                      pointerEvents:'none',
                    }}/>
                </>
              )}
            </div>
          </div>

          {/* Smart home controls */}
          <AnimatePresence>
            {showControls && (
              <motion.div
                initial={{ height:0, opacity:0 }} animate={{ height:'auto', opacity:1 }}
                exit={{ height:0, opacity:0 }} transition={{ duration:0.25 }}
                style={{ overflow:'hidden', flexShrink:0 }}>
                <SmartHomePanel
                  homeState={homeState}
                  onCommand={handleCommand}
                  onDebouncedCmd={handleDebouncedCmd}
                  onToggle={handleToggle}
                />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Chat */}
          <div style={{ flex:1, padding:'10px 14px', overflow:'hidden', minHeight:0 }}>
            <ChatPanel
              messages={messages} loading={loading}
              onSend={sendWithCity} connected={connected} emotion={emotion}
            />
          </div>
        </div>
      </div>

      {/* News ticker */}
      <NewsTicker items={news}/>

      <style>{`
        @keyframes spin { from{transform:rotate(0deg)}to{transform:rotate(360deg)} }
      `}</style>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// PAGE: AboutPage
// ─────────────────────────────────────────────────────────────────────────────
function AboutPage() {
  const stack = [
    { label:'Backend',    color:'#00ffaa', items:['FastAPI','LangChain','Mistral AI','Tavily','WebSocket'] },
    { label:'Frontend',   color:'#63c3ff', items:['React 18','TypeScript','Three.js','Framer Motion','Vite'] },
    { label:'AI Tools',   color:'#f0abfc', items:['Weather','News Fetch','Time Query','Reminders','Jokes'] },
    { label:'Smart Home', color:'#ffd97d', items:['Lights','Curtains','Fan','Thermostat','TV · Music'] },
  ]
  return (
    <div style={{ width:'100%', height:'100%', overflow:'auto', background:'#04080f', color:'#e2eaf4', padding:'60px 24px' }}>
      <div style={{ maxWidth:760, margin:'0 auto' }}>
        <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }}
          style={{ textAlign:'center', marginBottom:56 }}>
          <HoloFace emotion="happy" size={130}/>
          <h1 style={{ fontFamily:'"Courier New", monospace', fontSize:28, color:'#00ffaa', marginTop:20, letterSpacing:6 }}>ABOUT ARIA</h1>
          <p style={{ color:'#3a5060', fontSize:13, lineHeight:1.8, maxWidth:520, margin:'12px auto 0' }}>
            A full-stack AI home assistant powered by Mistral AI and LangChain.
            ARIA features a holographic pixel face with 8 emotions, a photorealistic 3D
            living room with interactive smart home devices, live weather, and real-time news.
          </p>
        </motion.div>
        <div style={{ display:'grid', gridTemplateColumns:'repeat(auto-fit,minmax(170px,1fr))', gap:16 }}>
          {stack.map((s,i) => (
            <motion.div key={i} initial={{ opacity:0, y:20 }} whileInView={{ opacity:1, y:0 }} transition={{ delay:i*0.1 }}
              style={{ padding:20, borderRadius:12, background:'rgba(255,255,255,0.025)', border:`1px solid rgba(255,255,255,0.06)` }}>
              <div style={{ fontSize:10, color:s.color, letterSpacing:3, fontFamily:'monospace', marginBottom:12 }}>{s.label}</div>
              {s.items.map(item => (
                <div key={item} style={{ padding:'4px 0', fontSize:12, color:'#4a6070', borderBottom:'1px solid rgba(255,255,255,0.04)' }}>{item}</div>
              ))}
            </motion.div>
          ))}
        </div>
        <div style={{ marginTop:56, textAlign:'center', color:'#1a3040', fontSize:11, fontFamily:'monospace' }}>
          ARIA v3.0 · Mistral AI · LangChain · Three.js · React 18
        </div>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENT: Navbar
// ─────────────────────────────────────────────────────────────────────────────
function Navbar({ page, setPage }: { page: string; setPage: (p: string) => void }) {
  if (page === 'loading') return null
  const links = [
    { id:'home',  label:'Home',  icon:<Home size={13}/> },
    { id:'room',  label:'Room',  icon:<Power size={13}/> },
    { id:'about', label:'About', icon:<Info size={13}/> },
  ]
  return (
    <div style={{
      position:'fixed', bottom:22, left:'50%', transform:'translateX(-50%)', zIndex:200,
      background:'rgba(4,8,15,0.92)', backdropFilter:'blur(16px)',
      border:'1px solid rgba(0,255,170,0.12)', borderRadius:40,
      padding:'7px 20px', display:'flex', gap:4,
    }}>
      {links.map(l => (
        <motion.button key={l.id} onClick={() => setPage(l.id)}
          whileHover={{ scale:1.06 }} whileTap={{ scale:0.95 }}
          style={{
            display:'flex', alignItems:'center', gap:5, padding:'7px 16px',
            borderRadius:24, border:'none', cursor:'pointer',
            background: page===l.id ? 'rgba(0,255,170,0.12)' : 'transparent',
            color: page===l.id ? '#00ffaa' : '#2a4050',
            fontSize:11, fontFamily:'monospace', letterSpacing:2,
            transition:'all 0.2s',
          }}>
          {l.icon}{l.label}
        </motion.button>
      ))}
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT
// ─────────────────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState<string>(() =>
    sessionStorage.getItem('aria_v3_loaded') ? 'home' : 'loading'
  )
  const handleDone = useCallback(() => {
    sessionStorage.setItem('aria_v3_loaded', '1'); setPage('home')
  }, [])

  useEffect(() => {
    const link = document.createElement('link')
    link.rel = 'stylesheet'
    link.href = 'https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&display=swap'
    document.head.appendChild(link)
    const style = document.createElement('style')
    style.textContent = `
      *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
      html,body,#root{width:100%;height:100%;overflow:hidden}
      body{background:#04080f;color:#e2eaf4;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}
      input,button,textarea{font-family:inherit}
      ::-webkit-scrollbar{width:3px}
      ::-webkit-scrollbar-thumb{background:rgba(0,255,170,0.18);border-radius:2px}
    `
    document.head.appendChild(style)
  }, [])

  return (
    <div style={{ width:'100vw', height:'100vh', overflow:'hidden', position:'relative' }}>
      <AnimatePresence mode="wait">
        {page === 'loading' && (
          <motion.div key="loading" style={{ position:'absolute', inset:0 }} exit={{ opacity:0 }}>
            <LoadingScreen onDone={handleDone}/>
          </motion.div>
        )}
        {page === 'home' && (
          <motion.div key="home" style={{ position:'absolute', inset:0 }}
            initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}>
            <HomePage onEnter={() => setPage('room')}/>
          </motion.div>
        )}
        {page === 'room' && (
          <motion.div key="room" style={{ position:'absolute', inset:0 }}
            initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}>
            <RoomPage/>
          </motion.div>
        )}
        {page === 'about' && (
          <motion.div key="about" style={{ position:'absolute', inset:0 }}
            initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}>
            <AboutPage/>
          </motion.div>
        )}
      </AnimatePresence>
      <Navbar page={page} setPage={setPage}/>
    </div>
  )
}