import { Routes, Route } from 'react-router-dom'
import GuardianIDLoginPage from './components/GuardianIDPage'
import FigmaNode21790_516517 from './components/FigmaNode21790_516517'

function App() {
  return (
    <Routes>
      <Route path="/" element={<GuardianIDLoginPage />} />
      {/* Figma node 21790-516517 route - Product Detail Page (PDP) */}
      <Route path="/node-21790-516517" element={<FigmaNode21790_516517 />} />
    </Routes>
  )
}

export default App