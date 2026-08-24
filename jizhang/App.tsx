import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SplashScreen from "expo-splash-screen";
import {
  BarChart3,
  CalendarDays,
  Home,
  LineChart,
  ListPlus,
  PiggyBank,
  Plus,
  ReceiptText,
  Trash2,
  WalletCards,
} from "lucide-react-native";
import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  ImageBackground,
  Pressable,
  SafeAreaView,
  ScrollView,
  StatusBar,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import {
  categoryLabels,
  expenseCategories,
  incomeCategories,
} from "./src/data/categories";
import { sampleData } from "./src/data/sampleData";
import {
  buildSevenDayTrend,
  getBudgetStatus,
  getCategoryBudgetStatuses,
  getCategorySpending,
  getMonthlyTotals,
  getRecentRecords,
  validateRecordInput,
} from "./src/lib/analytics";
import { loadAppData, saveAppData } from "./src/lib/storage";
import type { AppData, BudgetLevel, Transaction, TransactionType } from "./src/lib/types";

type Tab = "home" | "record" | "budget" | "analysis";

type RecordForm = {
  type: TransactionType;
  amount: string;
  category: string;
  date: string;
  note: string;
};

const today = new Date().toISOString().slice(0, 10);
const money = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  maximumFractionDigits: 0,
});

const tabItems = [
  { id: "home", label: "首页", icon: Home },
  { id: "record", label: "记账", icon: ListPlus },
  { id: "budget", label: "预算", icon: PiggyBank },
  { id: "analysis", label: "分析", icon: BarChart3 },
] as const;

const startupSlides = [
  require("./assets/splash/splash-1.jpg"),
  require("./assets/splash/splash-2.jpg"),
  require("./assets/splash/splash-3.jpg"),
] as const;
const startupSlideDurationMs = 2500;

void SplashScreen.preventAutoHideAsync().catch(() => {
  // The native splash may already be hidden in development reloads.
});

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("home");
  const [showStartup, setShowStartup] = useState(true);
  const [startupImageReady, setStartupImageReady] = useState(false);
  const [startupSlide, setStartupSlide] = useState(0);
  const [data, setData] = useState<AppData>(sampleData);
  const [isReady, setIsReady] = useState(false);
  const [form, setForm] = useState<RecordForm>({
    type: "expense",
    amount: "",
    category: "Food",
    date: today,
    note: "",
  });
  const [budgetDraft, setBudgetDraft] = useState(String(sampleData.budget.monthlyBudget));

  useEffect(() => {
    let active = true;

    loadAppData(AsyncStorage).then((loadedData) => {
      if (!active) return;
      setData(loadedData);
      setBudgetDraft(String(loadedData.budget.monthlyBudget));
      setIsReady(true);
    });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (isReady) {
      saveAppData(AsyncStorage, data);
    }
  }, [data, isReady]);

  useEffect(() => {
    if (showStartup) {
      return undefined;
    }

    let unsubscribe: (() => void) | undefined;
    let cancelled = false;
    const setupTimer = setTimeout(() => {
      try {
        const { handleInitialNotification, scheduleHalfHourRecordReminder, subscribeToNotificationPress } =
          require("./src/lib/notifications") as typeof import("./src/lib/notifications");

        if (cancelled) {
          return;
        }

        void scheduleHalfHourRecordReminder().catch((error) => {
          console.warn("Failed to schedule record reminder notification", error);
        });

        void handleInitialNotification((tab) => setActiveTab(tab)).catch((error) => {
          console.warn("Failed to handle initial notification", error);
        });

        unsubscribe = subscribeToNotificationPress((tab) => setActiveTab(tab));
      } catch (error) {
        console.warn("Failed to load notification module", error);
      }
    }, 1200);

    return () => {
      cancelled = true;
      clearTimeout(setupTimer);
      unsubscribe?.();
    };
  }, [showStartup]);

  useEffect(() => {
    if (!showStartup) {
      return undefined;
    }

    const slideTimer = setInterval(() => {
      setStartupSlide((current) => Math.min(current + 1, startupSlides.length - 1));
    }, startupSlideDurationMs);
    const finishTimer = setTimeout(() => {
      setShowStartup(false);
    }, startupSlides.length * startupSlideDurationMs);

    return () => {
      clearInterval(slideTimer);
      clearTimeout(finishTimer);
    };
  }, [showStartup]);

  useEffect(() => {
    if (!startupImageReady) {
      return;
    }

    void SplashScreen.hideAsync().catch(() => {
      // Ignore development reload races.
    });
  }, [startupImageReady]);

  const metrics = useMemo(() => {
    return {
      totals: getMonthlyTotals(data.records, today),
      budget: getBudgetStatus(data.records, data.budget, today),
      categories: getCategorySpending(data.records, today),
      categoryBudgets: getCategoryBudgetStatuses(data.records, data.budget, today),
      trend: buildSevenDayTrend(data.records, today),
      recent: getRecentRecords(data.records, 6),
    };
  }, [data]);

  if (showStartup) {
    return (
      <StartupCarousel
        activeSlide={startupSlide}
        onFirstImageReady={() => setStartupImageReady(true)}
        onSkip={() => setShowStartup(false)}
      />
    );
  }

  function setFormType(type: TransactionType) {
    setForm((current) => ({
      ...current,
      type,
      category: type === "expense" ? "Food" : "Salary",
    }));
  }

  function addRecord() {
    const amount = Number(form.amount);
    const errors = validateRecordInput({
      amount,
      category: form.category,
      date: form.date,
    });

    if (errors.length > 0) {
      Alert.alert("账单还不能保存", errors.join("\n"));
      return;
    }

    const record: Transaction = {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      type: form.type,
      amount,
      category: form.category,
      date: form.date,
      note: form.note.trim(),
      createdAt: new Date().toISOString(),
    };

    setData((current) => ({ ...current, records: [record, ...current.records] }));
    setForm({
      type: "expense",
      amount: "",
      category: "Food",
      date: today,
      note: "",
    });
    setActiveTab("home");
  }

  function deleteRecord(id: string) {
    setData((current) => ({
      ...current,
      records: current.records.filter((record) => record.id !== id),
    }));
  }

  function saveMonthlyBudget() {
    const monthlyBudget = Math.max(0, Number(budgetDraft) || 0);
    setData((current) => ({
      ...current,
      budget: { ...current.budget, monthlyBudget },
    }));
    setBudgetDraft(String(monthlyBudget));
  }

  function updateCategoryBudget(category: string, value: string) {
    const amount = Math.max(0, Number(value) || 0);
    setData((current) => ({
      ...current,
      budget: {
        ...current.budget,
        categoryBudgets: {
          ...current.budget.categoryBudgets,
          [category]: amount,
        },
      },
    }));
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#f7faf9" />
      <View style={styles.app}>
        <View style={styles.topBar}>
          <View>
            <Text style={styles.eyebrow}>个人账本</Text>
            <Text style={styles.title}>{getTitle(activeTab)}</Text>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="新增账单"
            style={styles.iconButton}
            onPress={() => setActiveTab("record")}
          >
            <Plus color="#ffffff" size={20} />
          </Pressable>
        </View>

        <ScrollView
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {activeTab === "home" && (
            <HomeScreen metrics={metrics} onRecord={() => setActiveTab("record")} onDelete={deleteRecord} />
          )}
          {activeTab === "record" && (
            <RecordScreen form={form} onChange={setForm} onTypeChange={setFormType} onSubmit={addRecord} />
          )}
          {activeTab === "budget" && (
            <BudgetScreen
              budgetDraft={budgetDraft}
              budgetStatus={metrics.budget}
              categoryBudgets={metrics.categoryBudgets}
              onBudgetDraftChange={setBudgetDraft}
              onSaveMonthlyBudget={saveMonthlyBudget}
              onCategoryBudgetChange={updateCategoryBudget}
            />
          )}
          {activeTab === "analysis" && <AnalysisScreen metrics={metrics} records={data.records} />}
        </ScrollView>

        <View style={styles.bottomNav}>
          {tabItems.map((item) => {
            const Icon = item.icon;
            const active = item.id === activeTab;
            return (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={item.label}
                key={item.id}
                style={[styles.navItem, active && styles.navItemActive]}
                onPress={() => setActiveTab(item.id)}
              >
                <Icon color={active ? "#16805f" : "#6d817c"} size={20} />
                <Text style={[styles.navLabel, active && styles.navLabelActive]}>{item.label}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
  );
}

function StartupCarousel({
  activeSlide,
  onFirstImageReady,
  onSkip,
}: {
  activeSlide: number;
  onFirstImageReady: () => void;
  onSkip: () => void;
}) {
  return (
    <View style={styles.startup}>
      <StatusBar barStyle="light-content" backgroundColor="#10100f" />
      <ImageBackground
        source={startupSlides[activeSlide]}
        resizeMode="cover"
        style={styles.startupImage}
        onLoadEnd={activeSlide === 0 ? onFirstImageReady : undefined}
      >
        <View style={styles.startupShade} />
        <Pressable accessibilityRole="button" accessibilityLabel="跳过启动页" style={styles.startupSkip} onPress={onSkip}>
          <Text style={styles.startupSkipText}>跳过</Text>
        </Pressable>
        <View style={styles.startupFooter}>
          <Text style={styles.startupTitle}>记账</Text>
          <Text style={styles.startupSubtitle}>把每一天的小确幸都记下来</Text>
          <View style={styles.startupDots}>
            {startupSlides.map((_, index) => (
              <View key={index} style={[styles.startupDot, index === activeSlide && styles.startupDotActive]} />
            ))}
          </View>
        </View>
      </ImageBackground>
    </View>
  );
}

function HomeScreen({
  metrics,
  onRecord,
  onDelete,
}: {
  metrics: Metrics;
  onRecord: () => void;
  onDelete: (id: string) => void;
}) {
  return (
    <View style={styles.stack}>
      <View style={[styles.heroPanel, levelBackground(metrics.budget.level)]}>
        <View style={styles.heroRow}>
          <View>
            <Text style={styles.heroLabel}>本月支出</Text>
            <Text style={styles.heroAmount}>{formatMoney(metrics.totals.expense)}</Text>
          </View>
          <WalletCards color="#ffffff" size={28} />
        </View>
        <View style={styles.budgetLine}>
          <Text style={styles.budgetLineText}>预算剩余 {formatMoney(metrics.budget.remaining)}</Text>
          <Text style={styles.budgetLineText}>{metrics.budget.percent}%</Text>
        </View>
        <ProgressBar level={metrics.budget.level} percent={metrics.budget.percent} inverted />
      </View>

      <View style={styles.metricGrid}>
        <MetricCard label="本月收入" value={formatMoney(metrics.totals.income)} />
        <MetricCard label="本月结余" value={formatMoney(metrics.totals.net)} />
      </View>

      <Pressable style={styles.primaryAction} onPress={onRecord}>
        <ReceiptText color="#ffffff" size={20} />
        <Text style={styles.primaryActionText}>快速记一笔</Text>
      </Pressable>

      <SectionHeader icon={<CalendarDays color="#16805f" size={18} />} title="最近账单" />
      <TransactionList records={metrics.recent} onDelete={onDelete} />
    </View>
  );
}

function RecordScreen({
  form,
  onChange,
  onTypeChange,
  onSubmit,
}: {
  form: RecordForm;
  onChange: (form: RecordForm) => void;
  onTypeChange: (type: TransactionType) => void;
  onSubmit: () => void;
}) {
  const categories = form.type === "expense" ? expenseCategories : incomeCategories;

  return (
    <View style={[styles.panel, styles.stack]}>
      <View style={styles.segmented}>
        <SegmentButton active={form.type === "expense"} label="支出" onPress={() => onTypeChange("expense")} />
        <SegmentButton active={form.type === "income"} label="收入" onPress={() => onTypeChange("income")} />
      </View>

      <Field label="金额">
        <TextInput
          keyboardType="decimal-pad"
          placeholder="0.00"
          style={styles.input}
          value={form.amount}
          onChangeText={(amount) => onChange({ ...form, amount })}
        />
      </Field>

      <Field label="分类">
        <View style={styles.choiceWrap}>
          {categories.map((category) => (
            <ChoiceChip
              active={form.category === category}
              key={category}
              label={labelFor(category)}
              onPress={() => onChange({ ...form, category })}
            />
          ))}
        </View>
      </Field>

      <Field label="日期">
        <TextInput
          placeholder="YYYY-MM-DD"
          style={styles.input}
          value={form.date}
          onChangeText={(date) => onChange({ ...form, date })}
        />
      </Field>

      <Field label="备注">
        <TextInput
          multiline
          numberOfLines={3}
          placeholder="可选"
          style={[styles.input, styles.textArea]}
          value={form.note}
          onChangeText={(note) => onChange({ ...form, note })}
        />
      </Field>

      <Pressable style={styles.primaryAction} onPress={onSubmit}>
        <Plus color="#ffffff" size={20} />
        <Text style={styles.primaryActionText}>保存账单</Text>
      </Pressable>
    </View>
  );
}

function BudgetScreen({
  budgetDraft,
  budgetStatus,
  categoryBudgets,
  onBudgetDraftChange,
  onSaveMonthlyBudget,
  onCategoryBudgetChange,
}: {
  budgetDraft: string;
  budgetStatus: ReturnType<typeof getBudgetStatus>;
  categoryBudgets: ReturnType<typeof getCategoryBudgetStatuses>;
  onBudgetDraftChange: (value: string) => void;
  onSaveMonthlyBudget: () => void;
  onCategoryBudgetChange: (category: string, value: string) => void;
}) {
  return (
    <View style={styles.stack}>
      <View style={styles.panel}>
        <SectionHeader icon={<PiggyBank color="#16805f" size={18} />} title="月度总预算" />
        <View style={styles.budgetEditor}>
          <TextInput
            keyboardType="decimal-pad"
            style={[styles.input, styles.budgetInput]}
            value={budgetDraft}
            onChangeText={onBudgetDraftChange}
          />
          <Pressable style={styles.saveButton} onPress={onSaveMonthlyBudget}>
            <Text style={styles.saveButtonText}>保存</Text>
          </Pressable>
        </View>
        <Text style={[styles.statusText, levelText(budgetStatus.level)]}>
          已用 {formatMoney(budgetStatus.spent)}，剩余 {formatMoney(budgetStatus.remaining)}
        </Text>
        <ProgressBar level={budgetStatus.level} percent={budgetStatus.percent} />
      </View>

      <View style={styles.panel}>
        <SectionHeader icon={<LineChart color="#16805f" size={18} />} title="分类预算" />
        <View style={styles.stackSmall}>
          {categoryBudgets.map((item) => (
            <View key={item.category} style={styles.categoryBudget}>
              <View style={styles.rowBetween}>
                <View>
                  <Text style={styles.itemTitle}>{labelFor(item.category)}</Text>
                  <Text style={styles.muted}>
                    {formatMoney(item.spent)} / {formatMoney(item.limit)}
                  </Text>
                </View>
                <TextInput
                  keyboardType="decimal-pad"
                  style={styles.categoryBudgetInput}
                  value={String(item.limit)}
                  onChangeText={(value) => onCategoryBudgetChange(item.category, value)}
                />
              </View>
              <ProgressBar level={item.level} percent={item.percent} />
            </View>
          ))}
        </View>
      </View>
    </View>
  );
}

function AnalysisScreen({ metrics, records }: { metrics: Metrics; records: Transaction[] }) {
  const maxTrend = Math.max(...metrics.trend.map((item) => item.amount), 1);

  return (
    <View style={styles.stack}>
      <View style={styles.metricGrid}>
        <MetricCard label="收入" value={formatMoney(metrics.totals.income)} />
        <MetricCard label="支出" value={formatMoney(metrics.totals.expense)} />
      </View>

      <View style={styles.panel}>
        <SectionHeader icon={<LineChart color="#16805f" size={18} />} title="近 7 天支出" />
        <View style={styles.trendChart}>
          {metrics.trend.map((point) => (
            <View key={point.date} style={styles.trendColumn}>
              <Text style={styles.trendValue}>{point.amount > 0 ? `¥${Math.round(point.amount)}` : ""}</Text>
              <View style={styles.trendTrack}>
                <View style={[styles.trendBar, { height: `${Math.max(5, (point.amount / maxTrend) * 100)}%` }]} />
              </View>
              <Text style={styles.trendLabel}>{point.label.slice(3)}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={styles.panel}>
        <SectionHeader icon={<BarChart3 color="#16805f" size={18} />} title="分类占比" />
        {metrics.categories.length === 0 ? (
          <Text style={styles.emptyText}>本月还没有支出记录</Text>
        ) : (
          <View style={styles.stackSmall}>
            {metrics.categories.map((item) => (
              <View key={item.category} style={styles.categoryRow}>
                <View style={styles.rowBetween}>
                  <Text style={styles.itemTitle}>{labelFor(item.category)}</Text>
                  <Text style={styles.muted}>{item.percent}%</Text>
                </View>
                <ProgressBar level="healthy" percent={item.percent} />
                <Text style={styles.categoryAmount}>{formatMoney(item.amount)}</Text>
              </View>
            ))}
          </View>
        )}
      </View>

      <View style={styles.panel}>
        <SectionHeader icon={<ReceiptText color="#16805f" size={18} />} title="全部账单" />
        <TransactionList records={getRecentRecords(records, 20)} />
      </View>
    </View>
  );
}

function TransactionList({ records, onDelete }: { records: Transaction[]; onDelete?: (id: string) => void }) {
  if (records.length === 0) {
    return <Text style={styles.emptyText}>还没有账单，先记一笔吧。</Text>;
  }

  return (
    <View style={styles.transactionList}>
      {records.map((record) => (
        <View key={record.id} style={styles.transaction}>
          <View style={[styles.badge, record.type === "income" && styles.badgeIncome]}>
            <Text style={[styles.badgeText, record.type === "income" && styles.badgeTextIncome]}>
              {record.type === "income" ? "入" : "出"}
            </Text>
          </View>
          <View style={styles.transactionMain}>
            <Text numberOfLines={1} style={styles.itemTitle}>
              {labelFor(record.category)}
            </Text>
            <Text numberOfLines={1} style={styles.muted}>
              {record.date}
              {record.note ? ` · ${record.note}` : ""}
            </Text>
          </View>
          <Text style={[styles.amount, record.type === "income" && styles.amountIncome]}>
            {record.type === "income" ? "+" : "-"}
            {formatMoney(record.amount)}
          </Text>
          {onDelete && (
            <Pressable accessibilityRole="button" accessibilityLabel="删除账单" style={styles.deleteButton} onPress={() => onDelete(record.id)}>
              <Trash2 color="#8a9b96" size={16} />
            </Pressable>
          )}
        </View>
      ))}
    </View>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.metricCard}>
      <Text style={styles.muted}>{label}</Text>
      <Text numberOfLines={1} adjustsFontSizeToFit style={styles.metricValue}>
        {value}
      </Text>
    </View>
  );
}

function SectionHeader({ icon, title }: { icon: React.ReactNode; title: string }) {
  return (
    <View style={styles.sectionHeader}>
      {icon}
      <Text style={styles.sectionTitle}>{title}</Text>
    </View>
  );
}

function Field({ children, label }: { children: React.ReactNode; label: string }) {
  return (
    <View style={styles.field}>
      <Text style={styles.fieldLabel}>{label}</Text>
      {children}
    </View>
  );
}

function SegmentButton({ active, label, onPress }: { active: boolean; label: string; onPress: () => void }) {
  return (
    <Pressable style={[styles.segmentButton, active && styles.segmentButtonActive]} onPress={onPress}>
      <Text style={[styles.segmentText, active && styles.segmentTextActive]}>{label}</Text>
    </Pressable>
  );
}

function ChoiceChip({ active, label, onPress }: { active: boolean; label: string; onPress: () => void }) {
  return (
    <Pressable style={[styles.choiceChip, active && styles.choiceChipActive]} onPress={onPress}>
      <Text style={[styles.choiceChipText, active && styles.choiceChipTextActive]}>{label}</Text>
    </Pressable>
  );
}

function ProgressBar({ percent, level, inverted = false }: { percent: number; level: BudgetLevel | "healthy"; inverted?: boolean }) {
  return (
    <View style={[styles.progressTrack, inverted && styles.progressTrackInverted]}>
      <View style={[styles.progressFill, levelFill(level), { width: `${Math.min(Math.max(percent, 0), 100)}%` }]} />
    </View>
  );
}

type Metrics = {
  totals: ReturnType<typeof getMonthlyTotals>;
  budget: ReturnType<typeof getBudgetStatus>;
  categories: ReturnType<typeof getCategorySpending>;
  categoryBudgets: ReturnType<typeof getCategoryBudgetStatuses>;
  trend: ReturnType<typeof buildSevenDayTrend>;
  recent: ReturnType<typeof getRecentRecords>;
};

function getTitle(tab: Tab) {
  return {
    home: "今天也把钱看清楚",
    record: "记一笔",
    budget: "预算",
    analysis: "账单分析",
  }[tab];
}

function labelFor(category: string) {
  return categoryLabels[category] ?? category;
}

function formatMoney(value: number) {
  return money.format(value);
}

function levelBackground(level: BudgetLevel) {
  if (level === "over") return styles.heroOver;
  if (level === "near") return styles.heroNear;
  return styles.heroHealthy;
}

function levelText(level: BudgetLevel) {
  if (level === "over") return styles.textOver;
  if (level === "near") return styles.textNear;
  return styles.textHealthy;
}

function levelFill(level: BudgetLevel | "healthy") {
  if (level === "over") return styles.fillOver;
  if (level === "near") return styles.fillNear;
  return styles.fillHealthy;
}

const styles = StyleSheet.create({
  startup: {
    flex: 1,
    backgroundColor: "#10100f",
  },
  startupImage: {
    flex: 1,
    justifyContent: "space-between",
  },
  startupShade: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: "rgba(0,0,0,0.18)",
  },
  startupSkip: {
    alignSelf: "flex-end",
    minWidth: 62,
    minHeight: 34,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 54,
    marginRight: 18,
    backgroundColor: "rgba(0,0,0,0.38)",
  },
  startupSkipText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "900",
  },
  startupFooter: {
    paddingHorizontal: 24,
    paddingBottom: 48,
  },
  startupTitle: {
    color: "#ffffff",
    fontSize: 38,
    fontWeight: "900",
  },
  startupSubtitle: {
    color: "rgba(255,255,255,0.86)",
    fontSize: 14,
    fontWeight: "800",
    marginTop: 8,
  },
  startupDots: {
    flexDirection: "row",
    gap: 7,
    marginTop: 18,
  },
  startupDot: {
    width: 7,
    height: 7,
    borderRadius: 999,
    backgroundColor: "rgba(255,255,255,0.45)",
  },
  startupDotActive: {
    width: 24,
    backgroundColor: "#ffffff",
  },
  safeArea: {
    flex: 1,
    backgroundColor: "#f7faf9",
  },
  app: {
    flex: 1,
    backgroundColor: "#f7faf9",
  },
  topBar: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
    paddingHorizontal: 16,
    paddingTop: 14,
    paddingBottom: 12,
  },
  eyebrow: {
    color: "#5e7770",
    fontSize: 12,
    fontWeight: "700",
    marginBottom: 4,
  },
  title: {
    color: "#163c35",
    fontSize: 23,
    fontWeight: "800",
  },
  iconButton: {
    width: 42,
    height: 42,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#16805f",
  },
  content: {
    paddingHorizontal: 16,
    paddingBottom: 102,
  },
  stack: {
    gap: 14,
  },
  stackSmall: {
    gap: 12,
    marginTop: 12,
  },
  panel: {
    borderWidth: 1,
    borderColor: "#dce9e5",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    padding: 14,
  },
  heroPanel: {
    borderRadius: 8,
    padding: 16,
  },
  heroHealthy: {
    backgroundColor: "#16805f",
  },
  heroNear: {
    backgroundColor: "#b96b11",
  },
  heroOver: {
    backgroundColor: "#b93c3c",
  },
  heroRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
  },
  heroLabel: {
    color: "rgba(255,255,255,0.76)",
    fontSize: 13,
    marginBottom: 6,
  },
  heroAmount: {
    color: "#ffffff",
    fontSize: 34,
    fontWeight: "900",
  },
  budgetLine: {
    flexDirection: "row",
    justifyContent: "space-between",
    gap: 12,
    marginTop: 18,
    marginBottom: 10,
  },
  budgetLineText: {
    color: "#ffffff",
    fontSize: 13,
    fontWeight: "800",
  },
  metricGrid: {
    flexDirection: "row",
    gap: 10,
  },
  metricCard: {
    flex: 1,
    minWidth: 0,
    borderWidth: 1,
    borderColor: "#dce9e5",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    padding: 13,
  },
  metricValue: {
    color: "#17352f",
    fontSize: 18,
    fontWeight: "900",
    marginTop: 6,
  },
  primaryAction: {
    minHeight: 48,
    borderRadius: 8,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#16805f",
  },
  primaryActionText: {
    color: "#ffffff",
    fontSize: 15,
    fontWeight: "900",
  },
  sectionHeader: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  sectionTitle: {
    color: "#17352f",
    fontSize: 16,
    fontWeight: "900",
  },
  transactionList: {
    gap: 10,
  },
  transaction: {
    minHeight: 62,
    borderWidth: 1,
    borderColor: "#dce9e5",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    padding: 10,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  badge: {
    width: 34,
    height: 34,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#fff0ef",
  },
  badgeIncome: {
    backgroundColor: "#e7f5ef",
  },
  badgeText: {
    color: "#b93c3c",
    fontSize: 13,
    fontWeight: "900",
  },
  badgeTextIncome: {
    color: "#16805f",
  },
  transactionMain: {
    flex: 1,
    minWidth: 0,
  },
  itemTitle: {
    color: "#17352f",
    fontSize: 14,
    fontWeight: "900",
  },
  muted: {
    color: "#668078",
    fontSize: 12,
  },
  amount: {
    color: "#b93c3c",
    fontSize: 13,
    fontWeight: "900",
  },
  amountIncome: {
    color: "#16805f",
  },
  deleteButton: {
    width: 34,
    height: 34,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
  },
  segmented: {
    flexDirection: "row",
    padding: 4,
    borderRadius: 8,
    backgroundColor: "#edf5f2",
  },
  segmentButton: {
    flex: 1,
    minHeight: 40,
    borderRadius: 6,
    alignItems: "center",
    justifyContent: "center",
  },
  segmentButtonActive: {
    backgroundColor: "#ffffff",
  },
  segmentText: {
    color: "#5e7770",
    fontWeight: "900",
  },
  segmentTextActive: {
    color: "#17352f",
  },
  field: {
    gap: 7,
  },
  fieldLabel: {
    color: "#31534b",
    fontSize: 13,
    fontWeight: "900",
  },
  input: {
    minHeight: 46,
    borderWidth: 1,
    borderColor: "#cdded9",
    borderRadius: 8,
    color: "#17352f",
    backgroundColor: "#ffffff",
    paddingHorizontal: 12,
    paddingVertical: 10,
  },
  textArea: {
    minHeight: 86,
    textAlignVertical: "top",
  },
  choiceWrap: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 8,
  },
  choiceChip: {
    minHeight: 36,
    borderWidth: 1,
    borderColor: "#dce9e5",
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    paddingHorizontal: 12,
    backgroundColor: "#ffffff",
  },
  choiceChipActive: {
    borderColor: "#16805f",
    backgroundColor: "#e7f5ef",
  },
  choiceChipText: {
    color: "#5e7770",
    fontSize: 13,
    fontWeight: "800",
  },
  choiceChipTextActive: {
    color: "#16805f",
  },
  budgetEditor: {
    flexDirection: "row",
    gap: 10,
    marginTop: 12,
    marginBottom: 10,
  },
  budgetInput: {
    flex: 1,
  },
  saveButton: {
    width: 82,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#16805f",
  },
  saveButtonText: {
    color: "#ffffff",
    fontWeight: "900",
  },
  statusText: {
    fontSize: 13,
    fontWeight: "900",
    marginBottom: 10,
  },
  textHealthy: {
    color: "#16805f",
  },
  textNear: {
    color: "#b96b11",
  },
  textOver: {
    color: "#b93c3c",
  },
  progressTrack: {
    height: 8,
    borderRadius: 999,
    overflow: "hidden",
    backgroundColor: "rgba(22,128,95,0.12)",
  },
  progressTrackInverted: {
    backgroundColor: "rgba(255,255,255,0.25)",
  },
  progressFill: {
    height: "100%",
    borderRadius: 999,
  },
  fillHealthy: {
    backgroundColor: "#16805f",
  },
  fillNear: {
    backgroundColor: "#d8831d",
  },
  fillOver: {
    backgroundColor: "#d04444",
  },
  categoryBudget: {
    gap: 8,
  },
  rowBetween: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
  },
  categoryBudgetInput: {
    width: 92,
    minHeight: 40,
    borderWidth: 1,
    borderColor: "#cdded9",
    borderRadius: 8,
    color: "#17352f",
    paddingHorizontal: 10,
    backgroundColor: "#ffffff",
  },
  trendChart: {
    height: 170,
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
    marginTop: 14,
  },
  trendColumn: {
    flex: 1,
    height: "100%",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: 4,
  },
  trendValue: {
    height: 22,
    color: "#5e7770",
    fontSize: 10,
  },
  trendTrack: {
    flex: 1,
    width: "100%",
    justifyContent: "flex-end",
  },
  trendBar: {
    width: "100%",
    minHeight: 5,
    borderTopLeftRadius: 6,
    borderTopRightRadius: 6,
    backgroundColor: "#48b08f",
  },
  trendLabel: {
    color: "#668078",
    fontSize: 10,
  },
  categoryRow: {
    gap: 7,
  },
  categoryAmount: {
    color: "#17352f",
    fontSize: 13,
    fontWeight: "900",
  },
  emptyText: {
    color: "#668078",
    fontSize: 13,
    marginTop: 12,
  },
  bottomNav: {
    position: "absolute",
    left: 0,
    right: 0,
    bottom: 0,
    flexDirection: "row",
    gap: 4,
    paddingHorizontal: 10,
    paddingTop: 8,
    paddingBottom: 8,
    borderTopWidth: 1,
    borderTopColor: "#dce9e5",
    backgroundColor: "#ffffff",
  },
  navItem: {
    flex: 1,
    minHeight: 56,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    gap: 3,
  },
  navItemActive: {
    backgroundColor: "#e7f5ef",
  },
  navLabel: {
    color: "#6d817c",
    fontSize: 11,
    fontWeight: "900",
  },
  navLabelActive: {
    color: "#16805f",
  },
});
