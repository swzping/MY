import React from 'react';
import { Card, Row, Col, Typography, Statistic } from 'antd';
import { MedicineBoxOutlined, ExperimentOutlined, HeartOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;

const Home: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      title: '中医养生',
      icon: <MedicineBoxOutlined style={{ fontSize: '32px', color: '#1890ff' }} />,
      desc: '体质辨识、中药调理、穴位按摩',
      path: '/tcm',
    },
    {
      title: '营养膳食',
      icon: <ExperimentOutlined style={{ fontSize: '32px', color: '#52c41a' }} />,
      desc: '智能食谱、营养分析、相克提醒',
      path: '/nutrition',
    },
    {
      title: '心理健康',
      icon: <HeartOutlined style={{ fontSize: '32px', color: '#eb2f96' }} />,
      desc: '情绪识别、冥想训练、心理评估',
      path: '/mental',
    },
    {
      title: '运动健身',
      icon: <ThunderboltOutlined style={{ fontSize: '32px', color: '#faad14' }} />,
      desc: '个性化处方、数据追踪、效果评估',
      path: '/fitness',
    },
  ];

  return (
    <div>
      <div style={{ textAlign: 'center', marginBottom: 48 }}>
        <Title level={2}>欢迎使用大健康养生专家 Agent</Title>
        <Paragraph>
          您的全天候个性化健康顾问，整合中医与现代科学，为您提供全方位的健康管理服务。
        </Paragraph>
      </div>

      <Row gutter={[16, 16]}>
        {features.map((feature) => (
          <Col xs={24} sm={12} md={6} key={feature.title}>
            <Card
              hoverable
              onClick={() => navigate(feature.path)}
              style={{ height: '100%', textAlign: 'center' }}
            >
              <div style={{ marginBottom: 16 }}>{feature.icon}</div>
              <Title level={4}>{feature.title}</Title>
              <Paragraph type="secondary">{feature.desc}</Paragraph>
            </Card>
          </Col>
        ))}
      </Row>

      <div style={{ marginTop: 48 }}>
        <Title level={3}>今日健康概览</Title>
        <Row gutter={16}>
          <Col span={6}>
            <Card>
              <Statistic title="今日步数" value={6543} suffix="步" />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="卡路里消耗" value={420} suffix="kcal" precision={1} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="睡眠时长" value={7.5} suffix="小时" precision={1} />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic title="健康评分" value={88} suffix="分" valueStyle={{ color: '#3f8600' }} />
            </Card>
          </Col>
        </Row>
      </div>
    </div>
  );
};

export default Home;
