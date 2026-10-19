import { describe, expect, it } from 'vitest';
import { defaultFinance, calculateSafety, freedomTarget, spendingReference, stressTest, validateFinance, type FinanceState } from './financialSafety';
const state = (): FinanceState => ({ ...defaultFinance(), assets: [{ id:'a', name:'存款', kind:'deposit', channel:'银行', amount:1000000, liquid:true, investable:true, annualYield:1.2, maturity:'', updatedAt:'2026-10-19' }] });
describe('financial safety', () => {
 it('matches the million principal example and separates reserves', () => {
   const s=state(); s.settings.essentialMonthly=1000; s.settings.reserveMonths=12;
   const result=calculateSafety(s,'2026-10-19');
   expect(result.netAssets).toBe(1000000);
   expect(result.investable).toBe(988000);
   expect(freedomTarget(1000,1.2,0,false,1000000,0).required).toBe(1000000);
   expect(freedomTarget(1000,1.2,0,false,1000000,0).supportedMonthly).toBe(1000);
 });
 it('does not invent ratios for missing data and handles underwater households', () => {
   const s=defaultFinance();
   expect(calculateSafety(s,'2026-10-19').debtRatio).toBeNull();
   expect(calculateSafety(s,'2026-10-19').runway).toBeNull();
   s.debts=[{id:'d',name:'贷款',balance:10000,annualRate:5,monthlyPayment:500,maturity:'2027-01-01'}];
   expect(calculateSafety(s,'2026-10-19').netAssets).toBe(-10000);
   expect(calculateSafety(s,'2026-10-19').due12Months).toBe(10000);
 });
 it('excludes the home and keeps unknown yield explicit', () => {
   const s=state();s.assets.push({...s.assets[0],id:'h',kind:'home',amount:2000000,liquid:false,investable:false,annualYield:null});
   const r=calculateSafety(s,'2026-10-19');
   expect(r.investable).toBe(1000000);
   expect(r.estimatedPassiveMonthly).toBe(1000);
   expect(r.unknownYieldAssets).toBe(1);
 });
 it('does not count emergency funds twice and includes debt service in runway', () => {
   const s=state();s.assets.push({...s.assets[0],id:'cash',amount:12000,investable:false});
   s.settings.essentialMonthly=1000;s.settings.reserveMonths=12;
   expect(calculateSafety(s,'2026-10-19').investable).toBe(1000000);
   s.debts=[{id:'d',name:'贷款',balance:10000,annualRate:5,monthlyPayment:1000,maturity:''}];
   expect(calculateSafety(s,'2026-10-19').monthlyObligations).toBe(2000);
 });
 it('treats non-positive real returns as an unsustainable perpetuity', () => {
   expect(freedomTarget(1000,1.2,2,true,1000000,1000).required).toBeNull();
   expect(freedomTarget(1000,0,0,false,1000000,0).monthsToGoal).toBeNull();
   expect(freedomTarget(1000,1.2,0,false,900000,1000).monthsToGoal).toBe(100);
 });
 it('rejects invalid and inconsistent financial inputs', () => {
   expect(validateFinance(state())).toBe(true);
   const s=state();s.assets[0].amount=-1;expect(validateFinance(s)).toBe(false);
   expect(validateFinance({})).toBe(false);
 });
 it('uses three complete months, excludes exceptional categories and future data', () => {
   const record={id:'a',type:'expense' as const,amount:3000,category:'食',date:'2026-09-01',createdAt:'',note:''};
   const result=spendingReference([record,{...record,id:'b',category:'金融保险',amount:220000},{...record,id:'c',date:'2026-10-19',amount:100}], '2026-10-19',['金融保险']);
   expect(result.monthlyExpense).toBe(1000);
   expect(result.excludedTotal).toBe(220000);
   expect(result.monthsWithRecords).toBe(1);
 });
});

it('keeps income interruption and yield decline as independent stress scenarios', () => {
 const s=state();s.settings.essentialMonthly=1000;
 const result=stressTest(s,'2026-10-19',12,1100000,0.5);
 expect(result.remaining).toBe(-112000);
 expect(result.shortfall).toBe(112000);
 expect(result.supportedMonthly).toBeCloseTo(988000*0.007/12);
});
