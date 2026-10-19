import { expect,it } from 'vitest';
import { spendingAdvice } from './spendingAdvice';
import type { Transaction } from './types';
const tx=(date:string,amount:number,category='休闲娱乐',subcategory='旅游度假'):Transaction=>({id:date+amount,date,amount,type:'expense',category,subcategory,note:'',createdAt:date});
it('compares matching periods, excludes exceptional and essential expenses, and estimates savings',()=>{
 const r=spendingAdvice([tx('2026-09-01',600),tx('2026-08-01',200),tx('2026-07-01',200),tx('2026-06-01',200),tx('2026-10-01',900),tx('2026-10-25',10000),tx('2026-09-01',5000,'健康','医疗')],'2026-10-19',1000,[],10);
 expect(r.budget?.spent).toBe(900);
 expect(r.trends[0].increase).toBe(400);
 expect(r.cuts[0].monthlySaving).toBeCloseTo(1000/3*0.1);
 expect(r.cuts.some(x=>x.category==='健康')).toBe(false);
});
it('does not assert trend increases without enough history or recommend reductions for zero budgets',()=>{
 const r=spendingAdvice([tx('2026-09-01',500)],'2026-10-19',0,[],10);
 expect(r.trends).toHaveLength(0);expect(r.budget).toBeNull();
});
