import React from 'react';
import { Card, Button, Steps, Form, Radio, Input, Upload, message } from 'antd';
import { UploadOutlined } from '@ant-design/icons';

const TCMPage: React.FC = () => {
  const [current, setCurrent] = React.useState(0);

  const next = () => {
    setCurrent(current + 1);
  };

  const prev = () => {
    setCurrent(current - 1);
  };

  const steps = [
    {
      title: '基本信息',
      content: (
        <Form layout="vertical">
          <Form.Item label="出生日期">
            <Input type="date" />
          </Form.Item>
          <Form.Item label="舌象照片">
            <Upload>
              <Button icon={<UploadOutlined />}>上传舌象照片</Button>
            </Upload>
          </Form.Item>
        </Form>
      ),
    },
    {
      title: '体质问卷',
      content: (
        <Form layout="vertical">
          <Form.Item label="您是否容易疲劳？">
            <Radio.Group>
              <Radio value="a">经常</Radio>
              <Radio value="b">偶尔</Radio>
              <Radio value="c">从不</Radio>
            </Radio.Group>
          </Form.Item>
          <Form.Item label="您是否怕冷？">
            <Radio.Group>
              <Radio value="a">经常</Radio>
              <Radio value="b">偶尔</Radio>
              <Radio value="c">从不</Radio>
            </Radio.Group>
          </Form.Item>
        </Form>
      ),
    },
    {
      title: '完成',
      content: (
        <div style={{ textAlign: 'center' }}>
          <h3>测试完成！</h3>
          <p>点击提交查看您的体质报告。</p>
        </div>
      ),
    },
  ];

  const items = steps.map((item) => ({ key: item.title, title: item.title }));

  return (
    <div>
      <h2>中医养生调理</h2>
      <Card title="体质辨识测试">
        <Steps current={current} items={items} />
        <div style={{ marginTop: 24, minHeight: 200 }}>{steps[current].content}</div>
        <div style={{ marginTop: 24 }}>
          {current < steps.length - 1 && (
            <Button type="primary" onClick={() => next()}>
              下一步
            </Button>
          )}
          {current === steps.length - 1 && (
            <Button type="primary" onClick={() => message.success('提交成功！')}>
              提交测试
            </Button>
          )}
          {current > 0 && (
            <Button style={{ margin: '0 8px' }} onClick={() => prev()}>
              上一步
            </Button>
          )}
        </div>
      </Card>
    </div>
  );
};

export default TCMPage;
