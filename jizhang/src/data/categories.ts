import type { Transaction, TransactionType } from "../lib/types";

export const expenseCategories = [
  "Food",
  "Transport",
  "Shopping",
  "Housing",
  "Entertainment",
  "Health",
  "Study",
  "Other",
] as const;

export const incomeCategories = ["Salary", "Side Income", "Gift", "Other"] as const;

export const categoryLabels: Record<string, string> = {
  Food: "餐饮",
  Transport: "交通",
  Shopping: "购物",
  Housing: "住房",
  Entertainment: "娱乐",
  Health: "医疗",
  Study: "学习",
  Other: "其他",
  Salary: "工资",
  "Side Income": "副业",
  Gift: "礼金",
};

// 一级/二级分类来自 history.xlsx 的历史账单。
export const historicalCategories: Record<TransactionType, Record<string, string[]>> = {
  "expense": {
    "食": [
      "早午晚餐",
      "水果零食"
    ],
    "居家物业": [
      "住",
      "水电煤气",
      "日常用品",
      "装修软装",
      "装修",
      "租房",
      "物业管理"
    ],
    "行": [
      "公共交通",
      "加油",
      "停车",
      "高速",
      "私家车费用",
      "车保险"
    ],
    "社交": [
      "娱乐",
      "人情"
    ],
    "健康": [
      "养生",
      "医疗保险",
      "医疗"
    ],
    "其他杂项": [
      "其他支出"
    ],
    "家庭": [
      "家庭开支",
      "M",
      "Q",
      "人情往来",
      "送礼请客",
      "孝敬长辈"
    ],
    "交流通讯": [
      "手机费"
    ],
    "金融保险": [
      "学习进修",
      "保险",
      "理财投资",
      "银行手续",
      "投资亏损",
      "利息支出",
      "投资亏损  现金"
    ],
    "休闲娱乐": [
      "旅游度假",
      "交际聚会",
      "休闲玩乐"
    ]
  },
  "income": {
    "职业收入": [
      "工资收入",
      "奖金收入",
      "兼职收入",
      "经营所得"
    ],
    "理财收入": [
      "公积金",
      "顺风车",
      "娱乐收入",
      "红包",
      "礼金收入",
      "中奖收入",
      "投资收入",
      "利息收入"
    ],
    "家庭支持": [
      "家庭支持☺️"
    ]
  }
};

export function getCategoryOptions(
  type: TransactionType,
  records: Transaction[],
  selected?: Pick<Transaction, "category" | "subcategory">,
): Record<string, string[]> {
  const result = Object.fromEntries(Object.entries(historicalCategories[type])
    .map(([category, children]) => [category, [...children]]));
  for (const record of records) {
    if (record.type !== type || !result[record.category] || !record.subcategory?.trim()) continue;
    const child = record.subcategory.trim();
    if (!result[record.category].includes(child)) result[record.category].push(child);
  }
  if (selected) {
    const children = result[selected.category] ?? (result[selected.category] = []);
    const child = selected.subcategory ?? "";
    if (!children.includes(child)) children.push(child);
  }
  return result;
}
