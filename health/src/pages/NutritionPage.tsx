import React from 'react';
import { Card, Input, List, Avatar, Tag } from 'antd';

const { Search } = Input;

const data = [
  {
    title: '西红柿炒鸡蛋',
    description: '富含维生素C和蛋白质，适合气虚体质',
    tags: ['低卡', '高蛋白'],
  },
  {
    title: '山药排骨汤',
    description: '健脾养胃，适合脾虚湿盛体质',
    tags: ['滋补', '养胃'],
  },
  {
    title: '清蒸鲈鱼',
    description: '优质蛋白，易消化，适合所有体质',
    tags: ['海鲜', '清淡'],
  },
];

const NutritionPage: React.FC = () => {
  return (
    <div>
      <h2>营养膳食搭配</h2>
      <Search placeholder="搜索食材或食谱" enterButton="搜索" size="large" style={{ marginBottom: 24 }} />
      
      <Card title="今日推荐食谱">
        <List
          itemLayout="horizontal"
          dataSource={data}
          renderItem={(item) => (
            <List.Item>
              <List.Item.Meta
                avatar={<Avatar src="https://joeschmoe.io/api/v1/random" />}
                title={<a href="#">{item.title}</a>}
                description={item.description}
              />
              <div>
                {item.tags.map((tag) => (
                  <Tag color="green" key={tag}>{tag}</Tag>
                ))}
              </div>
            </List.Item>
          )}
        />
      </Card>
    </div>
  );
};

export default NutritionPage;
