import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, Button, Tabs, Tag, Row, Col, Statistic, message } from 'antd';
import { Share2, Download, Printer, ArrowLeft, Clock, User, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import ReactECharts from 'echarts-for-react';

// 模拟报告数据
const mockReportData = {
  id: 1,
  title: '八字命理分析报告',
  type: 'bazi',
  created_at: '2024-03-15',
  content: `
# 八字命理分析报告

## 基本信息

**出生时间**: 1990年5月15日 14:30  
**性别**: 男  
**八字**: 庚午年 辛巳月 丁丑日 丁未时

## 五行分析

| 五行 | 天干 | 地支 | 力量 |
|------|------|------|------|
| 金 | 庚、辛 | - | 中等 |
| 木 | - | - | 偏弱 |
| 水 | - | - | 偏弱 |
| 火 | 丁、丁 | 午、巳 | 偏旺 |
| 土 | - | 丑、未 | 中等 |

## 命局分析

您的八字火旺，为人热情开朗，有领导才能。金有庚辛透出，说明您有决断力，做事果断。

**优点**:
- 热情积极，有感染力
- 领导能力强，善于组织
- 做事果断，不拖泥带水

**需要注意**:
- 脾气可能较急，需学会控制
- 木水偏弱，可多接触绿色植物
- 注意心脏和眼睛健康

## 大运流年

当前大运: 甲申运 (2020-2030)  
明年流年: 甲辰年

2024年整体运势平稳，事业有新的发展机会，但需注意人际关系。
  `,
  data: {
    wuxing: {
      labels: ['金', '木', '水', '火', '土'],
      values: [20, 10, 10, 40, 20],
    },
    shishen: {
      labels: ['比肩', '劫财', '食神', '伤官', '偏财', '正财', '七杀', '正官', '偏印', '正印'],
      values: [15, 10, 8, 12, 18, 14, 6, 9, 11, 7],
    },
    dayun: {
      years: ['2010', '2015', '2020', '2025', '2030', '2035'],
      fortune: [60, 65, 70, 75, 72, 80],
    },
  },
};

const ReportView: React.FC = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [report] = useState(mockReportData);
  const [activeTab, setActiveTab] = useState('overview');

  const handleShare = () => {
    // 生成分享链接
    const shareUrl = `${window.location.origin}/share/${id}`;
    navigator.clipboard.writeText(shareUrl);
    message.success('分享链接已复制到剪贴板');
  };

  const handleDownload = () => {
    // 下载PDF
    message.success('报告下载中...');
  };

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="max-w-5xl mx-auto px-4 py-8"
    >
      {/* 头部 */}
      <div className="flex items-center justify-between mb-8">
        <Button
          icon={<ArrowLeft size={16} />}
          onClick={() => navigate(-1)}
          className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
        >
          返回
        </Button>
        <div className="flex gap-3">
          <Button
            icon={<Share2 size={16} />}
            onClick={handleShare}
            className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
          >
            分享
          </Button>
          <Button
            icon={<Download size={16} />}
            onClick={handleDownload}
            type="primary"
            style={{ background: '#C41E3A', borderColor: '#C41E3A' }}
          >
            下载PDF
          </Button>
        </div>
      </div>

      {/* 报告标题 */}
      <Card
        className="!bg-gradient-to-r from-[#C41E3A]/20 to-[#FFD700]/20 !border-[#C41E3A]/30 mb-6"
      >
        <div className="text-center py-4">
          <h1 className="text-3xl font-serif text-[#E0E0E0] mb-4">{report.title}</h1>
          <div className="flex justify-center gap-4 text-sm text-gray-400">
            <span className="flex items-center gap-1">
              <Clock size={14} /> {report.created_at}
            </span>
            <span className="flex items-center gap-1">
              <User size={14} /> 国学命理
            </span>
            <Tag color="#C41E3A">{report.type}</Tag>
          </div>
        </div>
      </Card>

      {/* 主要内容 */}
      <Row gutter={24}>
        <Col span={18}>
          <Card className="!bg-white/5 !border-white/10">
            <Tabs
              activeKey={activeTab}
              onChange={setActiveTab}
              className="report-tabs"
            >
              <Tabs.TabPane tab="详细分析" key="overview">
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown>{report.content}</ReactMarkdown>
                </div>
              </Tabs.TabPane>
              
              <Tabs.TabPane tab="五行图表" key="charts">
                <div className="space-y-6">
                  <div>
                    <h3 className="text-lg text-[#E0E0E0] mb-4">五行分布</h3>
                    <ReactECharts
                      option={{
                        tooltip: { trigger: 'item', formatter: '{b}: {c}%' },
                        legend: { 
                          orient: 'vertical', 
                          right: 10, 
                          top: 'center',
                          textStyle: { color: '#E0E0E0' }
                        },
                        series: [{
                          type: 'pie',
                          radius: ['40%', '70%'],
                          avoidLabelOverlap: false,
                          itemStyle: {
                            borderRadius: 10,
                            borderColor: '#1F1F1F',
                            borderWidth: 2
                          },
                          label: { show: false },
                          emphasis: {
                            label: { show: true, fontSize: 14, fontWeight: 'bold', color: '#E0E0E0' }
                          },
                          data: report.data.wuxing.labels.map((label, i) => ({
                            value: report.data.wuxing.values[i],
                            name: label,
                            itemStyle: {
                              color: ['#FFD700', '#52c41a', '#1890ff', '#C41E3A', '#8b4513'][i]
                            }
                          }))
                        }]
                      }}
                      style={{ height: 250 }}
                    />
                  </div>
                  <div>
                    <h3 className="text-lg text-[#E0E0E0] mb-4">十神分析</h3>
                    <ReactECharts
                      option={{
                        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
                        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                        xAxis: { 
                          type: 'category', 
                          data: report.data.shishen.labels,
                          axisLabel: { color: '#888', rotate: 45, fontSize: 10 },
                          axisLine: { lineStyle: { color: '#333' } }
                        },
                        yAxis: { 
                          type: 'value',
                          axisLabel: { color: '#888' },
                          splitLine: { lineStyle: { color: '#333' } }
                        },
                        series: [{
                          type: 'bar',
                          data: report.data.shishen.values,
                          itemStyle: {
                            color: {
                              type: 'linear',
                              x: 0, y: 0, x2: 0, y2: 1,
                              colorStops: [
                                { offset: 0, color: '#C41E3A' },
                                { offset: 1, color: '#FFD700' }
                              ]
                            },
                            borderRadius: [4, 4, 0, 0]
                          }
                        }]
                      }}
                      style={{ height: 280 }}
                    />
                  </div>
                  <div>
                    <h3 className="text-lg text-[#E0E0E0] mb-4">大运走势</h3>
                    <ReactECharts
                      option={{
                        tooltip: { trigger: 'axis' },
                        grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
                        xAxis: { 
                          type: 'category', 
                          data: report.data.dayun.years,
                          axisLabel: { color: '#888' },
                          axisLine: { lineStyle: { color: '#333' } }
                        },
                        yAxis: { 
                          type: 'value',
                          min: 50,
                          max: 100,
                          axisLabel: { color: '#888' },
                          splitLine: { lineStyle: { color: '#333' } }
                        },
                        series: [{
                          type: 'line',
                          data: report.data.dayun.fortune,
                          smooth: true,
                          symbol: 'circle',
                          symbolSize: 8,
                          lineStyle: { color: '#C41E3A', width: 3 },
                          itemStyle: { color: '#FFD700' },
                          areaStyle: {
                            color: {
                              type: 'linear',
                              x: 0, y: 0, x2: 0, y2: 1,
                              colorStops: [
                                { offset: 0, color: 'rgba(196, 30, 58, 0.4)' },
                                { offset: 1, color: 'rgba(196, 30, 58, 0.05)' }
                              ]
                            }
                          }
                        }]
                      }}
                      style={{ height: 200 }}
                    />
                  </div>
                </div>
              </Tabs.TabPane>
              
              <Tabs.TabPane tab="建议方案" key="suggestions">
                <div className="space-y-4">
                  <Card className="!bg-[#FFD700]/10 !border-[#FFD700]/30">
                    <h4 className="text-[#FFD700] font-medium mb-2 flex items-center gap-2">
                      <Sparkles size={16} /> 吉祥建议
                    </h4>
                    <ul className="text-gray-300 space-y-2">
                      <li>• 幸运颜色：绿色、蓝色</li>
                      <li>• 幸运数字：3、8</li>
                      <li>• 有利方位：东方、北方</li>
                      <li>• 适宜行业：教育、文化、环保</li>
                    </ul>
                  </Card>
                  
                  <Card className="!bg-white/5 !border-white/10">
                    <h4 className="text-[#E0E0E0] font-medium mb-2">日常建议</h4>
                    <ul className="text-gray-400 space-y-2">
                      <li>• 多接触绿色植物，补充木气</li>
                      <li>• 保持充足睡眠，养护肝脏</li>
                      <li>• 遇事冷静，避免冲动决策</li>
                      <li>• 多穿蓝绿色系衣服</li>
                    </ul>
                  </Card>
                </div>
              </Tabs.TabPane>
            </Tabs>
          </Card>
        </Col>

        <Col span={6}>
          <div className="space-y-4">
            <Card className="!bg-white/5 !border-white/10">
              <Statistic
                title={<span className="text-gray-400">分析深度</span>}
                value={98}
                suffix="%"
                valueStyle={{ color: '#FFD700' }}
              />
            </Card>
            
            <Card className="!bg-white/5 !border-white/10">
              <Statistic
                title={<span className="text-gray-400">数据点</span>}
                value={156}
                valueStyle={{ color: '#C41E3A' }}
              />
            </Card>
            
            <Card className="!bg-white/5 !border-white/10">
              <h4 className="text-[#E0E0E0] font-medium mb-3">报告标签</h4>
              <div className="flex flex-wrap gap-2">
                <Tag color="blue">八字</Tag>
                <Tag color="green">五行</Tag>
                <Tag color="orange">大运</Tag>
                <Tag color="purple">流年</Tag>
              </div>
            </Card>

            <Card className="!bg-white/5 !border-white/10">
              <h4 className="text-[#E0E0E0] font-medium mb-3">操作</h4>
              <div className="space-y-2">
                <Button
                  block
                  icon={<Printer size={14} />}
                  className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
                >
                  打印报告
                </Button>
                <Button
                  block
                  icon={<Share2 size={14} />}
                  onClick={handleShare}
                  className="!bg-white/5 !border-white/10 !text-[#E0E0E0]"
                >
                  分享报告
                </Button>
              </div>
            </Card>
          </div>
        </Col>
      </Row>
    </motion.div>
  );
};

export default ReportView;
