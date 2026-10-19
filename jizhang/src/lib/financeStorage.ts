import { defaultFinance, validateFinance, type FinanceState } from './financialSafety';
export const FINANCE_KEY='personal-budget-app:financial-safety:v1';
type Storage={getItem(key:string):Promise<string|null>;setItem(key:string,value:string):Promise<void>};
export async function loadFinance(storage:Storage):Promise<FinanceState>{
 const text=await storage.getItem(FINANCE_KEY);
 if(text===null)return defaultFinance();
 const data:unknown=JSON.parse(text);
 if(!validateFinance(data))throw new Error('财务资料格式不正确，已保留原数据，请检查后重试');
 return data;
}
export async function saveFinance(storage:Storage,data:FinanceState){
 if(!validateFinance(data))throw new Error('请检查金额、日期和必填项');
 await storage.setItem(FINANCE_KEY,JSON.stringify(data));
}
