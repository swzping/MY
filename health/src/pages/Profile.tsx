import React, { useEffect, useState } from 'react';
import { Card, Descriptions, Button, Avatar } from 'antd';
import { UserOutlined } from '@ant-design/icons';
import { supabase } from '../lib/supabase';
import { useNavigate } from 'react-router-dom';

const Profile: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    const getUser = async () => {
      // 1. Check for mock session first
      const mockSession = localStorage.getItem('health_agent_demo_user');
      if (mockSession) {
          const session = JSON.parse(mockSession);
          setUser(session.user);
          setLoading(false);
          return;
      }

      // 2. Check for Supabase session
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        navigate('/login');
        return;
      }
      
      setUser(user);
      setLoading(false);
    };

    getUser();
  }, [navigate]);

  const handleLogout = async () => {
    if (localStorage.getItem('health_agent_demo_user')) {
        localStorage.removeItem('health_agent_demo_user');
        navigate('/login');
        return;
    }
    await supabase.auth.signOut();
    navigate('/login');
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return (
    <div>
      <h2>个人中心</h2>
      <Card>
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 24 }}>
          <Avatar size={64} icon={<UserOutlined />} />
          <div style={{ marginLeft: 16 }}>
            <h3>{user.email}</h3>
            <p>{user.user_metadata?.role === 'admin' ? '超级管理员' : '普通会员'}</p>
          </div>
        </div>
        
        <Descriptions title="基本信息" bordered>
          <Descriptions.Item label="邮箱">{user.email}</Descriptions.Item>
          <Descriptions.Item label="注册时间">{new Date(user.created_at).toLocaleDateString()}</Descriptions.Item>
          <Descriptions.Item label="上次登录">{new Date(user.last_sign_in_at).toLocaleString()}</Descriptions.Item>
        </Descriptions>

        <div style={{ marginTop: 24 }}>
          <Button type="primary" onClick={() => {}}>编辑资料</Button>
          <Button style={{ marginLeft: 8 }} danger onClick={handleLogout}>退出登录</Button>
        </div>
      </Card>
    </div>
  );
};

export default Profile;
