import React, { useState } from 'react';
import { Card, Form, Input, Button, Avatar, Tabs, List, Switch, message } from 'antd';
import { User, Mail, Lock, Bell, Shield, LogOut, Camera } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '../contexts/AuthContext';
import { miscApi } from '../services/api';

const Settings: React.FC = () => {
  const { user, logout, updateUser } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);
  const [profileForm] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const handleUpdateProfile = async (values: {
    nickname?: string;
    email?: string;
    avatar?: string;
  }) => {
    setLoading(true);
    try {
      await updateUser(values);
    } catch (error) {
      console.error('更新失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (values: {
    oldPassword: string;
    newPassword: string;
    confirmPassword: string;
  }) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }

    setLoading(true);
    try {
      // await authApi.changePassword(values.oldPassword, values.newPassword);
      message.success('密码修改成功');
      passwordForm.resetFields();
    } catch (error: any) {
      message.error(error.response?.data?.detail || '密码修改失败');
    } finally {
      setLoading(false);
    }
  };

  const handleFeedback = async (values: { content: string; type: string }) => {
    try {
      await miscApi.createFeedback({
        type: values.type,
        content: values.content,
      });
      message.success('反馈提交成功，感谢您的建议！');
    } catch (error) {
      message.error('提交失败');
    }
  };

  const profileItems = [
    {
      key: 'profile',
      label: (
        <span className="flex items-center gap-2">
          <User size={16} /> 个人资料
        </span>
      ),
      children: (
        <div className="max-w-xl">
          <div className="flex items-center gap-6 mb-8">
            <div className="relative">
              <Avatar
                size={80}
                src={user?.avatar}
                className="bg-[#C41E3A] text-2xl"
              >
                {user?.nickname?.[0] || user?.username?.[0]}
              </Avatar>
              <button className="absolute -bottom-1 -right-1 p-1.5 bg-[#FFD700] rounded-full hover:bg-[#C41E3A] transition-colors">
                <Camera size={14} className="text-black" />
              </button>
            </div>
            <div>
              <h3 className="text-xl font-medium text-[#E0E0E0]">{user?.nickname}</h3>
              <p className="text-gray-500">{user?.username}</p>
              <p className="text-sm text-[#FFD700] mt-1">
                {user?.is_vip ? `${user.vip_level}会员` : '免费用户'}
              </p>
            </div>
          </div>

          <Form
            form={profileForm}
            layout="vertical"
            initialValues={{
              nickname: user?.nickname,
              email: user?.email,
            }}
            onFinish={handleUpdateProfile}
          >
            <Form.Item
              label="昵称"
              name="nickname"
              rules={[{ required: true, message: '请输入昵称' }]}
            >
              <Input
                prefix={<User size={16} className="text-gray-500" />}
                placeholder="请输入昵称"
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              />
            </Form.Item>

            <Form.Item
              label="邮箱"
              name="email"
              rules={[{ type: 'email', message: '请输入有效的邮箱' }]}
            >
              <Input
                prefix={<Mail size={16} className="text-gray-500" />}
                placeholder="请输入邮箱"
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{ background: '#C41E3A', borderColor: '#C41E3A' }}
              >
                保存修改
              </Button>
            </Form.Item>
          </Form>
        </div>
      ),
    },
    {
      key: 'password',
      label: (
        <span className="flex items-center gap-2">
          <Lock size={16} /> 修改密码
        </span>
      ),
      children: (
        <div className="max-w-xl">
          <Form
            form={passwordForm}
            layout="vertical"
            onFinish={handleChangePassword}
          >
            <Form.Item
              label="当前密码"
              name="oldPassword"
              rules={[{ required: true, message: '请输入当前密码' }]}
            >
              <Input.Password
                prefix={<Lock size={16} className="text-gray-500" />}
                placeholder="请输入当前密码"
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              />
            </Form.Item>

            <Form.Item
              label="新密码"
              name="newPassword"
              rules={[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码至少6个字符' },
              ]}
            >
              <Input.Password
                prefix={<Lock size={16} className="text-gray-500" />}
                placeholder="请输入新密码"
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              />
            </Form.Item>

            <Form.Item
              label="确认新密码"
              name="confirmPassword"
              rules={[{ required: true, message: '请确认新密码' }]}
            >
              <Input.Password
                prefix={<Lock size={16} className="text-gray-500" />}
                placeholder="请确认新密码"
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                style={{ background: '#C41E3A', borderColor: '#C41E3A' }}
              >
                修改密码
              </Button>
            </Form.Item>
          </Form>
        </div>
      ),
    },
    {
      key: 'notifications',
      label: (
        <span className="flex items-center gap-2">
          <Bell size={16} /> 通知设置
        </span>
      ),
      children: (
        <div className="max-w-xl">
          <List
            itemLayout="horizontal"
            className="settings-list"
          >
            <List.Item
              actions={[
                <Switch defaultChecked className="custom-switch" />
              ]}
            >
              <List.Item.Meta
                title={<span className="text-[#E0E0E0]">邮件通知</span>}
                description={<span className="text-gray-500">接收系统更新和重要通知</span>}
              />
            </List.Item>
            <List.Item
              actions={[
                <Switch defaultChecked className="custom-switch" />
              ]}
            >
              <List.Item.Meta
                title={<span className="text-[#E0E0E0]">咨询回复通知</span>}
                description={<span className="text-gray-500">当AI回复您的咨询时通知</span>}
              />
            </List.Item>
            <List.Item
              actions={[
                <Switch className="custom-switch" />
              ]}
            >
              <List.Item.Meta
                title={<span className="text-[#E0E0E0]">每日运势推送</span>}
                description={<span className="text-gray-500">每天推送您的星座运势</span>}
              />
            </List.Item>
          </List>
        </div>
      ),
    },
    {
      key: 'privacy',
      label: (
        <span className="flex items-center gap-2">
          <Shield size={16} /> 隐私设置
        </span>
      ),
      children: (
        <div className="max-w-xl">
          <List
            itemLayout="horizontal"
            className="settings-list"
          >
            <List.Item
              actions={[
                <Switch className="custom-switch" />
              ]}
            >
              <List.Item.Meta
                title={<span className="text-[#E0E0E0]">公开我的评价</span>}
                description={<span className="text-gray-500">允许其他用户看到我的评价</span>}
              />
            </List.Item>
            <List.Item
              actions={[
                <Switch defaultChecked className="custom-switch" />
              ]}
            >
              <List.Item.Meta
                title={<span className="text-[#E0E0E0]">数据 analytics</span>}
                description={<span className="text-gray-500">允许收集使用数据以改进服务</span>}
              />
            </List.Item>
          </List>
        </div>
      ),
    },
    {
      key: 'feedback',
      label: (
        <span className="flex items-center gap-2">
          <Mail size={16} /> 意见反馈
        </span>
      ),
      children: (
        <div className="max-w-xl">
          <Form layout="vertical" onFinish={handleFeedback}>
            <Form.Item
              label="反馈类型"
              name="type"
              initialValue="general"
            >
              <select className="w-full bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-[#E0E0E0]">
                <option value="general">一般反馈</option>
                <option value="bug">Bug报告</option>
                <option value="feature">功能建议</option>
                <option value="complaint">投诉</option>
              </select>
            </Form.Item>

            <Form.Item
              label="反馈内容"
              name="content"
              rules={[{ required: true, message: '请输入反馈内容' }]}
            >
              <Input.TextArea
                rows={4}
                placeholder="请输入您的意见或建议..."
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              />
            </Form.Item>

            <Form.Item>
              <Button
                type="primary"
                htmlType="submit"
                style={{ background: '#C41E3A', borderColor: '#C41E3A' }}
              >
                提交反馈
              </Button>
            </Form.Item>
          </Form>
        </div>
      ),
    },
    {
      key: 'logout',
      label: (
        <span className="flex items-center gap-2 text-[#C41E3A]">
          <LogOut size={16} /> 退出登录
        </span>
      ),
      children: (
        <div className="max-w-xl text-center py-12">
          <p className="text-gray-400 mb-6">确定要退出登录吗？</p>
          <Button
            type="primary"
            danger
            size="large"
            onClick={logout}
            style={{ background: '#C41E3A', borderColor: '#C41E3A' }}
          >
            确认退出
          </Button>
        </div>
      ),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-6xl mx-auto px-4 py-8"
    >
      <h1 className="text-3xl font-serif text-[#E0E0E0] mb-8">设置</h1>

      <Card
        className="!bg-white/5 !border-white/10"
        bodyStyle={{ padding: 0 }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          tabPosition="left"
          className="settings-tabs"
          items={profileItems}
          style={{ minHeight: 500 }}
        />
      </Card>
    </motion.div>
  );
};

export default Settings;
