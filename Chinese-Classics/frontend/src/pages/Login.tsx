import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, Form, Input, Button, Tabs, Typography, message } from 'antd';
import { User, Lock, Mail, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text } = Typography;

const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login, register } = useAuth();
  const [activeTab, setActiveTab] = useState('login');
  const [loading, setLoading] = useState(false);
  const [loginForm] = Form.useForm();
  const [registerForm] = Form.useForm();

  const handleLogin = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (values: {
    username: string;
    password: string;
    confirmPassword: string;
    email?: string;
    nickname?: string;
  }) => {
    if (values.password !== values.confirmPassword) {
      message.error('两次输入的密码不一致');
      return;
    }

    setLoading(true);
    try {
      await register({
        username: values.username,
        password: values.password,
        email: values.email,
        nickname: values.nickname || values.username,
      });
      navigate('/');
    } catch (error: any) {
      message.error(error.message || '注册失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 relative overflow-hidden">
      {/* 背景装饰 */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 left-10 w-72 h-72 bg-[#C41E3A] opacity-10 rounded-full blur-[100px]"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-[#FFD700] opacity-10 rounded-full blur-[100px]"></div>
      </div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md relative z-10"
      >
        <Card
          className="shadow-2xl border-0"
          style={{
            background: 'linear-gradient(135deg, #1a1a2e 0%, #2C2C2C 100%)',
            border: '1px solid rgba(196, 30, 58, 0.3)',
          }}
        >
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-[#C41E3A] to-[#FFD700] mb-4">
              <Sparkles className="w-8 h-8 text-white" />
            </div>
            <Title level={2} className="!text-[#E0E0E0] !mb-2 font-serif">
              国学命理
            </Title>
            <Text className="text-gray-500">
              探索传统智慧，指引现代生活
            </Text>
          </div>

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            centered
            className="auth-tabs"
          >
            <Tabs.TabPane tab="登录" key="login">
              <Form
                form={loginForm}
                onFinish={handleLogin}
                layout="vertical"
                className="mt-6"
              >
                <Form.Item
                  name="username"
                  rules={[{ required: true, message: '请输入用户名' }]}
                >
                  <Input
                    prefix={<User className="text-gray-500" size={16} />}
                    placeholder="用户名"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[{ required: true, message: '请输入密码' }]}
                >
                  <Input.Password
                    prefix={<Lock className="text-gray-500" size={16} />}
                    placeholder="密码"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    loading={loading}
                    block
                    style={{
                      background: 'linear-gradient(135deg, #C41E3A 0%, #FFD700 100%)',
                      border: 'none',
                    }}
                  >
                    登录
                  </Button>
                </Form.Item>
              </Form>
            </Tabs.TabPane>

            <Tabs.TabPane tab="注册" key="register">
              <Form
                form={registerForm}
                onFinish={handleRegister}
                layout="vertical"
                className="mt-6"
              >
                <Form.Item
                  name="username"
                  rules={[
                    { required: true, message: '请输入用户名' },
                    { min: 3, message: '用户名至少3个字符' },
                  ]}
                >
                  <Input
                    prefix={<User className="text-gray-500" size={16} />}
                    placeholder="用户名"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item
                  name="nickname"
                >
                  <Input
                    prefix={<User className="text-gray-500" size={16} />}
                    placeholder="昵称（可选）"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item
                  name="email"
                  rules={[{ type: 'email', message: '请输入有效的邮箱' }]}
                >
                  <Input
                    prefix={<Mail className="text-gray-500" size={16} />}
                    placeholder="邮箱（可选）"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item
                  name="password"
                  rules={[
                    { required: true, message: '请输入密码' },
                    { min: 6, message: '密码至少6个字符' },
                  ]}
                >
                  <Input.Password
                    prefix={<Lock className="text-gray-500" size={16} />}
                    placeholder="密码"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item
                  name="confirmPassword"
                  rules={[
                    { required: true, message: '请确认密码' },
                  ]}
                >
                  <Input.Password
                    prefix={<Lock className="text-gray-500" size={16} />}
                    placeholder="确认密码"
                    size="large"
                    className="!bg-white/5 !border-white/10 !text-[#E0E0E0] placeholder:text-gray-600"
                  />
                </Form.Item>

                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    size="large"
                    loading={loading}
                    block
                    style={{
                      background: 'linear-gradient(135deg, #C41E3A 0%, #FFD700 100%)',
                      border: 'none',
                    }}
                  >
                    注册
                  </Button>
                </Form.Item>
              </Form>
            </Tabs.TabPane>
          </Tabs>

          <div className="text-center mt-6">
            <Text className="text-gray-500 text-sm">
              注册即表示同意我们的
              <a href="#" className="text-[#FFD700] hover:text-[#C41E3A] mx-1">
                服务条款
              </a>
              和
              <a href="#" className="text-[#FFD700] hover:text-[#C41E3A] mx-1">
                隐私政策
              </a>
            </Text>
          </div>
        </Card>
      </motion.div>
    </div>
  );
};

export default Login;
