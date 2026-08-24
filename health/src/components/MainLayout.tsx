import React, { useState } from 'react';
import { Layout, Menu, theme, Avatar, Dropdown, Button } from 'antd';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import {
  UserOutlined,
  HomeOutlined,
  MedicineBoxOutlined,
  ExperimentOutlined,
  HeartOutlined,
  ThunderboltOutlined,
  SafetyCertificateOutlined,
  LogoutOutlined,
} from '@ant-design/icons';
import { supabase } from '../lib/supabase';

const { Header, Content, Footer, Sider } = Layout;

const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogout = async () => {
    // Check if it's a mock session
    if (localStorage.getItem('health_agent_demo_user')) {
        localStorage.removeItem('health_agent_demo_user');
        navigate('/login');
        return;
    }
    
    // Otherwise sign out from Supabase
    await supabase.auth.signOut();
    navigate('/login');
  };

  const userMenu = {
    items: [
      {
        key: 'profile',
        label: <Link to="/profile">个人中心</Link>,
        icon: <UserOutlined />,
      },
      {
        key: 'logout',
        label: '退出登录',
        icon: <LogoutOutlined />,
        onClick: handleLogout,
      },
    ],
  };

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: <Link to="/">首页</Link>,
    },
    {
      key: '/tcm',
      icon: <MedicineBoxOutlined />,
      label: <Link to="/tcm">中医养生</Link>,
    },
    {
      key: '/nutrition',
      icon: <ExperimentOutlined />,
      label: <Link to="/nutrition">营养膳食</Link>,
    },
    {
      key: '/mental',
      icon: <HeartOutlined />,
      label: <Link to="/mental">心理健康</Link>,
    },
    {
      key: '/fitness',
      icon: <ThunderboltOutlined />,
      label: <Link to="/fitness">运动健身</Link>,
    },
    {
      key: '/assessment',
      icon: <SafetyCertificateOutlined />,
      label: <Link to="/assessment">健康评估</Link>,
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={(value) => setCollapsed(value)}>
        <div className="demo-logo-vertical" style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)', borderRadius: 6 }} />
        <Menu
          theme="dark"
          defaultSelectedKeys={['/']}
          selectedKeys={[location.pathname]}
          mode="inline"
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 24px', background: colorBgContainer, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2 style={{ margin: 0, color: '#1677ff' }}>大健康养生专家 Agent</h2>
          <Dropdown menu={userMenu} placement="bottomRight">
            <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
              <Avatar icon={<UserOutlined />} />
              <span>用户</span>
            </div>
          </Dropdown>
        </Header>
        <Content style={{ margin: '16px 16px' }}>
          <div
            style={{
              padding: 24,
              minHeight: 360,
              background: colorBgContainer,
              borderRadius: borderRadiusLG,
            }}
          >
            <Outlet />
          </div>
        </Content>
        <Footer style={{ textAlign: 'center' }}>
          Health & Wellness Agent ©{new Date().getFullYear()} Created by Trae AI
        </Footer>
      </Layout>
    </Layout>
  );
};

export default MainLayout;
