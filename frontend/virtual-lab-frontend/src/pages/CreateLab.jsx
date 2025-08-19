import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card'
import { Input } from '../components/ui/input'
import { Label } from '../components/ui/label'
import { Textarea } from '../components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select'
import { Plus, Trash2, Server } from 'lucide-react'
import { labsAPI } from '../services/api'
import { useToast } from '../hooks/use-toast'
import { v4 as uuidv4 } from 'uuid'

const CreateLab = () => {
  const navigate = useNavigate()
  const { toast } = useToast()
  
  const [labData, setLabData] = useState({
    name: '',
    description: '',
    ansible_config_yaml: ''
  })
  
  const [vms, setVms] = useState([
    {
      id: uuidv4(),
      name: 'vm-1',
      vcpu: 2,
      ram_mb: 2048,
      disk_gb: 20,
      os_image: 'ubuntu-22.04'
    }
  ])
  
  const [loading, setLoading] = useState(false)

  const osImages = [
    { value: 'ubuntu-22.04', label: 'Ubuntu 22.04 LTS' },
    { value: 'ubuntu-20.04', label: 'Ubuntu 20.04 LTS' },
    { value: 'centos-stream-9', label: 'CentOS Stream 9' },
    { value: 'debian-12', label: 'Debian 12' },
    { value: 'fedora-39', label: 'Fedora 39' },
  ]

  const vcpuOptions = [1, 2, 4, 8, 16]
  const ramOptions = [512, 1024, 2048, 4096, 8192, 16384, 32768]
  const diskOptions = [10, 20, 50, 100, 200, 500]

  const addVM = () => {
    const newVM = {
      id: uuidv4(),
      name: `vm-${vms.length + 1}`,
      vcpu: 2,
      ram_mb: 2048,
      disk_gb: 20,
      os_image: 'ubuntu-22.04'
    }
    setVms([...vms, newVM])
  }

  const removeVM = (vmId) => {
    if (vms.length > 1) {
      setVms(vms.filter(vm => vm.id !== vmId))
    }
  }

  const updateVM = (vmId, field, value) => {
    setVms(vms.map(vm => 
      vm.id === vmId ? { ...vm, [field]: value } : vm
    ))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Préparer les données pour l'API
      const payload = {
        ...labData,
        vms: vms.map(({ id, ...vm }) => vm) // Retirer l'ID temporaire
      }

      const response = await labsAPI.create(payload)
      
      toast({
        title: "Succès",
        description: "Laboratoire créé avec succès",
      })
      
      navigate(`/labs/${response.data.id}`)
    } catch (error) {
      toast({
        title: "Erreur",
        description: error.response?.data?.detail || "Impossible de créer le laboratoire",
        variant: "destructive",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Créer un nouveau laboratoire</h1>
        <p className="text-muted-foreground">
          Configurez votre laboratoire virtuel avec les machines nécessaires
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Informations générales du lab */}
        <Card>
          <CardHeader>
            <CardTitle>Informations générales</CardTitle>
            <CardDescription>
              Définissez les propriétés de base de votre laboratoire
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label htmlFor="name">Nom du laboratoire *</Label>
              <Input
                id="name"
                value={labData.name}
                onChange={(e) => setLabData({ ...labData, name: e.target.value })}
                placeholder="Mon laboratoire de test"
                required
              />
            </div>
            
            <div>
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={labData.description}
                onChange={(e) => setLabData({ ...labData, description: e.target.value })}
                placeholder="Description du laboratoire..."
                rows={3}
              />
            </div>
          </CardContent>
        </Card>

        {/* Configuration des VMs */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Machines virtuelles</CardTitle>
                <CardDescription>
                  Configurez les machines virtuelles de votre laboratoire
                </CardDescription>
              </div>
              <Button type="button" onClick={addVM} variant="outline">
                <Plus className="h-4 w-4 mr-2" />
                Ajouter une VM
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {vms.map((vm, index) => (
              <div key={vm.id} className="border rounded-lg p-4 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Server className="h-4 w-4" />
                    <span className="font-medium">VM {index + 1}</span>
                  </div>
                  {vms.length > 1 && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => removeVM(vm.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  )}
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  <div>
                    <Label>Nom de la VM</Label>
                    <Input
                      value={vm.name}
                      onChange={(e) => updateVM(vm.id, 'name', e.target.value)}
                      placeholder="vm-1"
                    />
                  </div>
                  
                  <div>
                    <Label>vCPU</Label>
                    <Select
                      value={vm.vcpu.toString()}
                      onValueChange={(value) => updateVM(vm.id, 'vcpu', parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {vcpuOptions.map(option => (
                          <SelectItem key={option} value={option.toString()}>
                            {option} vCPU
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label>RAM (MB)</Label>
                    <Select
                      value={vm.ram_mb.toString()}
                      onValueChange={(value) => updateVM(vm.id, 'ram_mb', parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {ramOptions.map(option => (
                          <SelectItem key={option} value={option.toString()}>
                            {option >= 1024 ? `${option / 1024} GB` : `${option} MB`}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label>Disque (GB)</Label>
                    <Select
                      value={vm.disk_gb.toString()}
                      onValueChange={(value) => updateVM(vm.id, 'disk_gb', parseInt(value))}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {diskOptions.map(option => (
                          <SelectItem key={option} value={option.toString()}>
                            {option} GB
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div className="md:col-span-2">
                    <Label>Image OS</Label>
                    <Select
                      value={vm.os_image}
                      onValueChange={(value) => updateVM(vm.id, 'os_image', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {osImages.map(image => (
                          <SelectItem key={image.value} value={image.value}>
                            {image.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Configuration Ansible */}
        <Card>
          <CardHeader>
            <CardTitle>Configuration Ansible (optionnel)</CardTitle>
            <CardDescription>
              Collez votre playbook Ansible pour configurer automatiquement les VMs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              value={labData.ansible_config_yaml}
              onChange={(e) => setLabData({ ...labData, ansible_config_yaml: e.target.value })}
              placeholder="---
- hosts: all
  become: yes
  tasks:
    - name: Install packages
      apt:
        name:
          - nginx
          - git
        state: present"
              rows={10}
              className="font-mono text-sm"
            />
          </CardContent>
        </Card>

        {/* Boutons d'action */}
        <div className="flex justify-end space-x-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => navigate('/')}
          >
            Annuler
          </Button>
          <Button type="submit" disabled={loading}>
            {loading ? 'Création...' : 'Créer le laboratoire'}
          </Button>
        </div>
      </form>
    </div>
  )
}

export default CreateLab

