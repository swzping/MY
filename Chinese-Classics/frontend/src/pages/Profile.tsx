import React, { useState, useEffect } from 'react';
import { Card, Avatar, List, Typography, Button, Tabs, Spin, Empty } from 'antd';
import { User, Crown, Settings, LogOut, Clock, Bookmark, Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { historyApi, History } from '../services/api';

const { Title, Text } = Typography;

const Profile: React.FC = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [histories, setHistories] = useState<History[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({ total: 0, by_type: {} });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    fetchHistories();
  }, [isAuthenticated]);

  const fetchHistories = async () => {
    try {
      const [historiesRes, statsRes] = await Promise.all([
        historyApi.getHistories({ page_size: 10 }),
        historyApi.getStats()
      ]);
      setHistories(historiesRes.data.items || []);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch histories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
  };

  const getTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      iching: '周易占卜',
      horoscope: '星座运势',
      zodiac: '生肖配对',
      bazi: '八字命理',
      naming: '起名建议',
    };
    return map[type] || type;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  if (!user) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spin size="large" />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-1 space-y-6">
          <Card 
            className="!bg-white/5 !border-white/10 text-center shadow-lg backdrop-blur-md relative overflow-hidden"
            bordered={false}
          >
            <div className="absolute top-0 left-0 w-full h-24 bg-gradient-to-b from-[#C41E3A]/20 to-transparent"></div>
            
            <div className="relative mb-6 mt-4">
              <div className="relative inline-block">
                <Avatar 
                  size={100} 
                  className="bg-[#C41E3A] text-3xl border-4 border-[#1F1F1F] shadow-xl" 
                  icon={<User />} 
                  src={user.avatar}
                />
                {user.is_vip && (
                  <div className="absolute -bottom-2 -right-2 bg-[#FFD700] text-black text-xs px-3 py-1 rounded-full font-bold flex items-center gap-1 shadow-lg border border-[#1F1F1F]">
                    <Crown size={12} fill="black" /> {user.vip_level || 'VIP'}
                  </div>
                )}
              </div>
            </div>
            
            <Title level={3} className="!mb-1 !text-[#E0E0E0] font-serif">{user.nickname || user.username}</Title>
            <Text className="text-gray-500">ID: {user.id.toString().padStart(8, '0')}</Text>
            
            <div className="mt-8 flex justify-around border-t border-white/10 pt-6">
              <div className="text-center group cursor-pointer">
                <div className="text-2xl font-bold text-[#FFD700] group-hover:text-[#C41E3A] transition-colors">{user.credits || 0}</div>
                <div className="text-xs text-gray-500 mt-1 uppercase tracking-wider">积分</div>
              </div>
              <div className="text-center group cursor-pointer">
                <div className="text-2xl font-bold text-[#FFD700] group-hover:text-[#C41E3A] transition-colors">{stats.total}</div>
                <div className="text-xs text-gray-500 mt-1 uppercase tracking-wider">咨询</div>
              </div>
              <div className="text-center group cursor-pointer">
                <div className="text-2xl font-bold text-[#FFD700] group-hover:text-[#C41E3A] transition-colors">0</div>
                <div className="text-xs text-gray-500 mt-1 uppercase tracking-wider">收藏</div>
              </div>
            </div>
          </Card>

          <Card className="!bg-white/5 !border-white/10 shadow-lg backdrop-blur-md" bordered={false}>
            <List split={false}>
              <List.Item 
                className="!cursor-pointer hover:!bg-white/5 !rounded-lg !px-3 !transition-all !border-b-0 group mb-1"
                onClick={() => navigate('/settings')}
              >
                <div className="flex items-center gap-4 text-[#E0E0E0] group-hover:text-[#FFD700] transition-colors w-full py-1">
                  <Settings size={20} className="text-gray-500 group-hover:text-[#FFD700] transition-colors" />
                  <span className="text-base">系统设置</span>
                </div>
              </List.Item>
              <List.Item 
                className="!cursor-pointer hover:!bg-red-900/20 !rounded-lg !px-3 !transition-all !border-b-0 group mt-1"
                onClick={handleLogout}
              >
                <div className="flex items-center gap-4 text-[#E0E0E0] group-hover:text-[#C41E3A] transition-colors w-full py-1">
                  <LogOut size={20} className="text-gray-500 group-hover:text-[#C41E3A] transition-colors" />
                  <span className="text-base">退出登录</span>
                </div>
              </List.Item>
            </List>
          </Card>
        </div>

        <div className="md:col-span-2">
          <Card 
            className="!bg-white/5 !border-white/10 shadow-lg h-full backdrop-blur-md" 
            bordered={false}
            bodyStyle={{ padding: '0 24px 24px' }}
          >
            <Tabs
              defaultActiveKey="1"
              size="large"
              tabBarStyle={{ borderBottom: '1px solid rgba(255,255,255,0.1)', marginBottom: 24 }}
              items={[
                {
                  key: '1',
                  label: (
                    <span className="flex items-center gap-2 text-base px-2">
                      <Clock size={18} /> 历史记录
                    </span>
                  ),
                  children: loading ? (
                    <div className="flex justify-center py-12">
                      <Spin />
                    </div>
                  ) : histories.length === 0 ? (
                    <Empty 
                      description="暂无咨询记录" 
                      className="py-12"
                      image={Empty.PRESENTED_IMAGE_SIMPLE}
                    />
                  ) : (
                    <List
                      itemLayout="horizontal"
                      dataSource={histories}
                      className="profile-list"
                      renderItem={(item) => (
                        <List.Item
                          actions={[
                            <Button 
                              type="link" 
                              className="!text-[#FFD700] hover:!text-[#C41E3A]"
                              onClick={() => navigate(`/report/${item.id}`)}
                            >
                              查看详情
                            </Button>
                          ]}
                          className="hover:!bg-white/5 !transition-all !rounded-xl !px-4 !py-4 !mb-3 !border-b-0"
                        >
                          <List.Item.Meta
                            avatar={
                              <div className="bg-[#C41E3A]/10 p-3 rounded-xl text-[#C41E3A]">
                                <Star size={24} />
                              </div>
                            }
                            title={
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-lg font-serif text-[#E0E0E0]">{getTypeLabel(item.type)}</span>
                                <Text className="!text-gray-500 text-xs font-normal bg-white/5 px-2 py-1 rounded">
                                  {formatDate(item.created_at)}
                                </Text>
                              </div>
                            }
                            description={
                              <Text className="!text-gray-400 block mt-1 text-base truncate pr-4">
                                {item.question}
                              </Text>
                            }
                          />
                        </List.Item>
                      )}
                    />
                  ),
                },
                {
                  key: '2',
                  label: (
                    <span className="flex items-center gap-2 text-base px-2">
                      <Bookmark size={18} /> 我的收藏
                    </span>
                  ),
                  children: (
                    <div className="flex flex-col items-center justify-center py-20 text-gray-500 bg-white/5 rounded-2xl border border-dashed border-white/10 mx-4">
                      <div className="bg-white/5 p-6 rounded-full mb-4">
                        <Bookmark size={48} className="text-gray-600 opacity-50" />
                      </div>
                      <p className="text-lg">暂无收藏内容</p>
                      <p className="text-sm opacity-60">您收藏的命理报告将显示在这里</p>
                    </div>
                  ),
                },
              ]}
            />
          </Card>
        </div>
      </div>
    </div>
  );
};

export default Profile;
