import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SplashScreen from "expo-splash-screen";
import {
  BarChart3,
  CalendarDays,
  ChevronLeft,
  ChevronDown,
  ChevronRight,
  Home,
  LineChart,
  ListPlus,
  PiggyBank,
  Plus,
  ReceiptText,
  Trash2,
  WalletCards,
} from "lucide-react-native";
import { createContext, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  ImageBackground,
  Pressable,
  Platform,
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
  getCategoryOptions,
} from "./src/data/categories";
import { sampleData } from "./src/data/sampleData";
import {
  buildSevenDayTrend,
  getBudgetStatus,
  getCategoryBudgetStatuses,
  getCategorySpending,
  getCategoryBreakdown,
  getSubcategoryRecords,
  getExpenseRecordsByCategory,
  getLatestRecordDate,
  getMonthlyTotals,
  getMonthlyReport,
  getRecentRecords,
  getYearlyReport,
  validateRecordInput,
} from "./src/lib/analytics";
import SavingsTimelineScreen from "./src/components/SavingsTimelineScreen";
import { editRecord, editableNote } from "./src/lib/editRecord";
import { queueUnsyncedRecords, syncRecordToExcel } from "./src/lib/excelSync";
import { loadAppData, saveAppData } from "./src/lib/storage";
import type { AppData, BudgetLevel, Transaction, TransactionType } from "./src/lib/types";

const EditRecordContext = createContext<(record: Transaction) => void>(() => {});

type Tab = "home" | "record" | "budget" | "analysis" | "finance";

type RecordForm = {
  type: TransactionType;
  amount: string;
  category: string;
  subcategory: string;
  date: string;
  note: string;
};

const today = new Date().toISOString().slice(0, 10);
const money = new Intl.NumberFormat("zh-CN", {
  style: "currency",
  currency: "CNY",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
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
  const contentScroll = useRef<ScrollView>(null);
  const scrollOffset = useRef(0);
  const overviewOffset = useRef(0);
  const financeReturnOffset = useRef(0);

  function handleDetailNavigation(open: boolean) {
    if (open) overviewOffset.current = scrollOffset.current;
    requestAnimationFrame(() => {
      contentScroll.current?.scrollTo({ y: open ? 0 : overviewOffset.current, animated: false });
    });
  }

  const [editing, setEditing] = useState<Transaction | null>(null);
  const editReturnOffset = useRef(0);
  const [activeTab, setActiveTab] = useState<Tab>("home");
  const [showStartup, setShowStartup] = useState(true);
  const [startupImageReady, setStartupImageReady] = useState(false);
  const [startupSlide, setStartupSlide] = useState(0);
  const [data, setData] = useState<AppData>(sampleData);
  const [isReady, setIsReady] = useState(false);
  const [syncMessage, setSyncMessage] = useState("");
  const [retrySync, setRetrySync] = useState(0);
  const savingRecord = useRef(false);
  const pendingCount = data.records.filter((record) => record.excelSync === "pending").length;
  const [form, setForm] = useState<RecordForm>({
    type: "expense",
    amount: "",
    category: "食",
    subcategory: "早午晚餐",
    date: today,
    note: "",
  });
  const [budgetDraft, setBudgetDraft] = useState(String(sampleData.budget.monthlyBudget));

  useEffect(() => {
    let active = true;

    loadAppData(AsyncStorage).then((loadedData) => {
      if (!active) return;
      setData(Platform.OS === "web"
        ? { ...loadedData, records: queueUnsyncedRecords(loadedData.records) }
        : loadedData);
      setBudgetDraft(String(loadedData.budget.monthlyBudget));
      setIsReady(true);
    });

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!isReady) return;
    let active = true;
    async function persistAndSync() {
      try {
        await saveAppData(AsyncStorage, data);
        if (!active || Platform.OS !== "web") return;
        const pending = data.records.filter((record) => record.excelSync === "pending");
        if (!pending.length) {
          if (data.records.some((record) => record.excelSync === "synced")) setSyncMessage("账单已同步到 history.xlsx");
          return;
        }
        setSyncMessage(`正在同步 ${pending.length} 笔账单到表格…`);
        const completed: string[] = [];
        let failure = "";
        for (const record of pending) {
          if (!active) return;
          try {
            await syncRecordToExcel(record);
            completed.push(record.id);
          } catch (error) {
            failure = error instanceof Error ? error.message : "表格同步失败";
            break;
          }
        }
        if (!active) return;
        if (completed.length) {
          setData((current) => ({ ...current, records: current.records.map((record) =>
            completed.includes(record.id) && pending.some((sent) => sent.id === record.id && sent.updatedAt === record.updatedAt)
              ? { ...record, excelSync: "synced", excelOriginal: undefined } : record) }));
        }
        setSyncMessage(failure ? `账单已保存在本机，待同步：${failure}` : "账单已同步到 history.xlsx");
      } catch {
        if (active) setSyncMessage("本机账单保存失败，请检查浏览器存储空间后重试");
      }
    }
    void persistAndSync();
    return () => { active = false; };
  }, [data, isReady, retrySync]);

  useEffect(() => {
    if (Platform.OS !== "web" || !pendingCount) return;
    const timer = setInterval(() => setRetrySync((value) => value + 1), 30000);
    return () => clearInterval(timer);
  }, [pendingCount]);

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
    const cumulative = data.records.reduce(
      (totals, record) => {
        totals[record.type] += record.amount;
        return totals;
      },
      { income: 0, expense: 0 },
    );

    return {
      totals: getMonthlyTotals(data.records, today),
      budget: getBudgetStatus(data.records, data.budget, today),
      categories: getCategorySpending(data.records, today),
      categoryBudgets: getCategoryBudgetStatuses(data.records, data.budget, today),
      trend: buildSevenDayTrend(data.records, today),
      cumulative,
      incomeCategories: getCategoryBreakdown(data.records, "income"),
      expenseCategories: getCategoryBreakdown(data.records, "expense"),
      recordCount: data.records.length,
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
      category: type === "expense" ? "食" : "职业收入",
      subcategory: type === "expense" ? "早午晚餐" : "工资收入",
    }));
  }

  async function addRecord() {
    if (savingRecord.current || !isReady) return;
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

    const record: Transaction = editing ? editRecord(editing, {
      type: form.type, amount, category: form.category, subcategory: form.subcategory.trim(),
      date: form.date, note: form.note.trim(),
    }, Platform.OS === "web") : {
      id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
      type: form.type,
      amount,
      category: form.category,
      subcategory: form.subcategory.trim(),
      date: form.date,
      note: form.note.trim(),
      createdAt: new Date().toISOString(),
      ...(Platform.OS === "web" ? { excelSync: "pending" as const } : {}),
    };

    savingRecord.current = true;
    const updated = { ...data, records: editing
      ? data.records.map((item) => item.id === record.id ? record : item)
      : [record, ...data.records] };
    try {
      await saveAppData(AsyncStorage, updated);
      setData(updated);
    } catch {
      Alert.alert("保存失败", "账单尚未保存，请检查浏览器存储空间后重试。");
      return;
    } finally {
      savingRecord.current = false;
    }
    setForm({
      type: "expense",
      amount: "",
      category: "食",
      subcategory: "早午晚餐",
      date: today,
      note: "",
    });
    if (editing) {
      setEditing(null);
      requestAnimationFrame(() => contentScroll.current?.scrollTo({ y: editReturnOffset.current, animated: false }));
    } else setActiveTab("home");
  }

  function beginEdit(record: Transaction) {
    editReturnOffset.current = scrollOffset.current;
    setEditing(record);
    setForm({ type: record.type, amount: String(record.amount), category: record.category,
      subcategory: record.subcategory ?? "", date: record.date, note: editableNote(record) });
    requestAnimationFrame(() => contentScroll.current?.scrollTo({ y: 0, animated: false }));
  }

  function cancelEdit() {
    setEditing(null);
    setForm({ type: "expense", amount: "", category: "食", subcategory: "早午晚餐", date: today, note: "" });
    requestAnimationFrame(() => contentScroll.current?.scrollTo({ y: editReturnOffset.current, animated: false }));
  }

  function beginNewRecord() {
    setEditing(null);
    setForm({ type: "expense", amount: "", category: "食", subcategory: "早午晚餐", date: today, note: "" });
    setActiveTab("record");
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
    <EditRecordContext.Provider value={beginEdit}>
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" backgroundColor="#f7faf9" />
      <View style={styles.app}>
        <View style={styles.topBar}>
          <View>
            <Text style={styles.eyebrow}>个人账本</Text>
            <Text style={styles.title}>{editing ? "修改账单" : getTitle(activeTab)}</Text>
          </View>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="新增账单"
            style={styles.iconButton}
            onPress={beginNewRecord}
          >
            <Plus color="#ffffff" size={20} />
          </Pressable>
        </View>

        <ScrollView
          ref={contentScroll}
          onScroll={(event) => { scrollOffset.current = event.nativeEvent.contentOffset.y; }}
          scrollEventThrottle={16}
          contentContainerStyle={styles.content}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {Platform.OS === "web" && syncMessage !== "" && (
            <View style={[styles.panel, styles.stackSmall]}>
              <Text style={styles.muted}>{syncMessage}</Text>
              {pendingCount > 0 && (
                <Pressable accessibilityRole="button" onPress={() => setRetrySync((value) => value + 1)}>
                  <Text style={styles.backButtonText}>重试同步（{pendingCount} 笔）</Text>
                </Pressable>
              )}
            </View>
          )}
          {editing && <RecordScreen form={form} onChange={setForm} onTypeChange={setFormType}
            onSubmit={addRecord} editing onCancel={cancelEdit} records={data.records} />}
          <View style={editing ? { display: "none" } : undefined}>
          {(activeTab === "home" || activeTab === "finance") && (
            <View style={activeTab === "finance" ? { display: "none" } : undefined}><HomeScreen onFinance={() => { financeReturnOffset.current = scrollOffset.current; setActiveTab("finance"); contentScroll.current?.scrollTo({ y: 0, animated: false }); }} onDetailNavigation={handleDetailNavigation} records={data.records} metrics={metrics} onRecord={beginNewRecord} /></View>
          )}
          {activeTab === "record" && (
            <RecordScreen form={form} onChange={setForm} onTypeChange={setFormType} onSubmit={addRecord} records={data.records} />
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
          {activeTab === "finance" && <SavingsTimelineScreen records={data.records}
            onBack={() => { setActiveTab("home"); requestAnimationFrame(() => contentScroll.current?.scrollTo({ y: financeReturnOffset.current, animated: false })); }} />}
          {activeTab === "analysis" && <AnalysisScreen metrics={metrics} records={data.records} />}
          </View>
        </ScrollView>

        <View style={styles.bottomNav}>
          {tabItems.map((item) => {
            const Icon = item.icon;
            const active = item.id === activeTab || (item.id === "home" && activeTab === "finance");
            return (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel={item.label}
                key={item.id}
                style={[styles.navItem, active && styles.navItemActive]}
                onPress={() => { if (editing) cancelEdit(); setActiveTab(item.id); }}
              >
                <Icon color={active ? "#16805f" : "#6d817c"} size={20} />
                <Text style={[styles.navLabel, active && styles.navLabelActive]}>{item.label}</Text>
              </Pressable>
            );
          })}
        </View>
      </View>
    </SafeAreaView>
    </EditRecordContext.Provider>
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
  records,
  onRecord,
  onFinance,
  onDetailNavigation,
}: {
  metrics: Metrics;
  records: Transaction[];
  onRecord: () => void;
  onFinance: () => void;
  onDetailNavigation: (open: boolean) => void;
}) {
  const [selected, setSelected] = useState<{
    type: TransactionType; category: string; subcategory: string;
  } | null>(null);

  return (
    <>
      {selected && (
        <CategoryDetailScreen
          category={selected.subcategory}
          periodLabel={`全部时间 · ${labelFor(selected.category)} · ${selected.type === "income" ? "收入" : "支出"}`}
          records={getSubcategoryRecords(records, selected.type, selected.category, selected.subcategory)}
          transactionType={selected.type}
          backLabel="返回总览"
          onBack={() => { setSelected(null); onDetailNavigation(false); }}
        />
      )}
    <View style={[styles.stack, selected ? { display: "none" } : undefined]}>
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

      <Pressable accessibilityRole="button" accessibilityLabel="累计收支总览，查看还要存多久" onPress={onFinance}>
        <View style={styles.rowBetween}>
          <SectionHeader icon={<WalletCards color="#16805f" size={18} />} title="累计收支总览" />
          <ChevronRight color="#16805f" size={20} />
        </View>
        <Text style={styles.muted}>按现在的收支，算算还要存多久</Text>
      </Pressable>
      <Text style={styles.muted}>统计全部历史账单及手动记账</Text>
      <View style={styles.metricGrid}>
        <MetricCard label="总收入" value={formatMoney(metrics.cumulative.income)} />
        <MetricCard label="总支出" value={formatMoney(metrics.cumulative.expense)} />
      </View>
      <View style={styles.metricGrid}>
        <MetricCard label="累计结余" value={formatMoney(metrics.cumulative.income - metrics.cumulative.expense)} />
        <MetricCard label="账单笔数" value={`${metrics.recordCount} 笔`} />
      </View>
      <OverviewCategories title="收入分类" categories={metrics.incomeCategories} onSelect={(category, subcategory) => { setSelected({ type: "income", category, subcategory }); onDetailNavigation(true); }} />
      <OverviewCategories title="支出分类" categories={metrics.expenseCategories} onSelect={(category, subcategory) => { setSelected({ type: "expense", category, subcategory }); onDetailNavigation(true); }} />
    </View>
    </>
  );
}

function OverviewCategories({ title, categories, onSelect }: {
  title: string;
  categories: ReturnType<typeof getCategoryBreakdown>;
  onSelect: (category: string, subcategory: string) => void;
}) {
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set());

  function toggle(category: string) {
    setExpanded((current) => {
      const next = new Set(current);
      if (next.has(category)) next.delete(category);
      else next.add(category);
      return next;
    });
  }

  return (
    <View style={styles.stackSmall}>
      <SectionHeader icon={<BarChart3 color="#16805f" size={18} />} title={title} />
      <Text style={styles.muted}>点击大类展开小类</Text>
      {categories.length === 0 ? <Text style={styles.emptyText}>暂无记录</Text> : categories.map((item) => (
        <View key={item.category} style={styles.categoryRow}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`${expanded.has(item.category) ? "收起" : "展开"}${labelFor(item.category)}小类`}
            accessibilityState={{ expanded: expanded.has(item.category) }}
            onPress={() => toggle(item.category)}
            style={styles.stackSmall}
          >
            <View style={styles.rowBetween}>
              <Text style={styles.itemTitle}>{labelFor(item.category)}</Text>
              <View style={styles.categoryPercent}>
                <Text style={styles.muted}>{item.percent}%</Text>
                {expanded.has(item.category)
                  ? <ChevronDown color="#16805f" size={18} />
                  : <ChevronRight color="#16805f" size={18} />}
              </View>
            </View>
            <ProgressBar level="healthy" percent={item.percent} />
            <Text style={styles.categoryAmount}>{formatMoney(item.amount)}</Text>
          </Pressable>
          {expanded.has(item.category) && (
            <View style={styles.subcategoryList}>
              <Text style={styles.muted}>小类金额 · 占本大类比例</Text>
              {item.subcategories.map((child) => (
                <Pressable key={child.category} style={styles.subcategoryRow}
                  accessibilityRole="button"
                  accessibilityLabel={`查看${labelFor(item.category)}${child.category}明细`}
                  onPress={() => onSelect(item.category, child.category)}
                >
                  <Text style={styles.subcategoryName}>{child.category}</Text>
                  <View style={styles.subcategoryValues}>
                    <Text style={styles.categoryAmount}>{formatMoney(child.amount)}</Text>
                    <Text style={styles.muted}>{child.percent}%</Text>
                  </View>
                  <ChevronRight color="#16805f" size={18} />
                </Pressable>
              ))}
            </View>
          )}
        </View>
      ))}
    </View>
  );
}

function RecordScreen({
  form,
  onChange,
  onTypeChange,
  onSubmit,
  editing = false,
  onCancel,
  records,
}: {
  form: RecordForm;
  onChange: (form: RecordForm) => void;
  onTypeChange: (type: TransactionType) => void;
  onSubmit: () => void;
  editing?: boolean;
  onCancel?: () => void;
  records: Transaction[];
}) {
  const categoryOptions = getCategoryOptions(form.type, records, editing ? form : undefined);
  const categories = Object.keys(categoryOptions);
  const subcategories = categoryOptions[form.category] ?? [];

  return (
    <View style={[styles.panel, styles.stack]}>
      {editing && <Pressable accessibilityRole="button" onPress={onCancel}><Text style={styles.backButtonText}>取消修改，返回账单</Text></Pressable>}
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

      <Field label="一级分类">
        <View style={styles.choiceWrap}>
          {categories.map((category) => (
            <ChoiceChip
              active={form.category === category}
              key={category}
              label={labelFor(category)}
              onPress={() => onChange({ ...form, category, subcategory: category === form.category ? form.subcategory : categoryOptions[category][0] ?? "" })}
            />
          ))}
        </View>
      </Field>

      <Field label="二级分类">
        <View style={styles.choiceWrap}>
          {subcategories.map((subcategory) => (
            <ChoiceChip key={subcategory} label={subcategory || "未分类"}
              active={form.subcategory === subcategory}
              onPress={() => onChange({ ...form, subcategory })} />
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
        <Text style={styles.primaryActionText}>{editing ? "保存修改" : "保存账单"}</Text>
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
  const latestDate = getLatestRecordDate(records);
  const [reportMode, setReportMode] = useState<"month" | "year">("month");
  const [selectedMonth, setSelectedMonth] = useState(latestDate.slice(0, 7));
  const [selectedYear, setSelectedYear] = useState(latestDate.slice(0, 4));
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const monthlyReport = useMemo(() => getMonthlyReport(records, selectedMonth), [records, selectedMonth]);
  const yearlyReport = useMemo(() => getYearlyReport(records, selectedYear), [records, selectedYear]);
  const activeReport = reportMode === "month" ? monthlyReport : yearlyReport;
  const activePeriod = reportMode === "month" ? selectedMonth : selectedYear;
  const selectedCategoryRecords = useMemo(
    () => (selectedCategory ? getExpenseRecordsByCategory(records, selectedCategory, activePeriod) : []),
    [records, selectedCategory, activePeriod],
  );
  const activePeriodLabel = reportMode === "month" ? formatMonthLabel(selectedMonth) : `${selectedYear} 年`;

  useEffect(() => {
    setSelectedMonth(latestDate.slice(0, 7));
    setSelectedYear(latestDate.slice(0, 4));
  }, [latestDate]);

  useEffect(() => {
    setSelectedCategory(null);
  }, [reportMode, activePeriod]);

  if (selectedCategory) {
    return (
      <CategoryDetailScreen
        category={selectedCategory}
        periodLabel={activePeriodLabel}
        records={selectedCategoryRecords}
        onBack={() => setSelectedCategory(null)}
      />
    );
  }

  return (
    <View style={styles.stack}>
      <View style={styles.segmented}>
        <SegmentButton active={reportMode === "month"} label="月度" onPress={() => setReportMode("month")} />
        <SegmentButton active={reportMode === "year"} label="年度" onPress={() => setReportMode("year")} />
      </View>

      {reportMode === "month" ? (
        <PeriodSwitcher
          label={formatMonthLabel(selectedMonth)}
          onPrevious={() => setSelectedMonth(shiftMonth(selectedMonth, -1))}
          onNext={() => setSelectedMonth(shiftMonth(selectedMonth, 1))}
        />
      ) : (
        <PeriodSwitcher
          label={`${selectedYear} 年`}
          onPrevious={() => setSelectedYear(String(Number(selectedYear) - 1))}
          onNext={() => setSelectedYear(String(Number(selectedYear) + 1))}
        />
      )}

      <ReportMetricGrid totals={activeReport.totals} />

      <View style={styles.panel}>
        <SectionHeader icon={<LineChart color="#16805f" size={18} />} title={reportMode === "month" ? "每日支出" : "全年收支"} />
        {reportMode === "month" ? (
          <MonthlyTrendChart points={monthlyReport.dailyTrend} />
        ) : (
          <YearlyTrendChart summaries={yearlyReport.monthlySummaries} />
        )}
      </View>

      <View style={styles.panel}>
        <SectionHeader icon={<BarChart3 color="#16805f" size={18} />} title="分类排行" />
        <CategoryRanking
          categories={activeReport.categories}
          onSelectCategory={(category) => setSelectedCategory(category)}
        />
      </View>

      {reportMode === "year" && (
        <View style={styles.panel}>
          <SectionHeader icon={<CalendarDays color="#16805f" size={18} />} title="高支出月份" />
          <TopExpenseMonths months={yearlyReport.topExpenseMonths} />
        </View>
      )}

      {reportMode === "month" && (
        <View style={styles.panel}>
          <SectionHeader icon={<ReceiptText color="#16805f" size={18} />} title="本月账单" />
          {monthlyReport.records.length === 0 ? (
            <Text style={styles.emptyText}>这个月还没有账单记录</Text>
          ) : (
            <TransactionList records={monthlyReport.records} />
          )}
        </View>
      )}

      <View style={styles.panel}>
        <SectionHeader icon={<ReceiptText color="#16805f" size={18} />} title="最近账单" />
        <TransactionList records={getRecentRecords(records, 20)} />
      </View>
    </View>
  );
}

function PeriodSwitcher({ label, onPrevious, onNext }: { label: string; onPrevious: () => void; onNext: () => void }) {
  return (
    <View style={styles.periodSwitcher}>
      <Pressable accessibilityRole="button" accessibilityLabel="上一个周期" style={styles.periodButton} onPress={onPrevious}>
        <ChevronLeft color="#16805f" size={19} />
      </Pressable>
      <Text style={styles.periodLabel}>{label}</Text>
      <Pressable accessibilityRole="button" accessibilityLabel="下一个周期" style={styles.periodButton} onPress={onNext}>
        <ChevronRight color="#16805f" size={19} />
      </Pressable>
    </View>
  );
}

function ReportMetricGrid({ totals }: { totals: ReturnType<typeof getMonthlyReport>["totals"] }) {
  return (
    <View style={styles.reportMetricGrid}>
      <MetricCard label="收入" value={formatMoney(totals.income)} />
      <MetricCard label="支出" value={formatMoney(totals.expense)} />
      <MetricCard label="结余" value={formatMoney(totals.net)} />
      <MetricCard label="结余率" value={`${totals.savingsRate}%`} />
    </View>
  );
}

function MonthlyTrendChart({ points }: { points: ReturnType<typeof getMonthlyReport>["dailyTrend"] }) {
  const maxTrend = Math.max(...points.map((item) => item.amount), 1);

  if (points.every((point) => point.amount === 0)) {
    return <Text style={styles.emptyText}>这个月还没有支出记录</Text>;
  }

  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.monthlyTrendScroll}>
      {points.map((point, index) => (
        <View key={point.date} style={styles.monthlyTrendColumn}>
          <Text style={styles.trendValue}>{point.amount > 0 ? `¥${Math.round(point.amount)}` : ""}</Text>
          <View style={styles.trendTrack}>
            <View style={[styles.trendBar, { height: `${Math.max(5, (point.amount / maxTrend) * 100)}%` }]} />
          </View>
          <Text style={styles.trendLabel}>{index % 5 === 0 || index === points.length - 1 ? point.label.slice(3) : ""}</Text>
        </View>
      ))}
    </ScrollView>
  );
}

function YearlyTrendChart({ summaries }: { summaries: ReturnType<typeof getYearlyReport>["monthlySummaries"] }) {
  const maxExpense = Math.max(...summaries.map((summary) => summary.expense), 1);

  return (
    <View style={styles.yearlyRows}>
      {summaries.map((summary) => (
        <View key={summary.month} style={styles.yearlyRow}>
          <Text style={styles.yearlyMonth}>{summary.label}</Text>
          <View style={styles.yearlyBarTrack}>
            <View style={[styles.yearlyBar, { width: `${Math.max(3, (summary.expense / maxExpense) * 100)}%` }]} />
          </View>
          <View style={styles.yearlyNumbers}>
            <Text style={styles.yearlyExpense}>{formatMoney(summary.expense)}</Text>
            <Text style={styles.muted}>结余 {formatMoney(summary.net)}</Text>
          </View>
        </View>
      ))}
    </View>
  );
}

function CategoryRanking({
  categories,
  onSelectCategory,
}: {
  categories: ReturnType<typeof getMonthlyReport>["categories"];
  onSelectCategory: (category: string) => void;
}) {
  if (categories.length === 0) {
    return <Text style={styles.emptyText}>当前周期还没有支出记录</Text>;
  }

  return (
    <View style={styles.stackSmall}>
      {categories.slice(0, 8).map((item) => (
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`查看${labelFor(item.category)}明细`}
          key={item.category}
          style={[styles.categoryRow, styles.categoryPressable]}
          onPress={() => onSelectCategory(item.category)}
        >
          <View style={styles.rowBetween}>
            <Text style={styles.itemTitle}>{labelFor(item.category)}</Text>
            <View style={styles.categoryPercent}>
              <Text style={styles.muted}>{item.percent}%</Text>
              <ChevronRight color="#8a9b96" size={16} />
            </View>
          </View>
          <ProgressBar level="healthy" percent={item.percent} />
          <Text style={styles.categoryAmount}>{formatMoney(item.amount)}</Text>
        </Pressable>
      ))}
    </View>
  );
}

function CategoryDetailScreen({
  category,
  periodLabel,
  records,
  onBack,
  transactionType = "expense",
  backLabel = "返回分析",
}: {
  category: string;
  periodLabel: string;
  records: Transaction[];
  onBack: () => void;
  transactionType?: TransactionType;
  backLabel?: string;
}) {
  return (
    <View style={styles.stack}>
      <Pressable accessibilityRole="button" accessibilityLabel={backLabel} style={styles.backButton} onPress={onBack}>
        <ChevronLeft color="#16805f" size={19} />
        <Text style={styles.backButtonText}>{backLabel}</Text>
      </Pressable>

      <View style={styles.detailHero}>
        <View>
          <Text style={styles.heroLabelMuted}>{periodLabel}</Text>
          <Text style={styles.detailTitle}>{labelFor(category)}明细</Text>
          <Text style={styles.detailSubtitle}>
            {records.length} 笔{transactionType === "income" ? "收入" : "支出"}
          </Text>
        </View>
        <Text numberOfLines={1} adjustsFontSizeToFit style={styles.categoryDetailTotal}>
          {formatMoney(records.reduce((sum, record) => sum + record.amount, 0))}
        </Text>
      </View>

      <View style={styles.panel}>
        <SectionHeader icon={<ReceiptText color="#16805f" size={18} />} title="账单明细" />
        <View style={styles.categoryDetailList}>
          <TransactionList records={records} showFullNotes />
        </View>
      </View>
    </View>
  );
}

function TopExpenseMonths({ months }: { months: ReturnType<typeof getYearlyReport>["topExpenseMonths"] }) {
  if (months.length === 0) {
    return <Text style={styles.emptyText}>这一年还没有支出记录</Text>;
  }

  return (
    <View style={styles.stackSmall}>
      {months.map((month) => (
        <View key={month.month} style={styles.topMonthRow}>
          <View>
            <Text style={styles.itemTitle}>{month.label}</Text>
            <Text style={styles.muted}>收入 {formatMoney(month.income)} · 结余 {formatMoney(month.net)}</Text>
          </View>
          <Text style={styles.amount}>-{formatMoney(month.expense)}</Text>
        </View>
      ))}
    </View>
  );
}

function shiftMonth(month: string, offset: number) {
  const [year, monthIndex] = month.split("-").map(Number);
  const date = new Date(year, monthIndex - 1 + offset, 1);
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

function formatMonthLabel(month: string) {
  const [year, monthValue] = month.split("-");
  return `${year} 年 ${Number(monthValue)} 月`;
}

function TransactionList({ records, onDelete, showFullNotes = false }: { records: Transaction[]; onDelete?: (id: string) => void; showFullNotes?: boolean }) {
  const onEdit = useContext(EditRecordContext);
  if (records.length === 0) {
    return <Text style={styles.emptyText}>还没有账单，先记一笔吧。</Text>;
  }

  return (
    <View style={styles.transactionList}>
      {records.map((record) => (
        <Pressable key={record.id} style={styles.transaction} accessibilityRole="button"
          accessibilityLabel={`修改${record.date}${labelFor(record.category)}${formatMoney(record.amount)}账单`} onPress={() => onEdit(record)}>
          <View style={[styles.badge, record.type === "income" && styles.badgeIncome]}>
            <Text style={[styles.badgeText, record.type === "income" && styles.badgeTextIncome]}>
              {record.type === "income" ? "入" : "出"}
            </Text>
          </View>
          <View style={styles.transactionMain}>
            <Text numberOfLines={1} style={styles.itemTitle}>
              {labelFor(record.category)}
            </Text>
            <Text numberOfLines={showFullNotes ? undefined : 1} style={styles.muted}>
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
          <ChevronRight color="#8a9b96" size={16} />
        </Pressable>
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
    <Pressable accessibilityRole="button" accessibilityState={{ selected: active }}
      style={[styles.choiceChip, active && styles.choiceChipActive]} onPress={onPress}>
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
  cumulative: { income: number; expense: number };
  incomeCategories: ReturnType<typeof getCategoryBreakdown>;
  expenseCategories: ReturnType<typeof getCategoryBreakdown>;
  recordCount: number;
};

function getTitle(tab: Tab) {
  return {
    home: "今天也把钱看清楚",
    record: "记一笔",
    budget: "预算",
    analysis: "账单分析",
    finance: "还要存多久",
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
  subcategoryList: {
    marginTop: 14,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: "#dce9e5",
    gap: 12,
  },
  subcategoryRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  subcategoryName: { flex: 1, color: "#17352f", fontSize: 14 },
  subcategoryValues: { alignItems: "flex-end", gap: 4 },
  metricGrid: {
    flexDirection: "row",
    gap: 10,
  },
  reportMetricGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
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
  periodSwitcher: {
    minHeight: 48,
    borderWidth: 1,
    borderColor: "#dce9e5",
    borderRadius: 8,
    backgroundColor: "#ffffff",
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 8,
  },
  periodButton: {
    width: 38,
    height: 38,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "#e7f5ef",
  },
  periodLabel: {
    color: "#17352f",
    fontSize: 16,
    fontWeight: "900",
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
  monthlyTrendScroll: {
    height: 176,
    gap: 6,
    paddingTop: 14,
    paddingBottom: 2,
  },
  monthlyTrendColumn: {
    width: 30,
    height: "100%",
    alignItems: "center",
    justifyContent: "flex-end",
    gap: 4,
  },
  yearlyRows: {
    gap: 11,
    marginTop: 14,
  },
  yearlyRow: {
    minHeight: 46,
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
  },
  yearlyMonth: {
    width: 34,
    color: "#31534b",
    fontSize: 12,
    fontWeight: "900",
  },
  yearlyBarTrack: {
    flex: 1,
    height: 10,
    borderRadius: 999,
    overflow: "hidden",
    backgroundColor: "rgba(22,128,95,0.12)",
  },
  yearlyBar: {
    height: "100%",
    borderRadius: 999,
    backgroundColor: "#48b08f",
  },
  yearlyNumbers: {
    width: 96,
    alignItems: "flex-end",
  },
  yearlyExpense: {
    color: "#17352f",
    fontSize: 12,
    fontWeight: "900",
  },
  categoryRow: {
    gap: 7,
  },
  categoryPressable: {
    borderWidth: 1,
    borderColor: "transparent",
    borderRadius: 8,
    padding: 8,
    marginHorizontal: -8,
  },
  categoryPercent: {
    flexDirection: "row",
    alignItems: "center",
    gap: 2,
  },
  categoryAmount: {
    color: "#17352f",
    fontSize: 13,
    fontWeight: "900",
  },
  backButton: {
    alignSelf: "flex-start",
    minHeight: 38,
    borderRadius: 8,
    flexDirection: "row",
    alignItems: "center",
    gap: 4,
    paddingHorizontal: 10,
    backgroundColor: "#e7f5ef",
  },
  backButtonText: {
    color: "#16805f",
    fontSize: 13,
    fontWeight: "900",
  },
  detailHero: {
    borderRadius: 8,
    backgroundColor: "#17352f",
    padding: 16,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 12,
  },
  heroLabelMuted: {
    color: "rgba(255,255,255,0.72)",
    fontSize: 12,
    fontWeight: "800",
    marginBottom: 5,
  },
  detailTitle: {
    color: "#ffffff",
    fontSize: 25,
    fontWeight: "900",
    marginBottom: 5,
  },
  detailSubtitle: {
    color: "rgba(255,255,255,0.78)",
    fontSize: 12,
    fontWeight: "800",
  },
  categoryDetailTotal: {
    color: "#ffffff",
    fontSize: 20,
    fontWeight: "900",
    maxWidth: 132,
  },
  categoryDetailList: {
    marginTop: 12,
  },
  topMonthRow: {
    minHeight: 54,
    borderWidth: 1,
    borderColor: "#edf2f0",
    borderRadius: 8,
    backgroundColor: "#fbfdfc",
    padding: 10,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    gap: 10,
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
