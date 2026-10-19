import { expect,it } from 'vitest';
import {loadFinance,saveFinance} from './financeStorage';
import {defaultFinance} from './financialSafety';
it('persists finance separately and refuses to overwrite corrupt data during loading',async()=>{
 let text:string|null=null;const storage={getItem:async()=>text,setItem:async(_k:string,v:string)=>{text=v;}};
 expect((await loadFinance(storage)).assets).toEqual([]);
 const state=defaultFinance();state.settings.targetMonthly=2000;await saveFinance(storage,state);
 expect(await loadFinance(storage)).toEqual(state);
 text='bad';await expect(loadFinance(storage)).rejects.toThrow();expect(text).toBe('bad');
});
