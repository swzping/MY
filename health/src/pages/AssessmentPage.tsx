import React from 'react';
import { Card, Row, Col, Progress, Descriptions } from 'antd';

const AssessmentPage: React.FC = () => {
  return (
    <div>
      <h2>综合健康评估</h2>
      <Row gutter={16}>
        <Col span={8}>
          <Card title="综合健康评分">
            <div style={{ textAlign: 'center' }}>
              <Progress type="circle" percent={88} format={(percent) => `${percent}分`} />
              <p style={{ marginTop: 16 }}>状态：良好</p>
            </div>
          </Card>
        </Col>
        <Col span={16}>
          <Card title="健康指标详情">
            <Descriptions bordered column={2}>
              <Descriptions.Item label="BMI指数">22.5 (正常)</Descriptions.Item>
              <Descriptions.Item label="体脂率">18% (正常)</Descriptions.Item>
              <Descriptions.Item label="心肺功能">良好</Descriptions.Item>
              <Descriptions.Item label="睡眠质量">优</Descriptions.Item>
              <Descriptions.Item label="压力水平">中等</Descriptions.Item>
              <Descriptions.Item label="免疫力">强</Descriptions.Item>
            </Descriptions>
          </Card>
        </Col>
      </Row>

      <Card title="健康风险预警" style={{ marginTop: 24 }}>
        <p style={{ color: '#faad14' }}>⚠️ 您的久坐时间过长，建议每小时起身活动 5 分钟。</p>
        <p style={{ color: '#52c41a' }}>✅ 您的饮食结构合理，请继续保持。</p>
      </Card>
    </div>
  );
};

export default AssessmentPage;
