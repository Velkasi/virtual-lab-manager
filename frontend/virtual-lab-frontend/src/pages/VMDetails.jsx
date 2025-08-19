import { useState, useEffect } from 'react'
import { useParams, useSearchParams, Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { 
  ArrowLeft,
  Play, 
  Square, 
  RotateCcw, 
  Monitor, 
  Terminal, 
  Server,
  Cpu,
  HardDrive,
  MemoryStick,
  Network
} from 'lucide-react'
import { vmsAPI } from '../services/api'
import { useToast } from '../hooks/use-toast'
import SSHTerminal from '../components/SSHTerminal'
import VNCViewer from '../components/VNCViewer'

const VMDetails = () => {
  const { vmId } = useParams()
  const [searchParams] = useSearchParams()
  const accessType = searchParams.get('access')
  const { toast } = useToast()
  
  const [vm, setVm] = useState(null)
  const [sshInfo, setSshInfo] = useState(null)
  const [vncInfo, setVncInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState({
    ssh: false,
    vnc: false
  })

  useEffect(() => {
    fetchVMDetails()
    if (accessType === 'ssh') {
      fetchSSHInfo()
    } else if (accessType === 'vnc') {
      fetchVNCInfo()
    }
  }, [vmId, accessType])

  const fetchVMDetails = async () => {
    try {
      const response = await vmsAPI.getById(vmId)
      setVm(response.data)
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les détails de la VM",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchSSHInfo = async () => {
    try {
      const response = await vmsAPI.getSSHAccess(vmId)
      setSshInfo(response.data)
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de récupérer les informations SSH",
        variant: "destructive",
      })
    }
  }

  const fetchVNCInfo = async () => {
    try {
      const response = await vmsAPI.getVNCAccess(vmId)
      setVncInfo(response.data)
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de récupérer les informations VNC",
        variant: "destructive",
      })
    }
  }

  const handleVMAction = async (action) => {
    setActionLoading(action)
    
    try {
      let response
      switch (action) {
        case 'start':
          response = await vmsAPI.start(vmId)
          break
        case 'stop':
          response = await vmsAPI.stop(vmId)
          break
        case 'restart':
          response = await vmsAPI.restart(vmId)
          break
        default:
          return
      }
      
      toast({
        title: "Succès",
        description: response.data.message,
      })
      
      // Rafraîchir les détails de la VM
      fetchVMDetails()
    } catch (error) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || `Impossible d'exécuter l'action ${action}`,
        variant: "destructive",
      })
    } finally {
      setActionLoading(null)
    }
  }

  const handleConnectionStatus = (type, status) => {
    setConnectionStatus(prev => ({
      ...prev,
      [type]: status
    }))
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      pending: { variant: 'secondary', label: 'En attente' },
      running: { variant: 'default', label: 'En cours' },
      stopped: { variant: 'outline', label: 'Arrêté' },
      error: { variant: 'destructive', label: 'Erreur' },
    }

    const config = statusConfig[status] || { variant: 'outline', label: status }
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  const formatBytes = (bytes) => {
    if (bytes >= 1024) {
      return `${(bytes / 1024).toFixed(1)} GB`
    }
    return `${bytes} MB`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (!vm) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-2">Machine virtuelle non trouvée</h2>
        <p className="text-muted-foreground mb-4">
          La machine virtuelle demandée n'existe pas ou a été supprimée.
        </p>
        <Button asChild>
          <Link to="/">Retour au tableau de bord</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* En-tête */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button variant="outline" asChild>
            <Link to={`/labs/${vm.lab_id}`}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Retour au lab
            </Link>
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{vm.name}</h1>
            <p className="text-muted-foreground">{vm.os_image}</p>
          </div>
        </div>
        <div className="flex items-center space-x-4">
          {getStatusBadge(vm.status)}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Informations de la VM */}
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Spécifications</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Cpu className="h-4 w-4 text-muted-foreground" />
                  <span>vCPU</span>
                </div>
                <span className="font-medium">{vm.vcpu}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <MemoryStick className="h-4 w-4 text-muted-foreground" />
                  <span>RAM</span>
                </div>
                <span className="font-medium">{formatBytes(vm.ram_mb)}</span>
              </div>
              
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                  <span>Disque</span>
                </div>
                <span className="font-medium">{vm.disk_gb} GB</span>
              </div>
              
              {vm.ssh_port && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Network className="h-4 w-4 text-muted-foreground" />
                    <span>Port SSH</span>
                  </div>
                  <span className="font-medium">{vm.ssh_port}</span>
                </div>
              )}
              
              {vm.vnc_port && (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Network className="h-4 w-4 text-muted-foreground" />
                    <span>Port VNC</span>
                  </div>
                  <span className="font-medium">{vm.vnc_port}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {vm.status === 'stopped' && (
                <Button
                  className="w-full"
                  onClick={() => handleVMAction('start')}
                  disabled={actionLoading === 'start'}
                >
                  <Play className="h-4 w-4 mr-2" />
                  {actionLoading === 'start' ? 'Démarrage...' : 'Démarrer'}
                </Button>
              )}
              
              {vm.status === 'running' && (
                <>
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleVMAction('stop')}
                    disabled={actionLoading === 'stop'}
                  >
                    <Square className="h-4 w-4 mr-2" />
                    {actionLoading === 'stop' ? 'Arrêt...' : 'Arrêter'}
                  </Button>
                  
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => handleVMAction('restart')}
                    disabled={actionLoading === 'restart'}
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    {actionLoading === 'restart' ? 'Redémarrage...' : 'Redémarrer'}
                  </Button>
                </>
              )}
            </CardContent>
          </Card>

          {/* État des connexions */}
          {vm.status === 'running' && (
            <Card>
              <CardHeader>
                <CardTitle>État des connexions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Terminal className="h-4 w-4" />
                    <span>SSH</span>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${connectionStatus.ssh ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                </div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Monitor className="h-4 w-4" />
                    <span>VNC</span>
                  </div>
                  <div className={`w-2 h-2 rounded-full ${connectionStatus.vnc ? 'bg-green-500' : 'bg-gray-400'}`}></div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Zone d'accès SSH/VNC */}
        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Accès à la machine virtuelle</CardTitle>
              <CardDescription>
                Connectez-vous à votre VM via SSH ou VNC
              </CardDescription>
            </CardHeader>
            <CardContent>
              {vm.status !== 'running' ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  <Server className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="text-lg font-semibold mb-2">VM non démarrée</h3>
                  <p className="text-muted-foreground mb-4">
                    La machine virtuelle doit être démarrée pour permettre l'accès SSH/VNC.
                  </p>
                  {vm.status === 'stopped' && (
                    <Button onClick={() => handleVMAction('start')}>
                      <Play className="h-4 w-4 mr-2" />
                      Démarrer la VM
                    </Button>
                  )}
                </div>
              ) : (
                <Tabs defaultValue={accessType || 'ssh'} className="w-full">
                  <TabsList className="grid w-full grid-cols-2">
                    <TabsTrigger value="ssh">SSH</TabsTrigger>
                    <TabsTrigger value="vnc">VNC</TabsTrigger>
                  </TabsList>
                  
                  <TabsContent value="ssh" className="mt-4">
                    <div className="h-96">
                      <SSHTerminal 
                        vmId={vmId} 
                        onConnectionStatus={(status) => handleConnectionStatus('ssh', status)}
                      />
                    </div>
                  </TabsContent>
                  
                  <TabsContent value="vnc" className="mt-4">
                    <div className="h-96">
                      <VNCViewer 
                        vmId={vmId}
                        onConnectionStatus={(status) => handleConnectionStatus('vnc', status)}
                      />
                    </div>
                  </TabsContent>
                </Tabs>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default VMDetails

