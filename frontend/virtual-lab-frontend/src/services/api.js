import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Labs API
export const labsAPI = {
  // Récupérer tous les labs
  getAll: () => api.get('/labs'),
  
  // Récupérer un lab par ID
  getById: (id) => api.get(`/labs/${id}`),
  
  // Créer un nouveau lab
  create: (labData) => api.post('/labs', labData),
  
  // Supprimer un lab
  delete: (id) => api.delete(`/labs/${id}`),
  
  // Déployer un lab
  deploy: (id) => api.post(`/labs/${id}/deploy`),
  
  // Récupérer les logs d'un lab
  getLogs: (id) => api.get(`/labs/${id}/logs`),
}

// VMs API
export const vmsAPI = {
  // Récupérer toutes les VMs (optionnellement filtrées par lab_id)
  getAll: (labId = null) => {
    const params = labId ? { lab_id: labId } : {}
    return api.get('/vms', { params })
  },
  
  // Récupérer une VM par ID
  getById: (id) => api.get(`/vms/${id}`),
  
  // Démarrer une VM
  start: (id) => api.post(`/vms/${id}/start`),
  
  // Arrêter une VM
  stop: (id) => api.post(`/vms/${id}/stop`),
  
  // Redémarrer une VM
  restart: (id) => api.post(`/vms/${id}/restart`),
  
  // Récupérer les informations de connexion SSH
  getSSHAccess: (id) => api.get(`/vms/${id}/ssh_access`),
  
  // Récupérer les informations de connexion VNC
  getVNCAccess: (id) => api.get(`/vms/${id}/vnc_access`),
}

export default api

