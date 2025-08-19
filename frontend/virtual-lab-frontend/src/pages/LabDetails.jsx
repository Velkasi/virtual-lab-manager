import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs'
import { ScrollArea } from '../components/ui/scroll-area'
import { 
  Play, 
  Square, 
  RotateCcw, 
  Monitor, 
  Terminal, 
  Server, 
  Clock,
  Cpu,
  HardDrive,
  MemoryStick
} from 'lucide-react'
import { labsAPI, vmsAPI } from '../services/api'
import { useToast } from '../hooks/use-toast'

const LabDetails = () => {
  const { labId } = useParams()
  const { toast } = useToast()
  
  const [lab, setLab] = useState(null)
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState({})

  useEffect(() => {
    fetchLabDetails()
    fetchLogs()
  }, [labId])

  const fetchLabDetails = async () => {
    try {
      const response = await labsAPI.getById(labId)
      setLab(response.data)
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les détails du laboratoire",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const fetchLogs = async () => {
    try {
      const response = await labsAPI.getLogs(labId)
      setLogs(response.data)
    } catch (error) {
      console.error('Erreur lors du chargement des logs:', error)
    }
  }

  const handleVMAction = async (vmId, action) => {
    setActionLoading({ ...actionLoading, [vmId]: action })
    
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
      
      // Rafraîchir les détails du lab
      fetchLabDetails()
    } catch (error) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || `Impossible d'exécuter l'action ${action}`,
        variant: "destructive",
      })
    } finally {
      setActionLoading({ ...actionLoading, [vmId]: null })
    }
  }

  const handleDeployLab = async () => {
    try {
      await labsAPI.deploy(labId)
      toast({
        title: "Succès",
        description: "Déploiement lancé",
      })
      fetchLabDetails()
      fetchLogs()
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de lancer le déploiement",
        variant: "destructive",
      })
    }
  }

  const getStatusBadge = (status) => {
    const statusConfig = {
      created: { variant: 'secondary', label: 'Créé' },
      deploying: { variant: 'default', label: 'Déploiement' },
      deployed: { variant: 'default', label: 'Déployé' },
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

  if (!lab) {
    return (
      <div className="text-center py-12">
        <h2 className="text-2xl font-bold mb-2">Laboratoire non trouvé</h2>
        <p className="text-muted-foreground mb-4">
          Le laboratoire demandé n'existe pas ou a été supprimé.
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
        <div>
          <h1 className="text-3xl font-bold">{lab.name}</h1>
          <p className="text-muted-foreground">
            {lab.description || 'Aucune description'}
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {getStatusBadge(lab.status)}
          {lab.status === 'created' && (
            <Button onClick={handleDeployLab}>
              <Play className="h-4 w-4 mr-2" />
              Déployer
            </Button>
          )}
        </div>
      </div>

      <Tabs defaultValue="vms" className="space-y-4">
        <TabsList>
          <TabsTrigger value="vms">Machines virtuelles</TabsTrigger>
          <TabsTrigger value="logs">Logs de déploiement</TabsTrigger>
        </TabsList>

        <TabsContent value="vms" className="space-y-4">
          {lab.vms && lab.vms.length > 0 ? (
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {lab.vms.map((vm) => (
                <Card key={vm.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">{vm.name}</CardTitle>
                      {getStatusBadge(vm.status)}
                    </div>
                    <CardDescription>{vm.os_image}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Spécifications hardware */}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div className="flex items-center space-x-2">
                        <Cpu className="h-4 w-4 text-muted-foreground" />
                        <span>{vm.vcpu} vCPU</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <MemoryStick className="h-4 w-4 text-muted-foreground" />
                        <span>{formatBytes(vm.ram_mb)}</span>
                      </div>
                      <div className="flex items-center space-x-2 col-span-2">
                        <HardDrive className="h-4 w-4 text-muted-foreground" />
                        <span>{vm.disk_gb} GB</span>
                      </div>
                    </div>

                    {/* Actions VM */}
                    <div className="flex flex-wrap gap-2">
                      {vm.status === 'stopped' && (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleVMAction(vm.id, 'start')}
                          disabled={actionLoading[vm.id] === 'start'}
                        >
                          <Play className="h-3 w-3 mr-1" />
                          {actionLoading[vm.id] === 'start' ? 'Démarrage...' : 'Démarrer'}
                        </Button>
                      )}
                      
                      {vm.status === 'running' && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleVMAction(vm.id, 'stop')}
                            disabled={actionLoading[vm.id] === 'stop'}
                          >
                            <Square className="h-3 w-3 mr-1" />
                            {actionLoading[vm.id] === 'stop' ? 'Arrêt...' : 'Arrêter'}
                          </Button>
                          
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleVMAction(vm.id, 'restart')}
                            disabled={actionLoading[vm.id] === 'restart'}
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            {actionLoading[vm.id] === 'restart' ? 'Redémarrage...' : 'Redémarrer'}
                          </Button>
                        </>
                      )}
                    </div>

                    {/* Accès SSH/VNC */}
                    {vm.status === 'running' && (
                      <div className="flex space-x-2 pt-2 border-t">
                        <Button
                          variant="outline"
                          size="sm"
                          asChild
                          className="flex-1"
                        >
                          <Link to={`/vms/${vm.id}?access=ssh`}>
                            <Terminal className="h-3 w-3 mr-1" />
                            SSH
                          </Link>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          asChild
                          className="flex-1"
                        >
                          <Link to={`/vms/${vm.id}?access=vnc`}>
                            <Monitor className="h-3 w-3 mr-1" />
                            VNC
                          </Link>
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Server className="h-12 w-12 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Aucune machine virtuelle</h3>
                <p className="text-muted-foreground text-center">
                  Ce laboratoire ne contient aucune machine virtuelle.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Logs de déploiement</CardTitle>
              <CardDescription>
                Historique des opérations Terraform et Ansible
              </CardDescription>
            </CardHeader>
            <CardContent>
              {logs.length > 0 ? (
                <ScrollArea className="h-96 w-full rounded border p-4">
                  <div className="space-y-4">
                    {logs.map((log) => (
                      <div key={log.id} className="border-l-2 border-muted pl-4">
                        <div className="flex items-center space-x-2 mb-2">
                          <Badge variant="outline">{log.log_type}</Badge>
                          <div className="flex items-center space-x-1 text-sm text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{new Date(log.created_at).toLocaleString()}</span>
                          </div>
                        </div>
                        <pre className="text-sm bg-muted p-2 rounded overflow-x-auto">
                          {log.content}
                        </pre>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              ) : (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">Aucun log disponible</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default LabDetails

