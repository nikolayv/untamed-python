/**
 * Next.js/React WebSocket Video Stream Client
 *
 * Example component that connects to the Python WebSocket server
 * and displays the styled video stream.
 *
 * Usage in Next.js:
 *   import VideoStream from './client_example'
 *
 *   function MyPage() {
 *     return <VideoStream wsUrl="ws://localhost:8765" />
 *   }
 *
 * For Three.js integration, see the ThreeJsVideoStream component below.
 */

'use client' // For Next.js 13+ app router

import { useEffect, useRef, useState } from 'react'

interface VideoStreamProps {
  wsUrl?: string
  width?: number
  height?: number
  className?: string
}

interface FrameMessage {
  type: 'frame' | 'connected' | 'error'
  data?: string
  timestamp?: number
  frameNumber?: number
  message?: string
  fps?: number
  resolution?: {
    width: number
    height: number
  }
  style?: string
}

/**
 * Basic video stream component using HTML5 <img> tag
 */
export function VideoStream({
  wsUrl = 'ws://localhost:8765',
  width = 640,
  height = 480,
  className = ''
}: VideoStreamProps) {
  const [imageSrc, setImageSrc] = useState<string>('')
  const [connected, setConnected] = useState(false)
  const [fps, setFps] = useState<number>(0)
  const [style, setStyle] = useState<string>('')
  const [frameCount, setFrameCount] = useState(0)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const message: FrameMessage = JSON.parse(event.data)

        if (message.type === 'connected') {
          console.log('Server info:', message)
          setFps(message.fps || 0)
          setStyle(message.style || '')
        } else if (message.type === 'frame') {
          // Update image with base64 data
          setImageSrc(`data:image/jpeg;base64,${message.data}`)
          setFrameCount(message.frameNumber || 0)
        }
      } catch (error) {
        console.error('Error parsing message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    }

    // Cleanup
    return () => {
      ws.close()
    }
  }, [wsUrl])

  return (
    <div className={className}>
      <div style={{ position: 'relative' }}>
        {imageSrc ? (
          <img
            src={imageSrc}
            alt="Video stream"
            width={width}
            height={height}
            style={{ display: 'block' }}
          />
        ) : (
          <div
            style={{
              width,
              height,
              background: '#1a1a1a',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#666'
            }}
          >
            {connected ? 'Waiting for frames...' : 'Connecting...'}
          </div>
        )}

        {/* Status overlay */}
        <div style={{
          position: 'absolute',
          top: 10,
          left: 10,
          background: 'rgba(0,0,0,0.7)',
          color: 'white',
          padding: '8px 12px',
          borderRadius: 4,
          fontSize: 12,
          fontFamily: 'monospace'
        }}>
          <div>{connected ? '🟢 Connected' : '🔴 Disconnected'}</div>
          {style && <div>Style: {style}</div>}
          {fps > 0 && <div>FPS: {fps}</div>}
          {frameCount > 0 && <div>Frame: {frameCount}</div>}
        </div>
      </div>
    </div>
  )
}

/**
 * Three.js video stream component using texture mapping
 * Displays the video stream on a plane in a Three.js scene
 */
export function ThreeJsVideoStream({
  wsUrl = 'ws://localhost:8765',
  width = 640,
  height = 480,
}: VideoStreamProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    if (!canvasRef.current) return

    // Three.js setup
    const THREE = require('three')
    const scene = new THREE.Scene()
    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000)
    const renderer = new THREE.WebGLRenderer({ canvas: canvasRef.current })
    renderer.setSize(width, height)

    // Create a plane to display the video
    const geometry = new THREE.PlaneGeometry(16, 9)

    // Create canvas texture
    const textureCanvas = document.createElement('canvas')
    textureCanvas.width = width
    textureCanvas.height = height
    const textureContext = textureCanvas.getContext('2d')!

    const texture = new THREE.CanvasTexture(textureCanvas)
    const material = new THREE.MeshBasicMaterial({ map: texture })
    const plane = new THREE.Mesh(geometry, material)
    scene.add(plane)

    camera.position.z = 10

    // WebSocket connection
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws

    ws.onopen = () => {
      console.log('WebSocket connected')
      setConnected(true)
    }

    ws.onmessage = (event) => {
      try {
        const message: FrameMessage = JSON.parse(event.data)

        if (message.type === 'frame' && message.data) {
          // Create image from base64 data
          const img = new Image()
          img.onload = () => {
            // Draw image to canvas texture
            textureContext.drawImage(img, 0, 0, width, height)
            texture.needsUpdate = true
          }
          img.src = `data:image/jpeg;base64,${message.data}`
        }
      } catch (error) {
        console.error('Error parsing message:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    ws.onclose = () => {
      console.log('WebSocket disconnected')
      setConnected(false)
    }

    // Animation loop
    function animate() {
      requestAnimationFrame(animate)

      // Optional: Add some rotation or animation
      // plane.rotation.y += 0.001

      renderer.render(scene, camera)
    }
    animate()

    // Cleanup
    return () => {
      ws.close()
      renderer.dispose()
      geometry.dispose()
      material.dispose()
      texture.dispose()
    }
  }, [wsUrl, width, height])

  return (
    <div style={{ position: 'relative' }}>
      <canvas ref={canvasRef} />

      {/* Status indicator */}
      <div style={{
        position: 'absolute',
        top: 10,
        left: 10,
        background: 'rgba(0,0,0,0.7)',
        color: 'white',
        padding: '8px 12px',
        borderRadius: 4,
        fontSize: 12
      }}>
        {connected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>
    </div>
  )
}

/**
 * Example usage in a Next.js page:
 *
 * // app/stream/page.tsx
 * import { VideoStream, ThreeJsVideoStream } from '@/components/client_example'
 *
 * export default function StreamPage() {
 *   return (
 *     <div className="container">
 *       <h1>Neural Style Transfer Stream</h1>
 *
 *       {/* Basic video display */}
 *       <VideoStream
 *         wsUrl="ws://localhost:8765"
 *         width={640}
 *         height={480}
 *       />
 *
 *       {/* Or with Three.js */}
 *       <ThreeJsVideoStream
 *         wsUrl="ws://localhost:8765"
 *         width={640}
 *         height={480}
 *       />
 *     </div>
 *   )
 * }
 */

export default VideoStream
