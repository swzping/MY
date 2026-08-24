import React from 'react';
import { Card, Calendar, Badge, List } from 'antd';
import type { BadgeProps } from 'antd';
import type { Dayjs } from 'dayjs';

const getListData = (value: Dayjs) => {
  let listData;
  switch (value.date()) {
    case 8:
      listData = [
        { type: 'warning', content: '有氧运动 30分钟' },
        { type: 'success', content: '八段锦 15分钟' },
      ];
      break;
    case 10:
      listData = [
        { type: 'warning', content: '力量训练 45分钟' },
      ];
      break;
    case 15:
      listData = [
        { type: 'success', content: '太极拳 20分钟' },
        { type: 'error', content: '未完成：跑步' },
      ];
      break;
    default:
  }
  return listData || [];
};

const dateCellRender = (value: Dayjs) => {
  const listData = getListData(value);
  return (
    <ul className="events">
      {listData.map((item) => (
        <li key={item.content}>
          <Badge status={item.type as BadgeProps['status']} text={item.content} />
        </li>
      ))}
    </ul>
  );
};

const FitnessPage: React.FC = () => {
  return (
    <div>
      <h2>运动健康管理</h2>
      <Card title="本月运动计划">
        <Calendar dateCellRender={dateCellRender} />
      </Card>
      
      <Card title="推荐运动" style={{ marginTop: 24 }}>
        <List
          grid={{ gutter: 16, column: 4 }}
          dataSource={[
            { title: '八段锦', desc: '传统养生功法' },
            { title: '慢跑', desc: '有氧运动' },
            { title: '瑜伽', desc: '柔韧性训练' },
            { title: '深蹲', desc: '力量训练' },
          ]}
          renderItem={(item) => (
            <List.Item>
              <Card title={item.title}>{item.desc}</Card>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default FitnessPage;
