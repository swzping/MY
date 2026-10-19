import { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import type { Transaction } from '../lib/types';
import { savingsSummary, savingsTimeline } from '../lib/savingsTimeline';

const money = (n: number) => new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(n);
const duration = (months: number | null) => months === null ? '暂时无法达到' : months === 0 ? '已达到' : `${Math.floor(months / 12) ? `${Math.floor(months / 12)} 年` : ''}${months % 12 ? ` ${months % 12} 个月` : ''}`;

export default function SavingsTimelineScreen({ records, onBack }: { records: Transaction[]; onBack: () => void }) {
  const summary = savingsSummary(records, new Date().toLocaleDateString('sv-SE'));
  const [override, setOverride] = useState<string | null>(null);
  const initial = Math.max(0, summary.balance);
  const capital = override === null ? initial : Number(override);
  const valid = override === null || (override.trim() !== '' && Number.isFinite(capital) && capital >= 0 && capital <= 1e12);
  return <View style={s.page}>
    <Pressable accessibilityRole="button" onPress={onBack}><Text style={s.back}>‹ 返回收支总览</Text></Pressable>
    <View style={s.hero}>
      <Text style={s.eyebrow}>按现在的收支，还要存多久？</Text>
      <Text style={s.heroNumber}>每月可存 ¥{money(summary.saving)}</Text>
      <Text style={s.heroNote}>{summary.months[2]} 至 {summary.months[0]}，近 3 个完整月平均</Text>
      <View style={s.totals}><Text style={s.heroNote}>月收入 ¥{money(summary.income)}</Text><Text style={s.heroNote}>月支出 ¥{money(summary.expense)}</Text></View>
    </View>
    {summary.recordedMonths < 3 && <Text style={s.warning}>近 3 个月只有 {summary.recordedMonths} 个月有账单，空月按 0 计算，估算可能有偏差。</Text>}
    <View style={s.card}>
      <Text style={s.label}>现在已有多少存款（元）</Text>
      <TextInput accessibilityLabel="现有存款（元）" keyboardType="decimal-pad" style={s.input} value={override ?? initial.toFixed(2)} onChangeText={setOverride}/>
      <Text style={s.note}>默认按累计账面结余 ¥{money(summary.balance)} 估算{summary.balance < 0 ? '，负结余暂按 0 元本金' : ''}。不等于实际存款，可以直接改成实际金额；修改仅用于本次测算。</Text>
      {!valid && <Text style={s.warning}>请输入有效的非负存款金额。</Text>}
    </View>
    <View style={s.card}>
      <Text style={s.title}>希望每月有多少生活费</Text>
      <Text style={s.note}>按年净收益率 1.2% 假设：100 万本金约支持每月 1000 元。</Text>
      {[1000, 2000, 3000, 5000].map(monthly => {
        const result = savingsTimeline(monthly, capital, summary.saving);
        return <View key={monthly} style={s.item}>
          <View style={s.row}><Text style={s.label}>每月 ¥{money(monthly)}</Text><Text style={s.time}>{valid ? duration(result.months) : '待填写存款'}</Text></View>
          <Text style={s.note}>需要本金 {money(result.target / 10000)} 万{valid ? ` · 还差 ¥${money(result.gap)}` : ''}</Text>
        </View>;
      })}
      {summary.saving <= 0 && <Text style={s.warning}>目前月均没有结余，尚未达到的目标无法推算到达时间。需要先增加收入或降低支出。</Text>}
    </View>
    <Text style={s.note}>还需月数＝（目标本金 − 现有存款）÷ 当前月均结余，向上取整。档位代表未来希望覆盖的生活费，存钱速度仍按现在的实际收支计算。包含全部账单支出，未剔除一次性大额支出；不计存钱期间的复利、通胀及未来收支变化。1.2% 是测算假设，不是收益承诺。</Text>
  </View>;
}

const s = StyleSheet.create({
 page: { gap: 18, paddingBottom: 24 }, back: { color: '#29634f', fontSize: 15, fontWeight: '600', paddingVertical: 8 },
 hero: { backgroundColor: '#28634f', padding: 22, borderRadius: 22, gap: 12 },
 eyebrow: { color: '#e0eadd', fontSize: 16 }, heroNumber: { color: '#fff', fontSize: 27, fontWeight: '700' },
 heroNote: { color: '#e0eadd', fontSize: 13, lineHeight: 21 }, totals: { flexDirection: 'row', flexWrap: 'wrap', gap: 16 },
 card: { padding: 20, borderRadius: 20, backgroundColor: '#fffef9', borderColor: '#e0e6dc', borderWidth: 1, gap: 12 },
 title: { color: '#203c30', fontSize: 19, fontWeight: '700' }, label: { color: '#203c30', fontSize: 16, fontWeight: '600' },
 note: { color: '#788479', fontSize: 12, lineHeight: 21 }, input: { borderColor: '#cad7c9', borderWidth: 1, borderRadius: 10, padding: 12, fontSize: 20, color: '#203c30' },
 item: { borderTopWidth: 1, borderTopColor: '#e7ece3', paddingTop: 16, gap: 7 }, row: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 10 },
 time: { color: '#29634f', fontSize: 20, fontWeight: '700' }, warning: { color: '#956a23', fontSize: 13, lineHeight: 22 },
});
