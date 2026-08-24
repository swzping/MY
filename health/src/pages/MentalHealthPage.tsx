import React from 'react';
import { Card, Button, Progress, Row, Col } from 'antd';
import { SmileOutlined, MehOutlined, FrownOutlined } from '@ant-design/icons';

const MentalHealthPage: React.FC = () => {
  return (
    <div>
      <h2>情绪管理与心理健康</h2>
      <Row gutter={16}>
        <Col span={12}>
          <Card title="今日心情记录">
             <div style={{ display: 'flex', justifyContent: 'space-around', fontSize: 40 }}>
                <SmileOutlined style={{ color: '#52c41a', cursor: 'pointer' }} />
                <MehOutlined style={{ color: '#faad14', cursor: 'pointer' }} />
                <FrownOutlined style={{ color: '#f5222d', cursor: 'pointer' }} />
             </div>
             <p style={{ textAlign: 'center', marginTop: 16 }}>点击图标记录当前心情</p>
          </Card>
        </Col>
        <Col span={12}>
          <Card title="冥想训练">
            <p>当前进度：初级冥想课程</p>
            <Progress percent={30} />
            <Button type="primary" style={{ marginTop: 16 }}>开始今日练习</Button>
          </Card>
        </Col>
      </Row>
      
      <Card title="心理健康小贴士" style={{ marginTop: 24 }}>
        <p>1. 每天保持深呼吸 5 分钟，有助于缓解焦虑。</p>
        <p>2. 规律作息，保证充足的睡眠。</p>
        <p>3. 与朋友和家人保持沟通。</p>
      </Card>
    </div>
  );
};

export default MentalHealthPage;
