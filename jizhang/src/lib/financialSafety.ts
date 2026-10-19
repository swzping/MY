import type { Transaction } from './types';

export const assetKinds = { cash:'现金', deposit:'银行存款', bond:'国债', fund:'基金股票', home:'自住房', property:'投资房产', other:'其他资产' };
export type AssetKind = keyof typeof assetKinds;
export type Asset = { id:string; name:string; kind:AssetKind; channel:string; amount:number; liquid:boolean; investable:boolean; annualYield:number|null; maturity:string; updatedAt:string };
export type Debt = { id:string; name:string; balance:number; annualRate:number|null; monthlyPayment:number; maturity:string };
export type FinanceSettings = { essentialMonthly:number|null; stableMonthlyIncome:number|null; monthlySaving:number|null; reserveMonths:number; plannedExpense:number; targetMonthly:number; scenarioYield:number; inflation:number; useInflation:boolean; excludedCategories:string[] };
export type FinanceState = { version:1; updatedAt:string; assets:Asset[]; debts:Debt[]; settings:FinanceSettings; levels:{id:string;name:string;monthly:number}[] };
export function defaultFinance(): FinanceState {
 return {version:1,updatedAt:'',assets:[],debts:[],settings:{essentialMonthly:null,stableMonthlyIncome:null,monthlySaving:null,reserveMonths:12,plannedExpense:0,targetMonthly:1000,scenarioYield:1.2,inflation:2,useInflation:false,excludedCategories:['金融保险','居家物业','Housing','家庭']},levels:[1000,2000,3000,5000,10000].map((monthly,i)=>({id:String(i),name:['极简生活','基本生活','日常生活','舒适生活','宽裕生活'][i],monthly}))};
}
const sum = <T,>(items:T[], value:(item:T)=>number) => items.reduce((total,item)=>total+value(item),0);
const ratio=(top:number,bottom:number|null)=>bottom!==null&&bottom>0?top/bottom:null;
export function calculateSafety(state:FinanceState,today:string) {
 const {assets,debts,settings:s}=state;
 const totalAssets=sum(assets,a=>a.amount), totalDebts=sum(debts,d=>d.balance);
 const liquid=sum(assets.filter(a=>a.liquid),a=>a.amount);
 const monthlyPayments=sum(debts,d=>d.monthlyPayment);
 const monthlyObligations=s.essentialMonthly===null?null:s.essentialMonthly+monthlyPayments;
 const reserveTarget=(monthlyObligations??0)*s.reserveMonths;
 const nonInvestmentLiquid=sum(assets.filter(a=>a.liquid&&!a.investable),a=>a.amount);
 const eligible=sum(assets.filter(a=>a.investable&&a.kind!=='home'),a=>a.amount);
 const investable=Math.max(0,eligible-Math.max(0,reserveTarget+s.plannedExpense-nonInvestmentLiquid));
 const usableEmergency=Math.max(0,liquid-s.plannedExpense);
 const estimatedPassiveMonthly=sum(assets,a=>a.kind==='home'?0:a.amount*(a.annualYield??0)/100)/12;
 const oneYear=new Date(today+'T00:00:00');oneYear.setFullYear(oneYear.getFullYear()+1);
 const end=localDate(oneYear);
 const due12Months=sum(debts.filter(d=>d.maturity&&d.maturity>=today&&d.maturity<=end),d=>d.balance);
 return {totalAssets,totalDebts,netAssets:totalAssets-totalDebts,liquid,investable,reserveTarget,monthlyPayments,monthlyObligations,usableEmergency,
  runway:ratio(usableEmergency,monthlyObligations),debtRatio:ratio(totalDebts,totalAssets),paymentRatio:ratio(monthlyPayments,s.stableMonthlyIncome),estimatedPassiveMonthly,
  passiveCoverage:ratio(estimatedPassiveMonthly,s.targetMonthly),unknownYieldAssets:assets.filter(a=>a.annualYield===null).length,due12Months,
  overdueDebt:sum(debts.filter(d=>d.maturity&&d.maturity<today),d=>d.balance)};
}
export function freedomTarget(monthly:number,yieldPercent:number,inflation:number,real:boolean,capital:number,saving:number|null) {
 const rate=real?(1+yieldPercent/100)/(1+inflation/100)-1:yieldPercent/100;
 const required=rate>0?monthly*12/rate:null;
 const gap=required===null?null:Math.max(0,required-capital);
 return {required,gap,progress:required?capital/required:null,supportedMonthly:Math.max(0,capital*rate/12),
  monthsToGoal:gap===0?0:gap!==null&&saving!==null&&saving>0?Math.ceil(gap/saving):null};
}
export function distribution(assets:Asset[],by:'kind'|'channel') {
 const total=sum(assets,a=>a.amount), grouped=new Map<string,number>();
 for(const a of assets){const key=by==='kind'?assetKinds[a.kind]:a.channel;grouped.set(key,(grouped.get(key)??0)+a.amount);}
 return [...grouped].map(([name,amount])=>({name,amount,percent:total?amount/total:0})).sort((a,b)=>b.amount-a.amount);
}
function localDate(d:Date){return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;}
export function previousMonths(today:string,count=3) {
 const [year,month]=today.split('-').map(Number);
 return Array.from({length:count},(_,i)=>localDate(new Date(year,month-2-i,1)).slice(0,7));
}
export function spendingReference(records:Transaction[],today:string,excluded:string[]) {
 const months=previousMonths(today);const all=records.filter(r=>months.includes(r.date.slice(0,7)));
 const expenses=all.filter(r=>r.type==='expense');
 const excludedTotal=sum(expenses.filter(r=>excluded.includes(r.category)),r=>r.amount);
 return {months,monthsWithRecords:new Set(all.map(r=>r.date.slice(0,7))).size,monthlyExpense:(sum(expenses,r=>r.amount)-excludedTotal)/3,excludedTotal,
  monthlyNet:(sum(all.filter(r=>r.type==='income'),r=>r.amount)-sum(expenses,r=>r.amount))/3};
}
export function stressTest(state:FinanceState,today:string,months:number,shock:number,yieldDrop:number) {
 const base=calculateSafety(state,today);
 const remaining=base.monthlyObligations===null?null:base.usableEmergency-shock-base.monthlyObligations*months;
 const newYield=Math.max(0,state.settings.scenarioYield-yieldDrop);
 return {remaining,shortfall:remaining===null?null:Math.max(0,-remaining),newYield,
  supportedMonthly:freedomTarget(state.settings.targetMonthly,newYield,state.settings.inflation,state.settings.useInflation,base.investable,null).supportedMonthly};
}
export function validDate(value:unknown):value is string {
 if(typeof value!=='string')return false;
 if(value==='')return true;
 if(!/^\d{4}-\d{2}-\d{2}$/.test(value))return false;
 const date=new Date(value+'T00:00:00');return Number.isFinite(date.getTime())&&localDate(date)===value;
}
export function validateFinance(value:unknown):value is FinanceState {
 if(!value||typeof value!=='object')return false;
 const v=value as FinanceState;
 const num=(n:unknown)=>typeof n==='number'&&Number.isFinite(n)&&n>=0&&n<=1e12;
 const nullable=(n:unknown)=>n===null||num(n);
 const str=(s:unknown)=>typeof s==='string';
 const unique=(a:{id:string}[])=>new Set(a.map(x=>x.id)).size===a.length;
 try {return v.version===1&&str(v.updatedAt)&&Array.isArray(v.assets)&&unique(v.assets)&&v.assets.every(a=>a&&str(a.id)&&!!a.id&&str(a.name)&&!!a.name.trim()&&str(a.channel)&&!!a.channel.trim()&&Object.keys(assetKinds).includes(a.kind)&&num(a.amount)&&typeof a.liquid==='boolean'&&typeof a.investable==='boolean'&&nullable(a.annualYield)&&validDate(a.maturity)&&str(a.updatedAt)&&!(a.kind==='home'&&(a.liquid||a.investable)))
 &&Array.isArray(v.debts)&&unique(v.debts)&&v.debts.every(d=>d&&str(d.id)&&!!d.id&&str(d.name)&&!!d.name.trim()&&num(d.balance)&&nullable(d.annualRate)&&num(d.monthlyPayment)&&validDate(d.maturity))
 &&v.settings&&nullable(v.settings.essentialMonthly)&&nullable(v.settings.stableMonthlyIncome)&&nullable(v.settings.monthlySaving)&&num(v.settings.reserveMonths)&&v.settings.reserveMonths<=120&&num(v.settings.plannedExpense)&&num(v.settings.targetMonthly)&&v.settings.targetMonthly>0&&num(v.settings.scenarioYield)&&v.settings.scenarioYield<=100&&num(v.settings.inflation)&&v.settings.inflation<=100&&typeof v.settings.useInflation==='boolean'&&Array.isArray(v.settings.excludedCategories)&&v.settings.excludedCategories.every(str)
 &&Array.isArray(v.levels)&&v.levels.length>0&&unique(v.levels)&&v.levels.every(l=>str(l.id)&&str(l.name)&&!!l.name.trim()&&num(l.monthly)&&l.monthly>0);
 }catch{return false;}
}
