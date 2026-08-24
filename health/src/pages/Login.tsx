import React from 'react';
import { Form, Input, Button, Checkbox, Card, message, Divider } from 'antd';
import { UserOutlined, LockOutlined, MobileOutlined, KeyOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

const Login: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(false);
  const [adminLoading, setAdminLoading] = React.useState(false);

  const onFinish = async (values: any) => {
    setLoading(true);
    const { phone, password } = values;
    // Reconstruct email from phone
    const email = `${phone}@health.local`;

    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);

    if (error) {
      // Improve error message for user context
      if (error.message.includes('Invalid login credentials')) {
        message.error('手机号或密码错误');
      } else {
        message.error(error.message);
      }
    } else {
      message.success('登录成功');
      navigate('/');
    }
  };

  const handleAdminLogin = async () => {
    setAdminLoading(true);
    
    // Mock Admin User Data
    const mockUser = {
        id: 'mock-admin-id',
        email: 'admin@health.local',
        phone: '13800138000',
        role: 'admin',
        created_at: new Date().toISOString(),
        last_sign_in_at: new Date().toISOString(),
        user_metadata: {
            name: '超级管理员',
            role: 'admin'
        }
    };

    // Store in localStorage to simulate session
    localStorage.setItem('health_agent_demo_user', JSON.stringify({ user: mockUser }));
    
    // Simulate network delay
    setTimeout(() => {
        message.success('管理员免密登录成功 (开发模式)');
        setAdminLoading(false);
        navigate('/');
    }, 800);
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' }}>
      <Card title="大健康养生专家 Agent - 登录" style={{ width: 400 }}>
        <Form
          name="normal_login"
          className="login-form"
          initialValues={{ remember: true }}
          onFinish={onFinish}
        >
          <Form.Item
            name="phone"
            rules={[{ required: true, message: '请输入手机号!' }]}
          >
            <Input prefix={<MobileOutlined className="site-form-item-icon" />} placeholder="手机号" />
          </Form.Item>
          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码!' }]}
          >
            <Input
              prefix={<LockOutlined className="site-form-item-icon" />}
              type="password"
              placeholder="密码"
            />
          </Form.Item>
          <Form.Item>
            <Form.Item name="remember" valuePropName="checked" noStyle>
              <Checkbox>记住我</Checkbox>
            </Form.Item>

            <a className="login-form-forgot" href="">
              忘记密码
            </a>
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" className="login-form-button" style={{ width: '100%' }} loading={loading}>
              登录
            </Button>
            <div style={{ marginTop: 12, textAlign: 'center' }}>
                Or <a href="/register">现在注册!</a>
            </div>
          </Form.Item>
        </Form>
        
        <Divider plain>开发者通道</Divider>
        
        <Button 
            block 
            icon={<KeyOutlined />} 
            onClick={handleAdminLogin}
            loading={adminLoading}
            style={{ backgroundColor: '#52c41a', color: '#fff', borderColor: '#52c41a' }}
        >
            管理员一键通行 (免Supabase)
        </Button>
      </Card>
    </div>
  );
};

export default Login;
