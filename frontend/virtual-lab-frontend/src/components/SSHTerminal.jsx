import { useEffect, useRef, useState } from 'react'
import { Terminal } from 'xterm'
import { FitAddon } from '@xterm/addon-fit'
import { WebLinksAddon } from '@xterm/addon-web-links'
import 'xterm/css/xterm.css'

const SSHTerminal = ({ vmId, onConnectionStatus }) => {
  const terminalRef = useRef(null)
  const terminal = useRef(null)
  const websocket = useRef(null)
  const fitAddon = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState(null)

  useEffect(() => {
    if (!terminalRef.current) return

    // Initialiser le terminal
    terminal.current = new Terminal({
      cursorBlink: true,
      fontSize: 14,
      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace',
      theme: {
        background: '#1e1e1e',
        foreground: '#d4d4d4',
        cursor: '#ffffff',
        selection: '#264f78',
        black: '#000000',
        red: '#cd3131',
        green: '#0dbc79',
        yellow: '#e5e510',
        blue: '#2472c8',
        magenta: '#bc3fbc',
        cyan: '#11a8cd',
        white: '#e5e5e5',
        brightBlack: '#666666',
        brightRed: '#f14c4c',
        brightGreen: '#23d18b',
        brightYellow: '#f5f543',
        brightBlue: '#3b8eea',
        brightMagenta: '#d670d6',
        brightCyan: '#29b8db',
        brightWhite: '#e5e5e5'
      }
    })

    // Ajouter les addons
    fitAddon.current = new FitAddon()
    terminal.current.loadAddon(fitAddon.current)
    terminal.current.loadAddon(new WebLinksAddon())

    // Ouvrir le terminal dans le DOM
    terminal.current.open(terminalRef.current)
    fitAddon.current.fit()

    // Établir la connexion WebSocket
    connectWebSocket()

    // Gérer le redimensionnement
    const handleResize = () => {
      if (fitAddon.current) {
        fitAddon.current.fit()
      }
    }

    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (websocket.current) {
        websocket.current.close()
      }
      if (terminal.current) {
        terminal.current.dispose()
      }
    }
  }, [vmId])

  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8000/api/v1/ws/ssh/${vmId}`
    
    try {
      websocket.current = new WebSocket(wsUrl)

      websocket.current.onopen = () => {
        setIsConnected(true)
        setConnectionError(null)
        onConnectionStatus?.(true)
        
        terminal.current.writeln('Connexion SSH établie...')
        terminal.current.writeln('Appuyez sur Entrée pour commencer.')
        
        // Gérer les entrées du terminal
        terminal.current.onData((data) => {
          if (websocket.current && websocket.current.readyState === WebSocket.OPEN) {
            websocket.current.send(data)
          }
        })
      }

      websocket.current.onmessage = (event) => {
        if (terminal.current) {
          terminal.current.write(event.data)
        }
      }

      websocket.current.onclose = (event) => {
        setIsConnected(false)
        onConnectionStatus?.(false)
        
        if (event.code !== 1000) {
          const error = `Connexion fermée (code: ${event.code})`
          setConnectionError(error)
          terminal.current?.writeln(`\r\n${error}`)
        }
      }

      websocket.current.onerror = (error) => {
        const errorMsg = 'Erreur de connexion WebSocket'
        setConnectionError(errorMsg)
        onConnectionStatus?.(false)
        terminal.current?.writeln(`\r\n${errorMsg}`)
      }

    } catch (error) {
      const errorMsg = `Erreur lors de la connexion: ${error.message}`
      setConnectionError(errorMsg)
      onConnectionStatus?.(false)
      terminal.current?.writeln(errorMsg)
    }
  }

  const reconnect = () => {
    if (websocket.current) {
      websocket.current.close()
    }
    setConnectionError(null)
    terminal.current?.clear()
    connectWebSocket()
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between p-2 bg-gray-800 text-white text-sm">
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span>{isConnected ? 'Connecté' : 'Déconnecté'}</span>
        </div>
        {connectionError && (
          <button
            onClick={reconnect}
            className="px-2 py-1 bg-blue-600 hover:bg-blue-700 rounded text-xs"
          >
            Reconnecter
          </button>
        )}
      </div>
      <div 
        ref={terminalRef} 
        className="flex-1 bg-black"
        style={{ minHeight: '400px' }}
      />
    </div>
  )
}

export default SSHTerminal

