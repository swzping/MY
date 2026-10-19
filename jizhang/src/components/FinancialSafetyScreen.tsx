import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import Svg, { Circle, Text as SvgText } from 'react-native-svg';
import { ArrowLeft, ChevronDown, ChevronRight, ShieldCheck } from 'lucide-react-native';
import { assetKinds, calculateSafety, distribution, freedomTarget, spendingReference, stressTest, validDate,
 type Asset, type AssetKind, type Debt, type FinanceState } from '../lib/financialSafety';
import { loadFinance, saveFinance } from '../lib/financeStorage';
import { spendingAdvice } from '../lib/spendingAdvice';
import { categoryLabels } from '../data/categories';
import type { Transaction } from '../lib/types';
const money=(n:number)=>new Intl.NumberFormat('zh-CN',{style:'currency',currency:'CNY',maximumFractionDigits:2}).format(n);
const pct=(n:number|null)=>n===null?'待填写':`${(n*100).toFixed(1)}%`;
const colors=['#29765e','#81ad8b','#d3a54a','#729aa9','#9a8ab3','#bd876e','#a5b4a0'];
const id=()=>`${Date.now()}-${Math.random().toString(16).slice(2)}`;
function Button({label,onPress,secondary=false,disabled=false}:{label:string;onPress:()=>void;secondary?:boolean;disabled?:boolean}) {
 return <Pressable accessibilityRole="button" disabled={disabled} accessibilityState={{disabled}} onPress={onPress} style={[s.button,secondary&&s.secondary,disabled&&{opacity:0.5}]}><Text style={[s.buttonText,secondary&&{color:'#29634f'}]}>{label}</Text></Pressable>;
}
function Metric({label,value,caption}:{label:string;value:string;caption?:string}){return <View style={s.metric}><Text style={s.muted}>{label}</Text><Text adjustsFontSizeToFit numberOfLines={1} style={s.value}>{value}</Text>{caption&&<Text style={s.small}>{caption}</Text>}</View>;}
function Section({title,subtitle,children}:{title:string;subtitle?:string;children:React.ReactNode}){return <View style={s.panel}><Text style={s.sectionTitle}>{title}</Text>{subtitle&&<Text style={s.muted}>{subtitle}</Text>}{children}</View>;}
function Field({label,value,onChange,placeholder='',numeric=false}:{label:string;value:string;onChange:(value:string)=>void;placeholder?:string;numeric?:boolean}){return <View style={s.field}><Text style={s.label}>{label}</Text><TextInput accessibilityLabel={label} value={value} onChangeText={onChange} placeholder={placeholder} keyboardType={numeric?'decimal-pad':'default'} style={s.input}/></View>;}
function Toggle({label,value,onChange}:{label:string;value:boolean;onChange:(value:boolean)=>void}){return <View style={s.row}><Text style={s.flexText}>{label}</Text><Switch accessibilityLabel={label} value={value} onValueChange={onChange} trackColor={{true:'#29765e'}}/></View>;}
function amount(text:string,optional=false):number|null {if(!text.trim()){if(optional)return null;throw new Error('请填写必填金额');}const value=Number(text);if(!Number.isFinite(value)||value<0||value>1e12)throw new Error('金额或比例须为有效的非负数字');return value;}
function Composition({items}:{items:ReturnType<typeof distribution>}){
 let used=0;const r=66,c=2*Math.PI*r;
 return <View style={s.allocation}>
  <Svg width={180} height={180} viewBox="0 0 180 180" accessibilityLabel="资产占比分布图">
   <Circle cx={90} cy={90} r={r} stroke="#edf1e9" strokeWidth={23} fill="none"/>
   {items.map((item,i)=>{const offset=-used*c;used+=item.percent;return <Circle key={item.name} cx={90} cy={90} r={r} stroke={colors[i%colors.length]} strokeWidth={23} fill="none" strokeDasharray={`${item.percent*c} ${c}`} strokeDashoffset={offset} rotation={-90} origin="90,90"/>;})}
   <SvgText x={90} y={86} textAnchor="middle" fontSize={13} fill="#718277">资产分布</SvgText>
   <SvgText x={90} y={109} textAnchor="middle" fontSize={22} fontWeight="bold" fill="#203c30">{items.length} 项</SvgText>
  </Svg>
  <View style={s.legend}>{items.map((item,i)=><View key={item.name} style={s.legendRow}><View style={[s.dot,{backgroundColor:colors[i%colors.length]}]}/><View style={{flex:1}}><Text style={s.label}>{item.name}</Text><Text style={s.small}>{money(item.amount)}</Text></View><Text style={s.label}>{pct(item.percent)}</Text></View>)}</View>
 </View>;
}
export default function FinancialSafetyScreen({records,monthlyBudget,onBack,onEditorOpen}:{records:Transaction[];monthlyBudget:number;onBack:()=>void;onEditorOpen:()=>void}) {
 const today=new Date().toLocaleDateString('sv-SE');
 const [state,setState]=useState<FinanceState|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [editor,setEditor]=useState<{kind:'asset'|'debt'|'settings'|'level';key:string}|null>(null);
 const [by,setBy]=useState<'kind'|'channel'>('kind');
 const [expanded,setExpanded]=useState<string|null>(null),[remove,setRemove]=useState<string|null>(null);
 const [months,setMonths]=useState(12),[shock,setShock]=useState('50000'),[drop,setDrop]=useState('0.5'),[cut,setCut]=useState(10);
 async function read(){try{setError('');setState(await loadFinance(AsyncStorage));}catch(e){setError(e instanceof Error?e.message:'财务资料加载失败，请重试');}}
 useEffect(()=>{void read();},[]);
 useEffect(()=>{if(editor)onEditorOpen();},[editor]);
 async function commit(next:FinanceState){setBusy(true);setError('');try{const saved={...next,updatedAt:new Date().toISOString()};await saveFinance(AsyncStorage,saved);setState(saved);setEditor(null);setRemove(null);return true;}catch(e){setError(e instanceof Error?e.message:'保存失败，请重试');return false;}finally{setBusy(false);}}
 const categories=useMemo(()=>[...new Set(records.filter(r=>r.type==='expense').map(r=>r.category))],[records]);
 if(!state)return <View style={s.stack}><Button secondary label="返回收支总览" onPress={onBack}/><Text style={s.muted}>{error||'正在读取财务资料…'}</Text>{!!error&&<Button label="重新读取" onPress={()=>void read()}/>}</View>;
 const summary=calculateSafety(state,today),settings=state.settings;
 const reference=spendingReference(records,today,settings.excludedCategories);
 const advice=spendingAdvice(records,today,monthlyBudget,settings.excludedCategories,cut);
 const shockValid=shock.trim()!==''&&Number.isFinite(Number(shock))&&Number(shock)>=0;
 const dropValid=drop.trim()!==''&&Number.isFinite(Number(drop))&&Number(drop)>=0&&Number(drop)<=100;
 const stress=stressTest(state,today,months,shockValid?Number(shock):0,dropValid?Number(drop):0);
 const hasAssets=state.assets.length>0;
 const configured=settings.essentialMonthly!==null;
 const estimate=freedomTarget(settings.targetMonthly,settings.scenarioYield,settings.inflation,settings.useInflation,summary.investable,settings.monthlySaving);
 return <View style={s.stack}>
  <Pressable accessibilityRole="button" onPress={onBack} style={s.back}><ArrowLeft size={18} color="#29634f"/><Text style={s.link}>返回收支总览</Text></Pressable>
  <View style={s.hero}><View style={s.row}><Text style={s.heroEyebrow}>FINANCIAL WELLBEING</Text><ShieldCheck color="#d6e8c7" size={26}/></View><Text style={s.heroTitle}>财务安全与自由</Text><Text style={s.heroCopy}>先看抵御风险的底气，再规划想要的生活。</Text><Text style={s.heroSmall}>{state.updatedAt?`资料更新于 ${new Date(state.updatedAt).toLocaleString('zh-CN')}`:'从录入真实资产与必要支出开始'}</Text></View>
  {!!error&&<Text accessibilityRole="alert" style={s.error}>{error}</Text>}
  {editor&&<Section title={{asset:'资产资料',debt:'负债资料',settings:'生活与测算设置',level:'生活档位设置'}[editor.kind]}>
    {editor.kind==='asset'&&<AssetForm key={editor.key} initial={state.assets.find(a=>a.id===editor.key)} busy={busy} onCancel={()=>setEditor(null)} onSave={async asset=>{await commit({...state,assets:[...state.assets.filter(a=>a.id!==asset.id),asset]});}}/>}
    {editor.kind==='debt'&&<DebtForm key={editor.key} initial={state.debts.find(d=>d.id===editor.key)} busy={busy} onCancel={()=>setEditor(null)} onSave={async debt=>{await commit({...state,debts:[...state.debts.filter(d=>d.id!==debt.id),debt]});}}/>}
    {editor.kind==='settings'&&<SettingsForm state={state} categories={categories} busy={busy} onCancel={()=>setEditor(null)} onSave={commit}/>}
    {editor.kind==='level'&&<LevelForm initial={state.levels.find(l=>l.id===editor.key)!} busy={busy} onCancel={()=>setEditor(null)} onSave={async level=>{await commit({...state,levels:state.levels.map(l=>l.id===level.id?level:l)});}}/>}
  </Section>}
  <Section title="01  安全概况" subtitle="资产余额独立录入，不将历史账单结余视作存款。">
   {!hasAssets&&<Text style={s.notice}>尚未录入资产，资产相关指标暂不评估。</Text>}
   <View style={s.grid}><Metric label="净资产" value={hasAssets?money(summary.netAssets):'待录入资产'} caption="总资产 − 总负债"/><Metric label="应急资金可支撑" value={!hasAssets||summary.runway===null?'待填写':`${summary.runway.toFixed(1)} 个月`} caption="不依赖工资或投资收益"/><Metric label="负债率" value={!hasAssets?'待填写':summary.debtRatio===null?'无资产，无法计算':pct(summary.debtRatio)}/><Metric label="预计被动收入覆盖率" value={hasAssets?pct(summary.passiveCoverage):'待录入资产'} caption={`目标 ${money(settings.targetMonthly)}/月`}/></View>
   <Text style={s.small}>预计被动收入按已填写的年净收益率折算，并非每月实际到账。{summary.unknownYieldAssets>0?`${summary.unknownYieldAssets} 项资产未填收益率，暂未计入收益。`:''}</Text>
   {configured&&hasAssets&&summary.runway!==null&&summary.runway<settings.reserveMonths&&<Text style={s.warning}>⚠ 应急资金可支撑 {summary.runway.toFixed(1)} 个月，低于你设置的 {settings.reserveMonths} 个月目标。优先补充可随时取用的资金。</Text>}
   <Button secondary label="设置生活支出与收益假设" onPress={()=>setEditor({kind:'settings',key:'settings'})}/>
   <Text style={s.small}>必要月支出 {settings.essentialMonthly===null?'待填写':money(settings.essentialMonthly)}（不含月供） · 月供 {money(summary.monthlyPayments)}</Text>
  </Section>
  <Section title="02  资产放在哪里" subtitle="按资产类型或持有渠道查看占比。金额按当前余额填写。">
   <View style={s.rowStart}>{(['kind','channel'] as const).map(value=><Chip key={value} label={value==='kind'?'资产类型':'持有渠道'} active={by===value} onPress={()=>setBy(value)}/>)}</View>
   {hasAssets?<Composition items={distribution(state.assets,by)}/>:<Text style={s.empty}>添加银行存款、现金或投资账户，建立你的资产全貌。</Text>}
   {state.assets.map(a=><View key={a.id} style={s.item}><Pressable accessibilityRole="button" accessibilityLabel={`编辑资产${a.name}`} onPress={()=>setEditor({kind:'asset',key:a.id})} style={s.row}><View style={{flex:1}}><Text style={s.label}>{a.name}</Text><Text style={s.small}>{assetKinds[a.kind]} · {a.channel} · {a.liquid?'可随时取用':'非即时可用'}</Text><Text style={s.small}>{a.investable?'参与自由目标':'不参与自由目标'} · 年净收益率 {a.annualYield===null?'未填写':`${a.annualYield}%`}{a.maturity?` · ${a.maturity} 到期`:''}</Text></View><Text style={s.amount}>{money(a.amount)}</Text><ChevronRight size={16} color="#789084"/></Pressable><RemoveControl id={a.id} name={a.name} active={remove} setActive={setRemove} busy={busy} onRemove={()=>void commit({...state,assets:state.assets.filter(x=>x.id!==a.id)})}/></View>)}
   <Button label="＋ 添加资产" onPress={()=>setEditor({kind:'asset',key:id()})}/>
  </Section>
  <Section title="03  负债与还款压力">
   <View style={s.grid}><Metric label="负债总额" value={money(summary.totalDebts)}/><Metric label="每月还款" value={money(summary.monthlyPayments)}/><Metric label="月供收入比" value={settings.stableMonthlyIncome===0?'无稳定收入':pct(summary.paymentRatio)}/><Metric label="未来12个月到期余额" value={money(summary.due12Months)}/></View>
   <Text style={s.small}>到期余额按当前剩余本金显示，尚未扣除未来月供中的本金；请另行准备到期款。未录入负债时暂按 0 计算。</Text>
   {summary.overdueDebt>0&&<Text style={s.warning}>⚠ 有 {money(summary.overdueDebt)} 负债已超过登记到期日，请确认余额是否已更新。</Text>}
   {summary.due12Months>summary.liquid&&<Text style={s.warning}>⚠ 未来12个月到期余额高于当前可随时使用的资产，请提前安排还款资金。</Text>}
   {summary.paymentRatio!==null&&summary.paymentRatio>=0.5&&<Text style={s.warning}>⚠ 每月还款占稳定收入 {pct(summary.paymentRatio)}，请结合必要生活支出检查现金流。</Text>}
   {state.debts.map(d=><View key={d.id} style={s.item}><Pressable accessibilityRole="button" accessibilityLabel={`编辑负债${d.name}`} style={s.row} onPress={()=>setEditor({kind:'debt',key:d.id})}><View style={{flex:1}}><Text style={s.label}>{d.name}</Text><Text style={s.small}>利率 {d.annualRate===null?'未填写':`${d.annualRate}%`} · 月还款 {money(d.monthlyPayment)}{d.maturity?` · ${d.maturity} 到期`:''}</Text></View><Text style={s.amount}>{money(d.balance)}</Text><ChevronRight size={16} color="#789084"/></Pressable><RemoveControl id={d.id} name={d.name} active={remove} setActive={setRemove} busy={busy} onRemove={()=>void commit({...state,debts:state.debts.filter(x=>x.id!==d.id)})}/></View>)}
   <Button secondary label="＋ 添加负债" onPress={()=>setEditor({kind:'debt',key:id()})}/>
  </Section>
  <Section title="04  财务自由阶梯" subtitle="档位越高代表生活支出越高，不代表风险更低。">
   <View style={s.soft}><Text style={s.label}>{settings.useInflation?'考虑通胀的购买力模型':'名义本金不减少模型'}</Text><Text style={s.muted}>年净收益率 {settings.scenarioYield}%{settings.useInflation?` · 通胀 ${settings.inflation}%`:''}，均为可调整假设，不是收益承诺。</Text><Text style={s.small}>先预留应急金 {configured?money(summary.reserveTarget):'待确认'}、近期大额支出 {money(settings.plannedExpense)}，再计算投资本金。自住房不计入。</Text><Text style={s.label}>可用于目标的本金：{hasAssets?money(summary.investable):'待录入资产'}</Text>{!configured&&<Text style={s.warning}>尚未填写必要支出，应急金尚未扣除，以下完成度和可支持金额仅为预览。</Text>}<Text style={s.muted}>当前预计可支持：{hasAssets?`${money(estimate.supportedMonthly)}/月`:'待录入资产'}</Text></View>
   {state.levels.map((level,i)=>{const target=freedomTarget(level.monthly,settings.scenarioYield,settings.inflation,settings.useInflation,summary.investable,settings.monthlySaving);return <View key={level.id} style={s.level}><Pressable accessibilityRole="button" accessibilityState={{expanded:expanded===level.id}} onPress={()=>setExpanded(expanded===level.id?null:level.id)} style={s.row}><View style={s.levelNumber}><Text style={s.link}>{String(i+1).padStart(2,'0')}</Text></View><View style={{flex:1}}><Text style={s.label}>{level.name} · {money(level.monthly)}/月</Text><Text style={s.small}>{target.required===null?'当前收益假设不能持续覆盖支出':`目标本金 ${money(target.required)}`}</Text></View>{expanded===level.id?<ChevronDown size={18} color="#29765e"/>:<ChevronRight size={18} color="#29765e"/>}</Pressable><View style={s.track}><View style={[s.fill,{width:`${hasAssets&&target.progress!==null?Math.min(100,target.progress*100):0}%`}]}/></View>{expanded===level.id&&<View style={s.stackSmall}><Text style={s.muted}>完成度：{hasAssets?pct(target.progress):'待录入资产'} · 尚差：{!hasAssets?'待录入资产':target.gap===null?'无法计算':money(target.gap)}</Text><Text style={s.small}>按每月新增储蓄 {settings.monthlySaving===null?'待填写':money(settings.monthlySaving)}，预计 {hasAssets&&target.monthsToGoal!==null?`${target.monthsToGoal} 个月`:'暂无法估算'}。采用不计复利、不变收入支出的静态估算。</Text><Button secondary label={`调整${level.name}档位`} onPress={()=>setEditor({kind:'level',key:level.id})}/></View>}</View>;})}
   <Text style={s.small}>名义模型：所需本金＝月支出 × 12 ÷ 年净收益率。考虑通胀时使用实际收益率；实际收益率不为正时，不给出永久覆盖目标。</Text>
  </Section>
  <Section title="05  压力测试" subtitle="假设工资与被动收入全部中断，优先检查现金能否撑住。">
   <View style={s.rowStart}>{[6,12,24].map(n=><Chip key={n} label={`${n} 个月`} active={months===n} onPress={()=>setMonths(n)}/>)}</View>
   <Field label="一次性突发支出（元）" value={shock} onChange={setShock} numeric/>
   <Field label="收益率下降（百分点）" value={drop} onChange={setDrop} numeric/>
   {(!shockValid||!dropValid)?<Text style={s.error}>请输入有效的非负金额，收益下降须在 0–100 个百分点之间。</Text>:<View style={s.soft}><Text style={s.label}>{!hasAssets||stress.remaining===null?'录入资产及必要支出后查看结果':stress.remaining>=0?`${months} 个月后应急资金剩余 ${money(stress.remaining)}`:`${months} 个月内存在 ${money(stress.shortfall!)} 资金缺口`}</Text><Text style={s.muted}>独立收益情景：年净收益率降至 {stress.newYield.toFixed(2)}% 后，可支持 {hasAssets?money(stress.supportedMonthly):'待填写'} /月。</Text><Text style={s.small}>中断情景计入必要支出和月供，不计未来到期的整笔本金；收益情景不叠加失业期消耗。</Text></View>}
  </Section>
  <Section title="06  支出提醒与节省建议" subtitle="先看实际变化，再决定哪些支出值得调整。">
   {advice.budget&&<View style={advice.budget.ratio>=0.8?s.warningBox:s.soft}><Text style={s.label}>{advice.budget.ratio>1?'⚠ 本月预算已超出':advice.budget.ratio===1?'⚠ 本月预算已用完':advice.budget.ratio>=0.8?'⚠ 本月预算已用到八成以上':'本月预算使用情况'}</Text><Text style={s.muted}>截至 {today}，已支出 {money(advice.budget.spent)}，占预算 {pct(advice.budget.ratio)}。{advice.budget.ratio>1?`超出 ${money(advice.budget.spent-advice.budget.limit)}。`:''}</Text><Text style={s.small}>预算包含一次性支出，先核对大额账单，再决定是否减少日常支出。</Text></View>}
   <Text style={s.label}>{advice.latest} 完整月份支出变化</Text>
   {advice.trends.length===0?<Text style={s.muted}>{advice.baselineMonths<2?'历史完整月数据不足，暂不判断支出上涨。':'未发现同时上涨至少30%且多支出至少100元的类别。'}</Text>:advice.trends.map(t=><View key={t.category} style={s.warningBox}><Text style={s.label}>⚠ {categoryLabels[t.category]??t.category}：比历史月均多 {money(t.increase)}</Text><Text style={s.small}>上月 {money(t.current)}，此前有记录的 {advice.baselineMonths} 个月均值 {money(t.average)}。先核对是否为一次性或必要支出，再决定调整。</Text></View>)}
   <Text style={s.label}>可优先检查的弹性支出</Text><Text style={s.small}>按最近3个完整月平均，试算减少比例。类别仅作线索，是否能减由你决定；医疗、基本餐饮、还款不在自动建议内。</Text>
   <View style={s.rowStart}>{[10,20,30].map(n=><Chip key={n} label={`减少 ${n}%`} active={cut===n} onPress={()=>setCut(n)}/>)}</View>
   {advice.cuts.length===0?<Text style={s.muted}>暂无可识别的弹性支出，不强行给出削减建议。</Text>:advice.cuts.map(c=><View key={c.category+c.subcategory} style={s.item}><Text style={s.label}>{categoryLabels[c.category]??c.category}{c.subcategory?` · ${c.subcategory}`:''}</Text><Text style={s.muted}>月均 {money(c.monthlyAverage)} → 减少 {cut}% 后预计节省 <Text style={s.link}>{money(c.monthlySaving)}/月</Text></Text></View>)}
   {advice.monthsWithRecords<3&&<Text style={s.warning}>最近3个月仅 {advice.monthsWithRecords} 个月有账单，空月按0计算，节省估算可能偏低。</Text>}
   <View style={s.soft}><Text style={s.label}>必要月支出参考：{money(reference.monthlyExpense)}</Text><Text style={s.small}>区间 {reference.months[2]} 至 {reference.months[0]}，按3个月平均；已排除 {money(reference.excludedTotal)}。默认排除金融保险、居家物业、旧版住房和家庭，请在设置中按你的实际情况调整，再填写必要月支出。</Text><Text style={s.small}>历史账面月均结余 {money(reference.monthlyNet)}；它不等同于未来可持续储蓄额。</Text></View>
  </Section>
  <Text style={s.footer}>资料仅保存在当前浏览器／设备，与账单 Excel 分开保存。更换浏览器不会自动同步。</Text>
 </View>;
}
function Chip({label,active,onPress}:{label:string;active:boolean;onPress:()=>void}){return <Pressable accessibilityRole="button" accessibilityState={{selected:active}} onPress={onPress} style={[s.chip,active&&s.chipActive]}><Text style={[s.small,active&&s.link]}>{label}</Text></Pressable>;}
function RemoveControl({id,name,active,setActive,busy,onRemove}:{id:string;name:string;active:string|null;setActive:(id:string|null)=>void;busy:boolean;onRemove:()=>void}){return active===id?<View style={s.stackSmall}><Text style={s.warning}>从财务资料移除“{name}”？账单记录不受影响。</Text><View style={s.rowStart}><Button disabled={busy} label="确认移除" onPress={onRemove}/><Button secondary label="取消" onPress={()=>setActive(null)}/></View></View>:<Pressable accessibilityRole="button" accessibilityLabel={`移除${name}`} onPress={()=>setActive(id)}><Text style={s.delete}>移除</Text></Pressable>;}
function FormActions({busy,onCancel,onSave,error}:{busy:boolean;onCancel:()=>void;onSave:()=>void;error:string}){return <View style={s.stackSmall}>{!!error&&<Text accessibilityRole="alert" style={s.error}>{error}</Text>}<View style={s.rowStart}><Button disabled={busy} label={busy?'保存中…':'保存资料'} onPress={onSave}/><Button secondary disabled={busy} label="取消" onPress={onCancel}/></View></View>;}
function AssetForm({initial,busy,onCancel,onSave}:{initial?:Asset;busy:boolean;onCancel:()=>void;onSave:(a:Asset)=>Promise<void>}) {
 const [name,N]=useState(initial?.name??''),[channel,C]=useState(initial?.channel??''),[value,V]=useState(initial?String(initial.amount):''),[yieldValue,Y]=useState(initial?.annualYield==null?'':String(initial.annualYield)),[kind,K]=useState<AssetKind>(initial?.kind??'deposit'),[liquid,L]=useState(initial?.liquid??true),[investable,I]=useState(initial?.investable??true),[maturity,M]=useState(initial?.maturity??''),[error,E]=useState('');
 async function submit(){try{E('');if(!name.trim()||!channel.trim())throw new Error('请填写资产名称和持有渠道');if(!validDate(maturity))throw new Error('到期日请填写 YYYY-MM-DD，或留空');const annualYield=amount(yieldValue,true);if(annualYield!==null&&annualYield>100)throw new Error('收益率须在0–100%之间');await onSave({id:initial?.id??id(),name:name.trim(),channel:channel.trim(),amount:amount(value)!,annualYield,kind,liquid:kind==='home'?false:liquid,investable:kind==='home'?false:investable,maturity,updatedAt:new Date().toISOString()});}catch(e){E((e as Error).message);}}
 return <View style={s.stackSmall}><Field label="资产名称" value={name} onChange={N} placeholder="例如：应急存款"/><Field label="持有渠道" value={channel} onChange={C} placeholder="例如：工商银行"/><Text style={s.label}>资产类型</Text><View style={s.rowStart}>{Object.entries(assetKinds).map(([key,label])=><Chip key={key} label={label} active={kind===key} onPress={()=>{K(key as AssetKind);if(key==='home'){L(false);I(false);}else if(key==='fund'||key==='property'){L(false);Y('');}}}/>)}</View><Field label="当前余额（元）" value={value} onChange={V} numeric/><Field label="预计年净收益率（%）" value={yieldValue} onChange={Y} placeholder="未知请留空；不是收益保证" numeric/><Field label="到期日（可选）" value={maturity} onChange={M} placeholder="YYYY-MM-DD"/>{kind!=='home'&&<><Toggle label="可随时取用且本金稳定（计入应急资金）" value={liquid} onChange={L}/><Toggle label="参与财务自由本金计算" value={investable} onChange={I}/></>}<Text style={s.small}>基金股票价格会波动，不宜视为稳定的应急金。自住房仅计入净资产。</Text><FormActions busy={busy} onCancel={onCancel} onSave={()=>void submit()} error={error}/></View>;
}
function DebtForm({initial,busy,onCancel,onSave}:{initial?:Debt;busy:boolean;onCancel:()=>void;onSave:(d:Debt)=>Promise<void>}) {
 const [name,N]=useState(initial?.name??''),[balance,B]=useState(initial?String(initial.balance):''),[rate,R]=useState(initial?.annualRate==null?'':String(initial.annualRate)),[monthly,P]=useState(initial?String(initial.monthlyPayment):''),[maturity,M]=useState(initial?.maturity??''),[error,E]=useState('');
 async function submit(){try{E('');if(!name.trim())throw new Error('请填写负债名称');if(!validDate(maturity))throw new Error('到期日请填写 YYYY-MM-DD，或留空');const annualRate=amount(rate,true);if(annualRate!==null&&annualRate>100)throw new Error('年利率须在0–100%之间');await onSave({id:initial?.id??id(),name:name.trim(),balance:amount(balance)!,annualRate,monthlyPayment:amount(monthly)!,maturity});}catch(e){E((e as Error).message);}}
 return <View style={s.stackSmall}><Field label="负债名称" value={name} onChange={N} placeholder="例如：住房贷款"/><Field label="剩余本金（元）" value={balance} onChange={B} numeric/><Field label="年利率（%，可选）" value={rate} onChange={R} numeric/><Field label="每月还款（元）" value={monthly} onChange={P} placeholder="不按月还款填0" numeric/><Field label="最终到期日（可选）" value={maturity} onChange={M} placeholder="YYYY-MM-DD"/><FormActions busy={busy} onCancel={onCancel} onSave={()=>void submit()} error={error}/></View>;
}
const settingFields=[['essentialMonthly','必要月支出，不含还款（元）',true],['stableMonthlyIncome','稳定月收入（元）',true],['monthlySaving','可持续每月新增储蓄（元）',true],['reserveMonths','应急储备目标（月）',false],['plannedExpense','近期大额支出准备金（元）',false],['targetMonthly','被动收入覆盖目标（元/月）',false],['scenarioYield','自由目标年净收益率假设（%）',false],['inflation','通胀率假设（%）',false]] as const;
function SettingsForm({state,categories,busy,onCancel,onSave}:{state:FinanceState;categories:string[];busy:boolean;onCancel:()=>void;onSave:(s:FinanceState)=>Promise<boolean>}){
 const [values,V]=useState<Record<string,string>>(()=>Object.fromEntries(settingFields.map(([key])=>[key,state.settings[key]===null?'':String(state.settings[key])]))),[inflation,I]=useState(state.settings.useInflation),[excluded,X]=useState(state.settings.excludedCategories),[error,E]=useState('');
 async function submit(){try{E('');const settings={...state.settings,useInflation:inflation,excludedCategories:excluded};for(const [key,,optional] of settingFields)(settings as unknown as Record<string,unknown>)[key]=amount(values[key],optional);if(settings.targetMonthly<=0||settings.scenarioYield>100||settings.inflation>100||settings.reserveMonths>120)throw new Error('目标月支出须大于0；收益率和通胀率不超过100%，应急月数不超过120');await onSave({...state,settings});}catch(e){E((e as Error).message);}}
 return <View style={s.stackSmall}>{settingFields.map(([key,label,optional])=><Field key={key} label={label} value={values[key]} onChange={text=>V({...values,[key]:text})} placeholder={optional?'未知可留空，0表示明确没有':''} numeric/>)}<Toggle label="自由目标考虑通胀" value={inflation} onChange={I}/><Text style={s.label}>月支出参考与趋势分析排除的大类</Text><Text style={s.small}>已选中类别不参与日常支出参考。若住房类含房租，请按实际需要取消排除；医疗及家庭支出不可直接当作可削减项目。</Text><View style={s.rowStart}>{categories.map(category=><Chip key={category} label={categoryLabels[category]??category} active={excluded.includes(category)} onPress={()=>X(excluded.includes(category)?excluded.filter(x=>x!==category):[...excluded,category])}/>)}</View><FormActions busy={busy} onCancel={onCancel} onSave={()=>void submit()} error={error}/></View>;
}
function LevelForm({initial,busy,onCancel,onSave}:{initial:FinanceState['levels'][number];busy:boolean;onCancel:()=>void;onSave:(l:FinanceState['levels'][number])=>Promise<void>}){const [name,N]=useState(initial.name),[monthly,M]=useState(String(initial.monthly)),[error,E]=useState('');async function submit(){try{E('');const value=amount(monthly)!;if(!name.trim()||value<=0)throw new Error('请填写名称和大于0的月支出');await onSave({...initial,name:name.trim(),monthly:value});}catch(e){E((e as Error).message);}}return <View style={s.stackSmall}><Field label="档位名称" value={name} onChange={N}/><Field label="目标月支出（元）" value={monthly} onChange={M} numeric/><FormActions busy={busy} onCancel={onCancel} onSave={()=>void submit()} error={error}/></View>;}
const s=StyleSheet.create({
 stack:{gap:18},stackSmall:{gap:12},back:{flexDirection:'row',alignItems:'center',gap:8,paddingVertical:8},link:{color:'#29634f',fontWeight:'700'},
 hero:{backgroundColor:'#244f40',borderRadius:14,padding:24,gap:12},heroEyebrow:{color:'#c0d4ba',fontSize:11,letterSpacing:2},heroTitle:{color:'#fffdf5',fontSize:30,fontWeight:'800'},heroCopy:{color:'#e4edde',fontSize:15,lineHeight:24},heroSmall:{color:'#b8d1bd',fontSize:12},
 panel:{backgroundColor:'#fffef9',borderWidth:1,borderColor:'#dce5db',borderRadius:12,padding:18,gap:14},sectionTitle:{fontSize:19,fontWeight:'800',color:'#203c30'},muted:{fontSize:13,color:'#687c70',lineHeight:21},small:{fontSize:12,color:'#728278',lineHeight:19},label:{fontSize:14,fontWeight:'600',color:'#264536',lineHeight:22},amount:{fontSize:15,fontWeight:'700',color:'#264536',flexShrink:1},
 grid:{flexDirection:'row',flexWrap:'wrap',gap:10},metric:{flexGrow:1,flexBasis:'46%',minWidth:120,padding:14,backgroundColor:'#f2f5ed',borderRadius:9,gap:7},value:{fontSize:23,fontWeight:'800',color:'#264536'},
 row:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:10},rowStart:{flexDirection:'row',flexWrap:'wrap',alignItems:'center',gap:8},flexText:{flex:1,color:'#264536',fontSize:14,lineHeight:22},
 button:{backgroundColor:'#29765e',borderRadius:8,paddingHorizontal:16,paddingVertical:12,alignItems:'center'},secondary:{backgroundColor:'#edf3e9',borderWidth:1,borderColor:'#cbdcca'},buttonText:{color:'white',fontSize:14,fontWeight:'700'},
 field:{gap:6},input:{borderWidth:1,borderColor:'#cbd8cc',borderRadius:8,padding:12,minHeight:44,color:'#203c30',fontSize:15,backgroundColor:'#fff'},
 chip:{paddingHorizontal:12,paddingVertical:8,borderRadius:7,borderWidth:1,borderColor:'#dce5db',backgroundColor:'#fff'},chipActive:{backgroundColor:'#e9f2e5',borderColor:'#478366'},
 allocation:{flexDirection:'row',flexWrap:'wrap',alignItems:'center',justifyContent:'center',gap:14},legend:{flex:1,minWidth:150,gap:12},legendRow:{flexDirection:'row',alignItems:'center',gap:8},dot:{width:9,height:9,borderRadius:5},
 item:{borderTopWidth:1,borderTopColor:'#e6ece2',paddingTop:14,gap:8},delete:{color:'#9b6655',fontSize:12,alignSelf:'flex-end',paddingVertical:6},
 soft:{padding:14,backgroundColor:'#f1f5ed',borderRadius:8,gap:8},warningBox:{padding:14,backgroundColor:'#fbf2dd',borderRadius:8,gap:7},warning:{fontSize:13,color:'#986a25',lineHeight:21},error:{color:'#ac443b',fontSize:13,lineHeight:22},notice:{fontSize:13,color:'#986a25',backgroundColor:'#fbf2dd',padding:12,borderRadius:8,lineHeight:22},
 level:{borderWidth:1,borderColor:'#e1e7dc',borderRadius:10,padding:14,gap:12},levelNumber:{height:34,width:34,borderRadius:17,backgroundColor:'#e9f1e2',justifyContent:'center',alignItems:'center'},track:{height:5,backgroundColor:'#e8eee2',borderRadius:3,overflow:'hidden'},fill:{height:5,backgroundColor:'#4e8b67'},empty:{color:'#819083',fontSize:14,lineHeight:24,paddingVertical:16},footer:{color:'#849185',fontSize:12,textAlign:'center',lineHeight:20,paddingBottom:16}
});
