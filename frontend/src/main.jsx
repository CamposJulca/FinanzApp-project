import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'

// Django sirve la SPA bajo /transacciones/, así que el router trabaja con ese
// prefijo y las rutas de cada módulo quedan relativas a él.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter basename="/transacciones">
      <App />
    </BrowserRouter>
  </StrictMode>,
)
