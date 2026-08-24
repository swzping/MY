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
