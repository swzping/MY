import { Suspense, lazy } from 'react';
import { Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { Compass, Star, User, Book, PenTool, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';

// Lazy load 3D components
const Scene3DBanner = lazy(() => import('../components/3d/Scene3D').then(mod => ({ default: mod.Scene3DBanner })));
const Scene3D = lazy(() => import('../components/3d/Scene3D').then(mod => ({ default: mod.Scene3D })));

const { Title, Paragraph } = Typography;

const features = [
  {
    title: '周易占卜',
    description: '六爻排盘，解析吉凶祸福',
    icon: <Compass size={40} className="text-[#C41E3A]" />,
    path: '/chat?type=iching',
    color: 'hover:border-[#C41E3A]',
    bg: 'group-hover:bg-[#C41E3A]/10',
  },
  {
    title: '星座运势',
    description: '星象奥秘，每日运势更新',
    icon: <Star size={40} className="text-[#FFD700]" />,
    path: '/chat?type=horoscope',
    color: 'hover:border-[#FFD700]',
    bg: 'group-hover:bg-[#FFD700]/10',
  },
  {
    title: '生肖配对',
    description: '传统合婚，分析性格匹配',
    icon: <User size={40} className="text-green-500" />,
    path: '/chat?type=zodiac',
    color: 'hover:border-green-500',
    bg: 'group-hover:bg-green-500/10',
  },
  {
    title: '八字命理',
    description: '四柱排盘，详批流年大运',
    icon: <Book size={40} className="text-blue-500" />,
    path: '/chat?type=bazi',
    color: 'hover:border-blue-500',
    bg: 'group-hover:bg-blue-500/10',
  },
  {
    title: '起名建议',
    description: '五行八字，定制吉祥好名',
    icon: <PenTool size={40} className="text-purple-500" />,
    path: '/chat?type=naming',
    color: 'hover:border-purple-500',
    bg: 'group-hover:bg-purple-500/10',
  },
];

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 }
};

const Home: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      {/* Hero Section */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center mb-16 relative"
      >
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-[#C41E3A] opacity-5 rounded-full blur-[100px] pointer-events-none"></div>
        <Title level={1} className="!text-5xl md:!text-6xl font-serif !mb-6 text-[#E0E0E0] tracking-wide relative z-10 drop-shadow-2xl">
          探索传统智慧，<br className="hidden sm:block" />指引现代生活
        </Title>
        <Paragraph className="text-lg md:text-xl text-gray-400 max-w-3xl mx-auto font-light leading-relaxed relative z-10">
          融合<span className="text-[#C41E3A] font-medium mx-1">周易</span>、
          <span className="text-[#FFD700] font-medium mx-1">命理</span>、
          <span className="text-green-500 font-medium mx-1">星象</span>等传统文化精髓，
          辅以现代AI技术，为您提供专业、便捷的个性化咨询服务。
        </Paragraph>
      </motion.div>

      {/* 3D Scene Banner */}
      <div className="mb-16">
        <Suspense fallback={
          <div className="w-full h-64 md:h-80 lg:h-96 bg-gradient-to-br from-[#1a1a2e] to-[#0f0f1a] rounded-2xl flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#C41E3A] mx-auto mb-4"></div>
              <p className="text-gray-400">加载 3D 场景中...</p>
            </div>
          </div>
        }>
          <Scene3DBanner />
        </Suspense>
      </div>

      {/* 3D Interactive Section */}
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.6 }}
        className="mb-20"
      >
        <div className="text-center mb-8">
          <Title level={2} className="font-serif !text-3xl !text-[#E0E0E0] !mb-3">
            <span className="text-[#C41E3A]">3D</span> 沉浸式体验
          </Title>
          <Paragraph className="text-gray-400 max-w-2xl mx-auto">
            通过现代 3D 渲染技术，将传统太极、八卦元素立体呈现。<br />
            您可以拖拽旋转、缩放查看每一个细节，感受传统文化的魅力。
          </Paragraph>
        </div>

        <Suspense fallback={
          <div className="w-full h-[500px] bg-[#1a1a2e] rounded-2xl flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#FFD700] mx-auto mb-4"></div>
              <p className="text-gray-400">加载 3D 交互场景中...</p>
            </div>
          </div>
        }>
          <Scene3D initialMode="both" height="500px" />
        </Suspense>
      </motion.div>

      {/* Core Modules Grid */}
      <motion.div 
        variants={container}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, amount: 0.2 }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 mb-20"
      >
        {features.map((feature, index) => (
          <motion.div key={index} variants={item}>
            <div
              className={`h-full relative group cursor-pointer overflow-hidden rounded-2xl bg-[#1F1F1F]/50 border border-white/5 backdrop-blur-sm transition-all duration-300 hover:border-opacity-50 ${feature.color}`}
              onClick={() => navigate(feature.path)}
            >
              <div className={`absolute inset-0 opacity-0 transition-opacity duration-300 ${feature.bg}`}></div>
              
              <div className="p-8 flex flex-col items-center text-center h-full relative z-10">
                <div className="mb-6 p-5 bg-[#2C2C2C] rounded-full shadow-lg ring-1 ring-white/10 group-hover:scale-110 transition-transform duration-300">
                  {feature.icon}
                </div>
                <Title level={3} className="!mb-3 !text-2xl font-serif !text-[#E0E0E0] group-hover:!text-[#FFD700] transition-colors">
                  {feature.title}
                </Title>
                <Paragraph className="!text-gray-400 mb-6 leading-relaxed flex-grow">
                  {feature.description}
                </Paragraph>
                
                <div className="mt-auto opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center text-[#FFD700] text-sm font-medium tracking-wider uppercase">
                  立即体验 <ArrowRight size={16} className="ml-2" />
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* CTA Section */}
      <motion.div 
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, amount: 0.3 }}
        transition={{ duration: 0.6 }}
        className="relative overflow-hidden rounded-[32px] p-[1px]"
      >
        <div className="absolute inset-0 bg-gradient-to-r from-[#C41E3A] via-[#FFD700] to-[#C41E3A] opacity-20"></div>
        <div className="relative bg-[#1a1a1a] rounded-[31px] p-12 md:p-16 text-center border border-white/5 backdrop-blur-xl">
          <div className="max-w-2xl mx-auto">
            <Title level={2} className="font-serif !mb-6 !text-3xl md:!text-4xl !text-[#E0E0E0]">
              开启您的人生探索之旅
            </Title>
            <Paragraph className="text-gray-400 mb-10 text-lg">
              无论是困惑于当下的选择，还是好奇未来的走向，<br />
              AI 命理师都能为您提供独特的见解与指引。
            </Paragraph>
            <button
              className="group relative inline-flex items-center justify-center px-10 py-4 text-lg font-medium text-white transition-all duration-200 bg-[#C41E3A] rounded-full hover:bg-[#A01830] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#C41E3A] focus:ring-offset-[#1a1a1a]"
              onClick={() => navigate('/chat')}
            >
              <span className="absolute inset-0 w-full h-full -mt-1 rounded-lg opacity-30 bg-gradient-to-b from-transparent via-transparent to-black"></span>
              <span className="relative flex items-center">
                立即咨询 AI 命理师
                <ArrowRight className="ml-2 w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </span>
            </button>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default Home;
