import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, Avatar, Spin, Typography } from 'antd';
import { Send, Bot, User, Sparkles } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import { fetchEventSource } from '@microsoft/fetch-event-source';

const { Content, Footer } = Layout;
const { Text } = Typography;

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

const Chat: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialType = searchParams.get('type');
  
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: `您好！我是您的国学命理助手。${initialType ? `我看到您对**${getFeatureName(initialType)}**感兴趣。` : ''} 请问有什么可以帮您？`,
      timestamp: Date.now(),
    },
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  function getFeatureName(type: string | null) {
    const map: Record<string, string> = {
      iching: '周易占卜',
      horoscope: '星座运势',
      zodiac: '生肖配对',
      bazi: '八字命理',
      naming: '起名建议',
    };
    return type ? map[type] || '命理咨询' : '命理咨询';
  }

  const handleSend = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    const aiMessageId = (Date.now() + 1).toString();
    let aiContent = '';

    // Initial AI message placeholder
    setMessages((prev) => [
      ...prev,
      {
        id: aiMessageId,
        role: 'assistant',
        content: '',
        timestamp: Date.now(),
      },
    ]);

    try {
      await fetchEventSource('/api/v1/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          session_id: 'default'
        }),
        onmessage(msg) {
          try {
            const data = JSON.parse(msg.data);
            if (data.type === 'token') {
              aiContent += data.content;
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === aiMessageId ? { ...m, content: aiContent } : m
                )
              );
            } else if (data.type === 'status') {
               console.log('Status:', data.content);
            } else if (data.type === 'error') {
               console.error('Stream error:', data.content);
            }
          } catch (e) {
            console.error('Error parsing stream message', e);
          }
        },
        onerror(err) {
          console.error('EventSource error:', err);
          throw err; 
        }
      });

    } catch (error) {
      console.error('Failed to send message:', error);
      setMessages((prev) =>
        prev.map((m) =>
          m.id === aiMessageId ? { ...m, content: aiContent + '\n\n[连接服务器失败，请检查后端服务是否启动]' } : m
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Layout className="h-[calc(100vh-140px)] bg-transparent">
      <Content className="overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-8">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
            >
              <Avatar
                size={42}
                className={msg.role === 'user' ? 'bg-[#C41E3A]' : 'bg-[#FFD700] text-black'}
                icon={msg.role === 'user' ? <User size={20} /> : <Bot size={20} />}
              />
              <div
                className={`max-w-[85%] rounded-2xl px-6 py-4 shadow-md ${
                  msg.role === 'user'
                    ? 'bg-[#C41E3A] text-white rounded-tr-none'
                    : 'bg-white/10 border border-white/10 text-[#E0E0E0] rounded-tl-none backdrop-blur-sm'
                }`}
              >
                <div className={`prose ${msg.role === 'user' ? 'prose-invert' : 'prose-invert'} max-w-none leading-relaxed`}>
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                </div>
              </div>
            </div>
          ))}
          {isLoading && !messages.some(m => m.role === 'assistant' && m.id > Date.now().toString() && m.content) && (
            <div className="flex gap-4">
              <Avatar size={42} className="bg-[#FFD700] text-black" icon={<Bot size={20} />} />
              <div className="bg-white/10 border border-white/10 rounded-2xl rounded-tl-none px-6 py-4 shadow-sm flex items-center gap-3 backdrop-blur-sm">
                <Spin size="small" />
                <Text className="text-gray-400">正在推演天机...</Text>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </Content>
      <Footer className="bg-transparent border-t border-white/10 p-6">
        <div className="max-w-3xl mx-auto">
          <div className="relative group">
            <div className="absolute -inset-0.5 bg-gradient-to-r from-[#C41E3A] to-[#FFD700] rounded-xl blur opacity-20 group-hover:opacity-40 transition duration-1000 group-hover:duration-200"></div>
            <div className="relative">
              <Input.TextArea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onPressEnter={(e) => {
                  if (!e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                placeholder="请输入您的疑惑，例如：最近事业运势如何？"
                autoSize={{ minRows: 1, maxRows: 4 }}
                className="!pr-14 !py-4 !rounded-xl !bg-[#1F1F1F] !border-white/10 !text-[#E0E0E0] !placeholder-gray-500 shadow-xl focus:!border-[#C41E3A] text-lg hover:!bg-[#252525] transition-colors"
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !inputValue.trim()}
                className="absolute right-3 bottom-3 p-2 text-[#FFD700] hover:bg-white/10 rounded-full transition-colors disabled:opacity-30 disabled:hover:bg-transparent"
              >
                <Send size={22} />
              </button>
            </div>
          </div>
          <div className="mt-3 text-center">
            <Text className="text-xs text-gray-500">
              <Sparkles size={12} className="inline mr-1 text-[#FFD700]" />
              AI生成内容仅供参考，请相信科学，理性看待
            </Text>
          </div>
        </div>
      </Footer>
    </Layout>
  );
};

export default Chat;
