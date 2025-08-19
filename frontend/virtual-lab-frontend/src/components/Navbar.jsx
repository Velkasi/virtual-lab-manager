import { Link, useLocation } from 'react-router-dom'
import { Button } from './ui/button'
import { Server, Plus, Home } from 'lucide-react'

const Navbar = () => {
  const location = useLocation()

  return (
    <nav className="border-b bg-card">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center space-x-2">
            <Server className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold">Virtual Lab Manager</span>
          </Link>
          
          <div className="flex items-center space-x-4">
            <Button
              variant={location.pathname === '/' ? 'default' : 'ghost'}
              asChild
            >
              <Link to="/" className="flex items-center space-x-2">
                <Home className="h-4 w-4" />
                <span>Tableau de bord</span>
              </Link>
            </Button>
            
            <Button
              variant={location.pathname === '/create-lab' ? 'default' : 'ghost'}
              asChild
            >
              <Link to="/create-lab" className="flex items-center space-x-2">
                <Plus className="h-4 w-4" />
                <span>Créer un Lab</span>
              </Link>
            </Button>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar

