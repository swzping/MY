import React, { useState, useEffect } from 'react';
import { Button, Modal, Steps, Typography } from 'antd';
import { ArrowRight, ArrowLeft, X, Compass, Star, User, Book } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const { Title } = Typography;

interface TutorialProps {
  visible: boolean;
  onClose: () => void;
}

const tutorialSteps = [
  {
    title: '欢迎使用国学命理',
    icon: <Star className="w-12 h-12 text-[#FFD700]" />,
    content: `
      <p className="text-lg mb-4">探索传统智慧，指引现代生活</p>
      <p className="text-gray-400">本应用融合周易、命理、星象等传统文化精髓，辅以现代AI技术，为您提供专业的命理咨询服务。</p>
    `,
  },
  {
    title: '五大核心功能',
    icon: <Compass className="w-12 h-12 text-[#C41E3A]" />,
    content: `
      <div class="grid grid-cols-2 gap-4 mt-4">
        <div class="bg-white/5 p-3 rounded-lg">
          <h4 class="text-[#FFD700] font-medium">周易占卜</h4>
          <p class="text-sm text-gray-400">六爻排盘，解析吉凶祸福</p>
        </div>
        <div class="bg-white/5 p-3 rounded-lg">
          <h4 class="text-[#FFD700] font-medium">星座运势</h4>
          <p class="text-sm text-gray-400">星象奥秘，每日运势更新</p>
        </div>
        <div class="bg-white/5 p-3 rounded-lg">
          <h4 class="text-[#FFD700] font-medium">生肖配对</h4>
          <p class="text-sm text-gray-400">传统合婚，分析性格匹配</p>
        </div>
        <div class="bg-white/5 p-3 rounded-lg">
          <h4 class="text-[#FFD700] font-medium">八字命理</h4>
          <p class="text-sm text-gray-400">四柱排盘，详批流年大运</p>
        </div>
      </div>
    `,
  },
  {
    title: '如何开始咨询',
    icon: <Book className="w-12 h-12 text-blue-500" />,
    content: `
      <ol class="list-decimal list-inside space-y-3 text-gray-300">
        <li>在首页选择您感兴趣的功能模块</li>
        <li>进入咨询页面，输入您的问题</li>
        <li>AI助手将为您进行专业分析</li>
        <li>查看详细报告，获取个性化建议</li>
      </ol>
    `,
  },
  {
    title: '会员权益',
    icon: <User className="w-12 h-12 text-purple-500" />,
    content: `
      <div class="space-y-3">
        <div class="flex items-center justify-between bg-white/5 p-3 rounded-lg">
          <span class="text-[#E0E0E0]">免费用户</span>
          <span class="text-gray-400">每日10次咨询</span>
        </div>
        <div class="flex items-center justify-between bg-[#FFD700]/10 p-3 rounded-lg border border-[#FFD700]/30">
          <span class="text-[#FFD700] font-medium">月度会员</span>
          <span class="text-gray-400">每日100次 + 详细报告</span>
        </div>
        <div class="flex items-center justify-between bg-[#C41E3A]/10 p-3 rounded-lg border border-[#C41E3A]/30">
          <span class="text-[#C41E3A] font-medium">年度会员</span>
          <span class="text-gray-400">无限次 + 专家咨询</span>
        </div>
      </div>
    `,
  },
];

const Tutorial: React.FC<TutorialProps> = ({ visible, onClose }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const nextStep = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onClose();
      localStorage.setItem('tutorial_completed', 'true');
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const skipTutorial = () => {
    onClose();
    localStorage.setItem('tutorial_completed', 'true');
  };

  return (
    <Modal
      open={visible}
      onCancel={skipTutorial}
      footer={null}
      width={700}
      centered
      closable={false}
      className="tutorial-modal"
      style={{
        background: 'linear-gradient(135deg, #1a1a2e 0%, #2C2C2C 100%)',
      }}
    >
      <div className="relative">
        {/* 关闭按钮 */}
        <button
          onClick={skipTutorial}
          className="absolute top-0 right-0 p-2 text-gray-500 hover:text-[#E0E0E0] transition-colors z-10"
        >
          <X size={20} />
        </button>

        {/* 步骤指示器 */}
        <div className="flex justify-center mb-8">
          <Steps
            current={currentStep}
            className="custom-steps"
          >
            {tutorialSteps.map((_, index) => (
              <Steps.Step key={index} />
            ))}
          </Steps>
        </div>

        {/* 内容区域 */}
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
            className="text-center py-8"
          >
            <div className="flex justify-center mb-6">
              {tutorialSteps[currentStep].icon}
            </div>
            
            <Title level={3} className="!text-[#E0E0E0] !mb-4">
              {tutorialSteps[currentStep].title}
            </Title>
            
            <div 
              className="text-gray-300 max-w-md mx-auto"
              dangerouslySetInnerHTML={{ __html: tutorialSteps[currentStep].content }}
            />
          </motion.div>
        </AnimatePresence>

        {/* 按钮区域 */}
        <div className="flex justify-between items-center mt-8 pt-6 border-t border-white/10">
          <Button
            onClick={skipTutorial}
            className="!bg-transparent !border-none !text-gray-500 hover:!text-[#E0E0E0]"
          >
            跳过
          </Button>

          <div className="flex gap-3">
            {currentStep > 0 && (
              <Button
                onClick={prevStep}
                icon={<ArrowLeft size={16} />}
                className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
              >
                上一步
              </Button>
            )}
            <Button
              type="primary"
              onClick={nextStep}
              icon={currentStep === tutorialSteps.length - 1 ? undefined : <ArrowRight size={16} />}
              style={{
                background: currentStep === tutorialSteps.length - 1 ? '#C41E3A' : 'linear-gradient(135deg, #C41E3A 0%, #FFD700 100%)',
                border: 'none',
              }}
            >
              {currentStep === tutorialSteps.length - 1 ? '开始使用' : '下一步'}
            </Button>
          </div>
        </div>
      </div>
    </Modal>
  );
};

// 自动显示新手引导的Hook
export const useTutorial = () => {
  const [showTutorial, setShowTutorial] = useState(false);

  useEffect(() => {
    const completed = localStorage.getItem('tutorial_completed');
    if (!completed) {
      // 延迟显示，等页面加载完成
      const timer = setTimeout(() => {
        setShowTutorial(true);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  return { showTutorial, setShowTutorial };
};

export default Tutorial;
