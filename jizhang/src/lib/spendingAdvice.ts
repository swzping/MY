import type { Transaction } from './types';
import { previousMonths } from './financialSafety';
export function spendingAdvice(records:Transaction[],today:string,budget:number,excluded:string[],cutPercent:number) {
 const expenses=records.filter(r=>r.type==='expense'&&r.date<=today);
 const spent=expenses.filter(r=>r.date.startsWith(today.slice(0,7))).reduce((s,r)=>s+r.amount,0);
 const months=previousMonths(today,4),latest=months[0],baseline=months.slice(1);
 const available=new Set(records.filter(r=>baseline.includes(r.date.slice(0,7))).map(r=>r.date.slice(0,7)));
 const relevant=expenses.filter(r=>!excluded.includes(r.category));
 const keys=[...new Set(relevant.map(r=>r.category))];
 const trends=available.size<2?[]:keys.map(category=>{
   const current=relevant.filter(r=>r.category===category&&r.date.startsWith(latest)).reduce((s,r)=>s+r.amount,0);
   const average=relevant.filter(r=>r.category===category&&available.has(r.date.slice(0,7))).reduce((s,r)=>s+r.amount,0)/available.size;
   return {category,current,average,increase:current-average};
 }).filter(x=>x.average>0&&x.increase>=100&&x.current>=x.average*1.3).sort((a,b)=>b.increase-a.increase).slice(0,3);
 const recent=months.slice(0,3),groups=new Map<string,{category:string;subcategory:string;amount:number}>();
 for(const r of relevant){
   if(!recent.includes(r.date.slice(0,7)))continue;
   const sub=r.subcategory??'';
   const adjustable=r.category==='休闲娱乐'||r.category==='Entertainment'||(r.category==='食'&&sub==='水果零食')||(r.category==='社交'&&sub==='娱乐');
   if(!adjustable)continue;
   const key=JSON.stringify([r.category,sub]);const item=groups.get(key)??{category:r.category,subcategory:sub,amount:0};item.amount+=r.amount;groups.set(key,item);
 }
 const cuts=[...groups.values()].map(g=>({...g,monthlyAverage:g.amount/3,monthlySaving:g.amount/3*cutPercent/100})).sort((a,b)=>b.monthlySaving-a.monthlySaving).slice(0,3);
 return {budget:budget>0?{spent,limit:budget,ratio:spent/budget}:null,trends,cuts,latest,baselineMonths:available.size,
  recentMonths:recent,monthsWithRecords:new Set(records.filter(r=>recent.includes(r.date.slice(0,7))).map(r=>r.date.slice(0,7))).size};
}
