import { useEffect, useRef, useState } from 'react'

const VNCViewer = ({ vmId, onConnectionStatus }) => {
  const canvasRef = useRef(null)
  const websocket = useRef(null)
  const [isConnected, setIsConnected] = useState(false)
  const [connectionError, setConnectionError] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!canvasRef.current) return

    // Initialiser la connexion VNC
    connectWebSocket()

    return () => {
      if (websocket.current) {
        websocket.current.close()
      }
    }
  }, [vmId])

  const connectWebSocket = () => {
    const wsUrl = `ws://localhost:8000/api/v1/ws/vnc/${vmId}`
    
    try {
      websocket.current = new WebSocket(wsUrl)

      websocket.current.onopen = () => {
        setIsConnected(true)
        setConnectionError(null)
        setIsLoading(false)
        onConnectionStatus?.(true)
      }

      websocket.current.onmessage = (event) => {
        // Ici, nous traiterions les données VNC
        // Pour une implémentation complète, nous aurions besoin d'un client VNC JavaScript
        // comme noVNC ou une bibliothèque similaire
        console.log('Données VNC reçues:', event.data)
      }

      websocket.current.onclose = (event) => {
        setIsConnected(false)
        setIsLoading(false)
        onConnectionStatus?.(false)
        
        if (event.code !== 1000) {
          setConnectionError(`Connexion fermée (code: ${event.code})`)
        }
      }

      websocket.current.onerror = (error) => {
        setConnectionError('Erreur de connexion WebSocket')
        setIsLoading(false)
        onConnectionStatus?.(false)
      }

    } catch (error) {
      setConnectionError(`Erreur lors de la connexion: ${error.message}`)
      setIsLoading(false)
      onConnectionStatus?.(false)
    }
  }

  const reconnect = () => {
    if (websocket.current) {
      websocket.current.close()
    }
    setConnectionError(null)
    setIsLoading(true)
    connectWebSocket()
  }

  const handleMouseMove = (event) => {
    if (!isConnected || !websocket.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Envoyer les coordonnées de la souris au serveur VNC
    // (implémentation simplifiée)
    const mouseData = JSON.stringify({
      type: 'mouse_move',
      x: Math.floor(x),
      y: Math.floor(y)
    })
    
    websocket.current.send(mouseData)
  }

  const handleMouseClick = (event) => {
    if (!isConnected || !websocket.current) return

    const rect = canvasRef.current.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top

    // Envoyer le clic de souris au serveur VNC
    const clickData = JSON.stringify({
      type: 'mouse_click',
      x: Math.floor(x),
      y: Math.floor(y),
      button: event.button
    })
    
    websocket.current.send(clickData)
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
      
      <div className="flex-1 bg-gray-900 flex items-center justify-center">
        {isLoading ? (
          <div className="text-white">Connexion en cours...</div>
        ) : connectionError ? (
          <div className="text-center text-white">
            <div className="text-red-400 mb-2">{connectionError}</div>
            <button
              onClick={reconnect}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded"
            >
              Réessayer
            </button>
          </div>
        ) : (
          <canvas
            ref={canvasRef}
            width={800}
            height={600}
            className="border border-gray-600 bg-black cursor-crosshair"
            onMouseMove={handleMouseMove}
            onClick={handleMouseClick}
            style={{ maxWidth: '100%', maxHeight: '100%' }}
          />
        )}
      </div>
      
      <div className="p-2 bg-gray-800 text-white text-xs">
        <div className="text-center text-gray-400">
          Client VNC simplifié - Pour une implémentation complète, intégrer noVNC
        </div>
      </div>
    </div>
  )
}

export default VNCViewer

