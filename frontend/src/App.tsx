import { Routes, Route, Navigate } from 'react-router-dom'
import AppLayout from './components/Layout'
import Home from './pages/Home'
import Proyecto from './pages/Proyecto'
import Equipos from './pages/Equipos'
import ManoDeObra from './pages/ManoDeObra'
import Materiales from './pages/Materiales'
import Combustibles from './pages/Combustibles'
import Subcontratos from './pages/Subcontratos'
import Auxiliares from './pages/Auxiliares'
import Items from './pages/Items'
import GastosGenerales from './pages/GastosGenerales'
import Presupuesto from './pages/Presupuesto'
import ImportarExcel from './pages/ImportarExcel'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/p/:id" element={<AppLayout />}>
        <Route index element={<Navigate to="proyecto" replace />} />
        <Route path="proyecto" element={<Proyecto />} />
        <Route path="equipos" element={<Equipos />} />
        <Route path="mo" element={<ManoDeObra />} />
        <Route path="materiales" element={<Materiales />} />
        <Route path="combustibles" element={<Combustibles />} />
        <Route path="subcontratos" element={<Subcontratos />} />
        <Route path="auxiliares" element={<Auxiliares />} />
        <Route path="items" element={<Items />} />
        <Route path="gg" element={<GastosGenerales />} />
        <Route path="presupuesto" element={<Presupuesto />} />
        <Route path="importar" element={<ImportarExcel />} />
      </Route>
    </Routes>
  )
}
