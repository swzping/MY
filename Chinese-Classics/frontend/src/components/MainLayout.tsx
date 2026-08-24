import React from 'react';
import { Layout, Menu, Button, theme, Dropdown, Avatar, Breadcrumb } from 'antd';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { Home, MessageCircle, User, Settings, BookOpen, ChevronDown, Bell } from 'lucide-react';
import { motion } from 'framer-motion';

const { Header, Content, Sider } = Layout;

const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    token: { borderRadiusLG },
  } = theme.useToken();

  const menuItems = [
    {
      key: '/',
      icon: <Home size={20} />,
      label: '首页',
    },
    {
      key: '/chat',
      icon: <MessageCircle size={20} />,
      label: '智能咨询',
    },
    {
      key: '/history',
      icon: <BookOpen size={20} />,
      label: '历史记录',
    },
    {
      key: '/profile',
      icon: <User size={20} />,
      label: '个人中心',
    },
  ];

  const userMenu = [
    {
      key: 'profile',
      label: '个人资料',
    },
    {
      key: 'settings',
      label: '系统设置',
    },
    {
      key: 'logout',
      label: '退出登录',
      danger: true,
    },
  ];

  // Map path to breadcrumb name
  const breadcrumbNameMap: Record<string, string> = {
    '/': '首页',
    '/chat': '智能咨询',
    '/history': '历史记录',
    '/profile': '个人中心',
  };

  const pathSnippets = location.pathname.split('/').filter((i) => i);
  const breadcrumbItems = [
    {
      title: <Link to="/">首页</Link>,
    },
    ...pathSnippets.map((_, index) => {
      const url = `/${pathSnippets.slice(0, index + 1).join('/')}`;
      return {
        title: <Link to={url}>{breadcrumbNameMap[url] || url}</Link>,
      };
    }),
  ];

  return (
    <Layout className="min-h-screen bg-[#121212]">
      <Sider
        breakpoint="lg"
        collapsedWidth="0"
        width={260}
        className="!border-r !border-white/5 !bg-[#1a1a1a]/80 backdrop-blur-md z-50"
        trigger={null}
      >
        <div className="h-24 flex items-center justify-center border-b border-white/5">
          <motion.div 
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center"
          >
            <h1 className="text-2xl font-serif text-[#FFD700] font-bold tracking-[0.2em] drop-shadow-[0_2px_10px_rgba(255,215,0,0.3)]">
              国学命理
            </h1>
            <span className="text-[10px] text-gray-500 tracking-[0.3em] uppercase mt-2 font-light">
              Chinese Classics
            </span>
          </motion.div>
        </div>
        
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
          className="!bg-transparent mt-8 px-4 border-none"
        />
        
        <div className="absolute bottom-0 w-full p-8 text-center">
           <div className="w-12 h-[2px] bg-[#C41E3A] mx-auto mb-6 opacity-50"></div>
           <p className="text-xs text-gray-600 font-serif leading-relaxed italic">
             "天行健，君子以自强不息"
           </p>
        </div>
      </Sider>
      
      <Layout className="bg-transparent">
        <Header className="!bg-[#1a1a1a]/60 backdrop-blur-md !px-8 flex items-center justify-between h-20 sticky top-0 z-40 border-b border-white/5 transition-all duration-300">
          <div className="flex flex-col">
             <Breadcrumb items={breadcrumbItems} className="!text-gray-500 text-sm" separator=">" />
             <h2 className="text-[#E0E0E0] text-xl font-serif tracking-wide mt-1">
              {menuItems.find((item) => item.key === location.pathname)?.label || '国学命理智能体'}
            </h2>
          </div>
          
          <div className="flex items-center gap-6">
            <Button 
              type="text" 
              className="!text-gray-400 hover:!text-[#FFD700] hover:!bg-white/5 rounded-full w-10 h-10 flex items-center justify-center transition-all"
            >
              <Bell size={20} />
            </Button>
            <Button 
              type="text" 
              className="!text-gray-400 hover:!text-[#FFD700] hover:!bg-white/5 rounded-full w-10 h-10 flex items-center justify-center transition-all"
            >
              <Settings size={20} />
            </Button>
            
            <div className="h-8 w-[1px] bg-white/10 mx-2"></div>

            <Dropdown menu={{ items: userMenu }} placement="bottomRight" trigger={['click']}>
              <div className="flex items-center gap-3 cursor-pointer hover:bg-white/5 py-2 px-3 rounded-full transition-all border border-transparent hover:border-white/10">
                <Avatar 
                  style={{ backgroundColor: '#C41E3A', verticalAlign: 'middle' }} 
                  size="default"
                  className="shadow-lg ring-2 ring-[#1a1a1a]"
                >
                  U
                </Avatar>
                <div className="hidden md:block text-right mr-1">
                  <div className="text-sm text-[#E0E0E0] font-medium leading-tight">Guest User</div>
                  <div className="text-[10px] text-[#FFD700] uppercase tracking-wider">VIP Level 1</div>
                </div>
                <ChevronDown size={14} className="text-gray-500" />
              </div>
            </Dropdown>
          </div>
        </Header>
        
        <Content className="p-6 md:p-8 overflow-y-auto overflow-x-hidden scroll-smooth">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            style={{
              minHeight: 280,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </motion.div>
        </Content>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
