import { ConfigProvider, theme } from 'antd'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import MainLayout from './components/MainLayout'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Profile from './pages/Profile'
import Login from './pages/Login'
import Settings from './pages/Settings'
import ReportView from './pages/ReportView'

function App() {
  console.log('App rendering...')
  
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#C41E3A',
          colorLink: '#FFD700',
          borderRadius: 4,
          fontFamily: '"Noto Serif SC", "SimSun", serif',
          colorBgContainer: '#1F1F1F',
          colorBgLayout: 'transparent',
        },
        components: {
          Button: {
            colorPrimary: '#C41E3A',
            algorithm: true,
            primaryShadow: '0 2px 0 rgba(0,0,0,0.045)',
          },
          Layout: {
            headerBg: 'transparent',
            bodyBg: 'transparent',
            siderBg: '#1F1F1F',
          },
          Menu: {
            darkItemBg: 'transparent',
          }
        }
      }}
    >
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/report/:id" element={<ReportView />} />
          <Route path="/share/:code" element={<ReportView />} />
          
          <Route path="/" element={<MainLayout />}>
            <Route index element={<Home />} />
            <Route path="chat" element={<Chat />} />
            <Route path="profile" element={<Profile />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </Router>
    </ConfigProvider>
  )
}

export default App
