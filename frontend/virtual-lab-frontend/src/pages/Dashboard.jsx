import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Badge } from '../components/ui/badge'
import { Plus, Server, Play, Square, RotateCcw, Trash2, Eye } from 'lucide-react'
import { labsAPI } from '../services/api'
import { useToast } from '../hooks/use-toast'

const Dashboard = () => {
  const [labs, setLabs] = useState([])
  const [loading, setLoading] = useState(true)
  const { toast } = useToast()

  useEffect(() => {
    fetchLabs()
  }, [])

  const fetchLabs = async () => {
    try {
      const response = await labsAPI.getAll()
      setLabs(response.data)
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de charger les laboratoires",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteLab = async (labId) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce laboratoire ?')) {
      return
    }

    try {
      await labsAPI.delete(labId)
      toast({
        title: "Succès",
        description: "Laboratoire supprimé avec succès",
      })
      fetchLabs()
    } catch (error) {
      toast({
        title: "Erreur",
        description: "Impossible de supprimer le laboratoire",
        variant: "destructive",
      })
    }
  }

  const handleDeployLab = async (labId) => {
    try {
      await labsAPI.deploy(labId)
      toast({
        title: "Succès",
        description: "Déploiement lancé",
      })
      fetchLabs()
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
      error: { variant: 'destructive', label: 'Erreur' },
      deleted: { variant: 'outline', label: 'Supprimé' },
    }

    const config = statusConfig[status] || { variant: 'outline', label: status }
    return <Badge variant={config.variant}>{config.label}</Badge>
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Tableau de bord</h1>
          <p className="text-muted-foreground">
            Gérez vos laboratoires virtuels
          </p>
        </div>
        <Button asChild>
          <Link to="/create-lab" className="flex items-center space-x-2">
            <Plus className="h-4 w-4" />
            <span>Nouveau Lab</span>
          </Link>
        </Button>
      </div>

      {labs.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Server className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Aucun laboratoire</h3>
            <p className="text-muted-foreground text-center mb-4">
              Commencez par créer votre premier laboratoire virtuel
            </p>
            <Button asChild>
              <Link to="/create-lab">Créer un laboratoire</Link>
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {labs.map((lab) => (
            <Card key={lab.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">{lab.name}</CardTitle>
                  {getStatusBadge(lab.status)}
                </div>
                <CardDescription>
                  {lab.description || 'Aucune description'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Server className="h-4 w-4" />
                    <span>{lab.vms?.length || 0} VM(s)</span>
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      asChild
                    >
                      <Link to={`/labs/${lab.id}`} className="flex items-center space-x-1">
                        <Eye className="h-3 w-3" />
                        <span>Voir</span>
                      </Link>
                    </Button>
                    
                    {lab.status === 'created' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDeployLab(lab.id)}
                        className="flex items-center space-x-1"
                      >
                        <Play className="h-3 w-3" />
                        <span>Déployer</span>
                      </Button>
                    )}
                    
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDeleteLab(lab.id)}
                      className="flex items-center space-x-1 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-3 w-3" />
                      <span>Supprimer</span>
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

export default Dashboard

