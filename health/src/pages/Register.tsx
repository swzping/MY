import React from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

const Register: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = React.useState(false);

  const onFinish = async (values: any) => {
    setLoading(true);
    const { password, name, phone } = values;
    // Auto-generate email from phone for Supabase Auth requirement
    const email = `${phone}@health.local`;
    
    // Sign up with Supabase Auth
    const { data: authData, error: authError } = await supabase.auth.signUp({
      email,
      password,
    });

    if (authError) {
      if (authError.message.includes('rate limit')) {
        message.error('注册过于频繁，请稍后再试。如果您是开发者，请在 Supabase 控制台关闭邮件验证或检查频率限制。');
      } else {
        message.error(authError.message);
      }
      setLoading(false);
      return;
    }

    if (authData.user) {
      // Create user profile in public.users table
      const { error: profileError } = await supabase
        .from('users')
        .insert([
          { 
            id: authData.user.id, // Link to auth.users.id
            email, // Store the generated email or null if you prefer, but schema has unique constraint
            name, 
            phone,
            password_hash: 'managed_by_supabase_auth' // Placeholder as auth handles password
          },
        ]);

      if (profileError) {
        message.error('注册成功，但在创建个人资料时出错: ' + profileError.message);
      } else {
        message.success('注册成功！');
        navigate('/login');
      }
    }
    
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' }}>
      <Card title="大健康养生专家 Agent - 注册" style={{ width: 400 }}>
        <Form
          name="register"
          onFinish={onFinish}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="昵称"
            rules={[{ required: true, message: '请输入您的昵称!', whitespace: true }]}
          >
            <Input />
          </Form.Item>
          
          <Form.Item
            name="phone"
            label="手机号"
            rules={[{ required: true, message: '请输入您的手机号!' }]}
          >
            <Input />
          </Form.Item>

          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码!' },
              { min: 6, message: '密码长度至少6位' }
            ]}
            hasFeedback
          >
            <Input.Password />
          </Form.Item>

          <Form.Item
            name="confirm"
            label="确认密码"
            dependencies={['password']}
            hasFeedback
            rules={[
              { required: true, message: '请再次确认密码!' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致!'));
                },
              }),
            ]}
          >
            <Input.Password />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" style={{ width: '100%' }} loading={loading}>
              注册
            </Button>
            已有账号? <a href="/login">去登录</a>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default Register;
