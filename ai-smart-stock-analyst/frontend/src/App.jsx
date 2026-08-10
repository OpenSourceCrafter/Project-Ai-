import React, { useState, useMemo, useEffect } from "react";
import {
  AreaChart, Area, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Cell
} from "recharts";
import {
  Search, TrendingUp, TrendingDown, Home, BarChart2, Star, Briefcase,
  Newspaper, Settings, ChevronRight, X, Flame, ShieldAlert, Info,
  ArrowUpRight, ArrowDownRight, Minus, Wifi, WifiOff
} from "lucide-react";
import {
  fetchMarketOverview, fetchTopStocks, fetchGeneralNews, fetchQuote,
  fetchFundamentals, fetchStockNews, pingBackend,
} from "./lib/api.js";

/* ---------------------------------------------------------------
   AI SMART STOCK ANALYST — Frontend Prototype
   All data below is simulated/mock, for demonstration of the UI only.
   No live market data, news, or financial data is connected.
----------------------------------------------------------------*/

/* ---------- design tokens ---------- */
const C = {
  bg: "#0A111F",
  bg2: "#080D18",
  surface: "#121B2E",
  surfaceAlt: "#182338",
  border: "rgba(255,255,255,0.07)",
  text: "#EAF0FA",
  muted: "#8C9AB3",
  faint: "#5C6A85",
  green: "#34D399",
  greenDim: "rgba(52,211,153,0.14)",
  red: "#F87171",
  redDim: "rgba(248,113,113,0.14)",
  amber: "#FBBF24",
  amberDim: "rgba(251,191,36,0.14)",
  cyan: "#22D3EE",
  cyanDim: "rgba(34,211,238,0.14)",
};

const scoreColor = (s) =>
  s >= 85 ? C.green : s >= 70 ? C.cyan : s >= 50 ? C.amber : C.red;
const scoreLabel = (s) =>
  s >= 85 ? "VERY ATTRACTIVE" : s >= 70 ? "ATTRACTIVE" : s >= 50 ? "NEUTRAL" : "CAUTION";

const recColor = (r) => {
  if (["STRONG BUY", "BUY", "ACCUMULATE"].includes(r)) return C.green;
  if (["HOLD", "WATCH"].includes(r)) return C.amber;
  return C.red;
};

/* ---------- mock data ---------- */
const marketIndices = [
  { name: "SET", value: "1,392.18", chg: 0.42, spark: [1,2,1,3,2,4,3,5] },
  { name: "SET50", value: "878.44", chg: 0.31, spark: [2,1,2,3,3,4,4,5] },
  { name: "S&P 500", value: "5,842.30", chg: 0.81, spark: [1,1,2,2,3,4,5,6] },
  { name: "NASDAQ", value: "19,205.7", chg: 1.20, spark: [1,2,2,3,4,4,6,7] },
  { name: "Dow Jones", value: "41,880.2", chg: -0.18, spark: [5,4,4,3,3,4,3,3] },
  { name: "Nikkei 225", value: "39,940.1", chg: 0.65, spark: [2,2,3,3,4,4,5,6] },
  { name: "Hang Seng", value: "18,220.6", chg: -0.94, spark: [6,5,5,4,3,3,2,2] },
  { name: "Shanghai", value: "3,088.4", chg: 0.12, spark: [3,3,3,4,3,4,4,4] },
  { name: "Bitcoin", value: "$68,420", chg: 2.35, spark: [2,3,2,4,3,5,6,7] },
  { name: "Gold", value: "$2,415", chg: 0.28, spark: [3,3,4,3,4,4,5,5] },
  { name: "USD/THB", value: "34.62", chg: -0.15, spark: [5,5,4,4,4,3,3,3] },
];

const topStocks = [
  { rank: 1, ticker: "NVDA", name: "NVIDIA Corporation", country: "US", sector: "Semiconductor", price: 128.4, w1: 4.2, m1: 12.8, y1: 61.3, score: 94, risk: "Medium-High", sentiment: "Very Positive", rec: "STRONG BUY", potential: "+12% to +25%" },
  { rank: 2, ticker: "MSFT", name: "Microsoft Corp.", country: "US", sector: "Technology", price: 462.1, w1: 1.8, m1: 6.4, y1: 28.7, score: 91, risk: "Medium", sentiment: "Positive", rec: "BUY", potential: "+8% to +18%" },
  { rank: 3, ticker: "GOOGL", name: "Alphabet Inc.", country: "US", sector: "Technology", price: 178.9, w1: 2.4, m1: 7.1, y1: 34.5, score: 89, risk: "Medium", sentiment: "Positive", rec: "BUY", potential: "+10% to +20%" },
  { rank: 4, ticker: "AMZN", name: "Amazon.com Inc.", country: "US", sector: "Consumer", price: 201.5, w1: -0.6, m1: 3.9, y1: 22.1, score: 87, risk: "Medium", sentiment: "Positive", rec: "BUY", potential: "+9% to +17%" },
  { rank: 5, ticker: "AVGO", name: "Broadcom Inc.", country: "US", sector: "Semiconductor", price: 1842.3, w1: 3.1, m1: 9.6, y1: 45.2, score: 86, risk: "Medium-High", sentiment: "Positive", rec: "BUY", potential: "+11% to +22%" },
  { rank: 6, ticker: "META", name: "Meta Platforms", country: "US", sector: "Technology", price: 612.7, w1: 1.1, m1: 5.2, y1: 31.0, score: 85, risk: "Medium", sentiment: "Positive", rec: "BUY", potential: "+7% to +16%" },
  { rank: 7, ticker: "TSM", name: "Taiwan Semiconductor", country: "TW", sector: "Semiconductor", price: 189.2, w1: 2.0, m1: 6.8, y1: 27.4, score: 84, risk: "Medium", sentiment: "Positive", rec: "ACCUMULATE", potential: "+8% to +19%" },
  { rank: 8, ticker: "DELTA", name: "Delta Electronics PCL", country: "TH", sector: "Technology", price: 92.5, w1: -1.2, m1: 2.4, y1: 14.8, score: 83, risk: "Medium", sentiment: "Neutral", rec: "ACCUMULATE", potential: "+6% to +14%" },
  { rank: 9, ticker: "AMD", name: "Advanced Micro Devices", country: "US", sector: "Semiconductor", price: 152.8, w1: 0.4, m1: 4.1, y1: 18.9, score: 82, risk: "High", sentiment: "Positive", rec: "ACCUMULATE", potential: "+9% to +21%" },
  { rank: 10, ticker: "PTT", name: "PTT Public Company", country: "TH", sector: "Energy", price: 33.75, w1: -0.9, m1: -1.8, y1: -6.2, score: 81, risk: "Low-Medium", sentiment: "Neutral", rec: "HOLD", potential: "+3% to +9%" },
];

function genPriceSeries(base, days, vol) {
  let p = base;
  const out = [];
  let seed = base * 7 + days;
  const rand = () => {
    seed = (seed * 9301 + 49297) % 233280;
    return seed / 233280;
  };
  for (let i = 0; i < days; i++) {
    p = p + (rand() - 0.48) * vol;
    p = Math.max(p, base * 0.5);
    out.push({ day: i, price: Number(p.toFixed(2)) });
  }
  return out;
}

function withMA(series, period) {
  return series.map((pt, i) => {
    if (i < period - 1) return { ...pt };
    const slice = series.slice(i - period + 1, i + 1);
    const avg = slice.reduce((a, b) => a + b.price, 0) / period;
    return { ...pt, [`ma${period}`]: Number(avg.toFixed(2)) };
  });
}

const stockDetails = {
  NVDA: {
    name: "NVIDIA Corporation", exchange: "NASDAQ", price: 128.4, chg: 3.9, sentiment: "Bullish",
    score: 94, rec: "STRONG BUY",
    aiView: "หุ้นมีปัจจัยพื้นฐานแข็งแกร่งจากความต้องการชิป AI ที่ยังเติบโตต่อเนื่อง และ Momentum ระยะกลางยังเป็นบวก อย่างไรก็ตาม Valuation อยู่ในระดับสูง จึงควรพิจารณาความเสี่ยงก่อนลงทุน",
    support: 118, resistance: 142, rangeLow: 122, rangeHigh: 152,
    breakdown: { Fundamental: 90, Technical: 88, Growth: 97, Valuation: 62, News: 92, Momentum: 95, Risk: 58 },
    reasonsPos: ["Revenue เติบโตแข็งแกร่งต่อเนื่อง", "Earnings สูงกว่าคาดการณ์", "News Sentiment เป็นบวกชัดเจน", "Momentum ระยะกลาง-สั้นแข็งแกร่ง", "Institutional Interest สูง"],
    reasonsNeg: ["Valuation อยู่ในระดับสูงเมื่อเทียบ Sector", "Volatility ค่อนข้างสูง"],
    fundamentals: { Revenue: "$113.2B", RevGrowth: "+79%", EPS: "$2.98", EPSGrowth: "+82%", GrossMargin: "74.6%", ROE: "91.2%", DebtEquity: "0.24", PE: "48.2", PB: "34.1", DivYield: "0.03%" },
    forecast: { d7: [122, 134], d30: [118, 142], m3: [112, 156], y1: [130, 195] },
    confidence: 71,
    news: [
      { time: "2h ago", headline: "บริษัทประกาศรายได้ไตรมาสล่าสุดสูงกว่าคาด", sentiment: "Positive", impact: 82, high: true },
      { time: "6h ago", headline: "นักวิเคราะห์ปรับเพิ่มราคาเป้าหมายหลังงาน Developer Conference", sentiment: "Positive", impact: 74, high: true },
      { time: "1d ago", headline: "ความกังวลเรื่องข้อจำกัดการส่งออกชิปในภูมิภาคเอเชีย", sentiment: "Negative", impact: 55, high: false },
    ],
  },
  MSFT: {
    name: "Microsoft Corp.", exchange: "NASDAQ", price: 462.1, chg: 1.4, sentiment: "Bullish",
    score: 91, rec: "BUY",
    aiView: "ธุรกิจ Cloud และ AI Integration ยังเติบโตดี กระแสเงินสดแข็งแกร่งและมีความเสี่ยงด้าน Valuation ต่ำกว่ากลุ่ม Semiconductor อย่างไรก็ตามการเติบโตเริ่มชะลอลงเล็กน้อยเมื่อเทียบไตรมาสก่อน",
    support: 440, resistance: 480, rangeLow: 448, rangeHigh: 492,
    breakdown: { Fundamental: 93, Technical: 84, Growth: 82, Valuation: 70, News: 80, Momentum: 78, Risk: 74 },
    reasonsPos: ["Cloud Revenue เติบโตต่อเนื่อง", "Free Cash Flow แข็งแกร่งมาก", "Debt/Equity ต่ำ", "Diversified Revenue Stream"],
    reasonsNeg: ["การเติบโตเริ่มชะลอเมื่อเทียบปีก่อน", "Valuation ค่อนข้างสูงเมื่อเทียบ Historical Average"],
    fundamentals: { Revenue: "$245.1B", RevGrowth: "+15%", EPS: "$11.86", EPSGrowth: "+18%", GrossMargin: "69.8%", ROE: "38.4%", DebtEquity: "0.35", PE: "36.5", PB: "13.2", DivYield: "0.72%" },
    forecast: { d7: [450, 470], d30: [440, 480], m3: [430, 495], y1: [455, 560] },
    confidence: 76,
    news: [
      { time: "3h ago", headline: "Azure รายงานอัตราการเติบโตของลูกค้าองค์กรเพิ่มขึ้น", sentiment: "Positive", impact: 70, high: false },
      { time: "1d ago", headline: "บริษัทประกาศเพิ่มงบลงทุนโครงสร้างพื้นฐาน AI", sentiment: "Positive", impact: 68, high: false },
    ],
  },
};
// Default detail generator for tickers without curated data
function fallbackDetail(t) {
  const base = t.price;
  return {
    name: t.name, exchange: t.country === "TH" ? "SET" : t.country === "TW" ? "TWSE" : "NASDAQ",
    price: base, chg: t.w1 / 3, sentiment: t.sentiment,
    score: t.score, rec: t.rec,
    aiView: "หุ้นมีปัจจัยพื้นฐานและ Momentum อยู่ในเกณฑ์ที่ระบบให้ความสนใจ ควรพิจารณาความเสี่ยงและ Valuation ประกอบก่อนตัดสินใจลงทุน",
    support: Number((base * 0.92).toFixed(2)), resistance: Number((base * 1.08).toFixed(2)),
    rangeLow: Number((base * 0.95).toFixed(2)), rangeHigh: Number((base * 1.12).toFixed(2)),
    breakdown: { Fundamental: t.score - 4, Technical: t.score - 8, Growth: t.score - 2, Valuation: t.score - 20, News: t.score - 6, Momentum: t.score - 3, Risk: 100 - t.score + 30 },
    reasonsPos: ["ปัจจัยพื้นฐานอยู่ในเกณฑ์ดี", "Momentum ระยะสั้นเป็นบวก"],
    reasonsNeg: ["Valuation ควรพิจารณาเทียบ Sector", "มีความผันผวนที่ต้องติดตาม"],
    fundamentals: { Revenue: "—", RevGrowth: "—", EPS: "—", EPSGrowth: "—", GrossMargin: "—", ROE: "—", DebtEquity: "—", PE: "—", PB: "—", DivYield: "—" },
    forecast: { d7: [base*0.97, base*1.03], d30: [base*0.94, base*1.08], m3: [base*0.88, base*1.15], y1: [base*0.85, base*1.3] },
    confidence: 58,
    news: [{ time: "5h ago", headline: "ไม่มีข่าวสำคัญเพิ่มเติมในช่วง 24 ชั่วโมงที่ผ่านมา", sentiment: "Neutral", impact: 20, high: false }],
  };
}

const generalNews = [
  { time: "20 min ago", source: "Reuters", headline: "ธนาคารกลางสหรัฐฯ ส่งสัญญาณคงอัตราดอกเบี้ยในการประชุมรอบถัดไป", sentiment: "Neutral", impact: 60, high: true, tag: "Interest Rate" },
  { time: "1h ago", source: "Bloomberg", headline: "กลุ่มหุ้นเทคโนโลยีปรับตัวขึ้นหลังตัวเลขเงินเฟ้อออกมาต่ำกว่าคาด", sentiment: "Positive", impact: 71, high: true, tag: "Inflation" },
  { time: "3h ago", source: "SET Market News", headline: "นักลงทุนต่างชาติกลับมาซื้อสุทธิหุ้นไทยต่อเนื่องเป็นวันที่ 3", sentiment: "Positive", impact: 58, high: false, tag: "Fund Flow" },
  { time: "5h ago", source: "Nikkei Asia", headline: "ห่วงโซ่อุปทานเซมิคอนดักเตอร์ในเอเชียเผชิญแรงกดดันจากความต้องการที่พุ่งสูง", sentiment: "Neutral", impact: 64, high: true, tag: "Supply Chain" },
  { time: "8h ago", source: "CNBC", headline: "ราคาน้ำมันดิบปรับลดลงจากความกังวลอุปสงค์ชะลอตัว", sentiment: "Negative", impact: 52, high: false, tag: "Commodity" },
];

const sentimentColor = (s) => s === "Positive" || s === "Very Positive" ? C.green : s === "Negative" ? C.red : C.amber;

/* ---------- small components ---------- */
function Ring({ value, size = 96, stroke = 9, label, sub }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const pct = Math.max(0, Math.min(100, value)) / 100;
  const col = scoreColor(value);
  return (
    <div style={{ position: "relative", width: size, height: size }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={C.surfaceAlt} strokeWidth={stroke} />
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke={col} strokeWidth={stroke}
          strokeDasharray={c} strokeDashoffset={c * (1 - pct)} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }} />
      </svg>
      <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 600, fontSize: size * 0.24, color: C.text }}>{value}</span>
        {sub && <span style={{ fontSize: 9, color: C.faint, marginTop: 2 }}>{sub}</span>}
      </div>
    </div>
  );
}

function LiveBadge({ isLive }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 8px",
      borderRadius: 999, fontSize: 10, fontWeight: 700, letterSpacing: 0.3,
      color: isLive ? C.green : C.faint,
      background: isLive ? C.greenDim : C.surfaceAlt,
    }}>
      {isLive ? <Wifi size={11} /> : <WifiOff size={11} />}
      {isLive ? "LIVE" : "DEMO DATA"}
    </span>
  );
}

function Pill({ children, color, bg }) {
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 9px",
      borderRadius: 999, fontSize: 11, fontWeight: 600, color, background: bg,
      letterSpacing: 0.2, whiteSpace: "nowrap",
    }}>{children}</span>
  );
}

function Sparkline({ data, color }) {
  const points = data.map((v, i) => `${(i / (data.length - 1)) * 60},${20 - (v / Math.max(...data)) * 18}`).join(" ");
  return (
    <svg width="60" height="20" viewBox="0 0 60 20">
      <polyline points={points} fill="none" stroke={color} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function ChgTag({ v }) {
  const pos = v >= 0;
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: 2, color: pos ? C.green : C.red, fontFamily: "'JetBrains Mono', monospace", fontSize: 12, fontWeight: 600 }}>
      {pos ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
      {pos ? "+" : ""}{v.toFixed(2)}%
    </span>
  );
}

function SectionTitle({ eyebrow, title, right }) {
  return (
    <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", marginBottom: 14 }}>
      <div>
        {eyebrow && <div style={{ fontSize: 11, letterSpacing: 1.5, color: C.cyan, fontWeight: 600, marginBottom: 4, textTransform: "uppercase" }}>{eyebrow}</div>}
        <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 19, fontWeight: 600, color: C.text }}>{title}</div>
      </div>
      {right}
    </div>
  );
}

/* ---------- main sections ---------- */
function MarketOverview() {
  const [liveData, setLiveData] = useState(null);

  useEffect(() => {
    fetchMarketOverview().then((data) => {
      if (Array.isArray(data) && data.some((d) => d.is_available)) setLiveData(data);
    });
  }, []);

  // Live rows from the backend don't carry a sparkline (that needs history
  // the DB may not have yet) — reuse the mock spark shape purely for visuals.
  const rows = liveData
    ? liveData.map((d, i) => ({
        name: d.symbol,
        value: d.value != null ? d.value.toLocaleString() : "—",
        chg: d.change_pct ?? 0,
        spark: marketIndices[i % marketIndices.length].spark,
      }))
    : marketIndices;

  return (
    <div style={{ display: "flex", gap: 10, overflowX: "auto", paddingBottom: 6 }}>
      {rows.map((m) => (
        <div key={m.name} style={{
          minWidth: 148, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14,
          padding: "12px 14px", flexShrink: 0,
        }}>
          <div style={{ fontSize: 11, color: C.muted, marginBottom: 6, fontWeight: 500 }}>{m.name}</div>
          <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 15, color: C.text, fontWeight: 600, marginBottom: 4 }}>{m.value}</div>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <ChgTag v={m.chg} />
            <Sparkline data={m.spark} color={m.chg >= 0 ? C.green : C.red} />
          </div>
        </div>
      ))}
    </div>
  );
}

function SentimentPanel() {
  const score = 78;
  return (
    <div style={{ background: `linear-gradient(135deg, ${C.surface}, ${C.surfaceAlt})`, border: `1px solid ${C.border}`, borderRadius: 18, padding: 20, display: "flex", gap: 18, alignItems: "center" }}>
      <Ring value={score} size={92} sub="/ 100" />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 11, color: C.cyan, fontWeight: 700, letterSpacing: 1, marginBottom: 3 }}>AI MARKET SENTIMENT</div>
        <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 20, fontWeight: 700, color: C.green, marginBottom: 8 }}>BULLISH</div>
        <ul style={{ margin: 0, padding: 0, listStyle: "none", display: "flex", flexDirection: "column", gap: 4 }}>
          {["Earnings Growth ดีขึ้นทั่วกลุ่ม Technology", "ตลาดคาดการณ์แนวโน้มดอกเบี้ยทรงตัวถึงลดลง", "Institutional Buying เพิ่มขึ้นในหุ้นกลุ่ม AI"].map((r) => (
            <li key={r} style={{ fontSize: 12.5, color: C.muted, display: "flex", gap: 6 }}>
              <span style={{ color: C.green }}>•</span>{r}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function TopStockRow({ s, onClick }) {
  return (
    <button onClick={() => onClick(s)} style={{
      display: "grid", gridTemplateColumns: "28px 1fr auto auto auto", alignItems: "center",
      width: "100%", gap: 12, padding: "12px 14px", background: "transparent", border: "none",
      borderBottom: `1px solid ${C.border}`, cursor: "pointer", textAlign: "left",
    }}>
      <span style={{ fontFamily: "'JetBrains Mono', monospace", color: C.faint, fontSize: 13 }}>{s.rank}</span>
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
          <span style={{ fontWeight: 700, color: C.text, fontSize: 14 }}>{s.ticker}</span>
          <span style={{ fontSize: 10, color: C.faint, background: C.surfaceAlt, padding: "1px 6px", borderRadius: 5 }}>{s.country}</span>
        </div>
        <div style={{ fontSize: 11.5, color: C.muted, marginTop: 1 }}>{s.name}</div>
      </div>
      <div style={{ textAlign: "right" }}>
        <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 13, color: C.text }}>{s.price.toLocaleString()}</div>
        <ChgTag v={s.w1} />
      </div>
      <div style={{ textAlign: "center" }}>
        <span style={{ fontFamily: "'JetBrains Mono', monospace", fontWeight: 700, fontSize: 14, color: scoreColor(s.score) }}>{s.score}</span>
        <div style={{ fontSize: 9, color: C.faint }}>AI SCORE</div>
      </div>
      <Pill color={recColor(s.rec)} bg={recColor(s.rec) === C.green ? C.greenDim : recColor(s.rec) === C.amber ? C.amberDim : C.redDim}>{s.rec}</Pill>
    </button>
  );
}

function TopTen({ onSelect }) {
  const [tab, setTab] = useState("Global");
  const [liveRows, setLiveRows] = useState(null); // null = not fetched / unavailable for this tab
  const tabs = ["Global", "US", "Thai", "AI", "Momentum"];
  const categoryMap = { Global: "GLOBAL", US: "US", Thai: "THAI", AI: "AI", Momentum: "MOMENTUM" };

  useEffect(() => {
    let cancelled = false;
    fetchTopStocks(categoryMap[tab]).then((data) => {
      if (!cancelled) setLiveRows(data?.stocks?.length ? data.stocks : null);
    });
    return () => { cancelled = true; };
  }, [tab]);

  // Live rows come pre-shaped from the API (TopStockCard schema); mock rows
  // use slightly different field names (ticker/company vs name) — normalize both.
  const rows = liveRows || topStocks.map((s) => ({
    rank: s.rank, ticker: s.ticker, company: s.name, country: s.country,
    current_price: s.price, week_change_pct: s.w1, ai_score: s.score, recommendation: s.rec,
  }));

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 18, overflow: "hidden" }}>
      <div style={{ padding: "16px 16px 0" }}>
        <SectionTitle
          eyebrow="Updated Friday, 7 August 2026"
          title="🏆 AI Top 10 Stocks of the Week"
          right={<LiveBadge isLive={!!liveRows} />}
        />
        <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
          {tabs.map((t) => (
            <button key={t} onClick={() => setTab(t)} style={{
              padding: "6px 12px", borderRadius: 999, fontSize: 12, fontWeight: 600, cursor: "pointer",
              border: `1px solid ${tab === t ? C.cyan : C.border}`,
              background: tab === t ? C.cyanDim : "transparent",
              color: tab === t ? C.cyan : C.muted,
            }}>{t}</button>
          ))}
        </div>
      </div>
      <div>
        {rows.map((s) => (
          <TopStockRow
            key={s.ticker}
            s={{
              rank: s.rank, ticker: s.ticker, name: s.company, country: s.country,
              price: s.current_price, w1: s.week_change_pct, score: s.ai_score, rec: s.recommendation,
            }}
            onClick={onSelect}
          />
        ))}
      </div>
      <div style={{ padding: "10px 16px", fontSize: 11, color: C.faint, display: "flex", alignItems: "center", gap: 6 }}>
        <Info size={12} /> จัดอันดับจาก Fundamental 25% · Technical 20% · Growth 15% · Valuation 15% · News 10% · Momentum 5% · Risk 10%
      </div>
    </div>
  );
}

function NewsFeed() {
  const [liveNews, setLiveNews] = useState(null);

  useEffect(() => {
    fetchGeneralNews(10).then((data) => {
      if (Array.isArray(data) && data.length > 0) setLiveNews(data);
    });
  }, []);

  const items = liveNews || generalNews;

  return (
    <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 18, padding: 16 }}>
      <SectionTitle eyebrow="AI News Intelligence" title="ข่าวสำคัญล่าสุด" right={<LiveBadge isLive={!!liveNews} />} />
      <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
        {items.map((n, i) => {
          // Live items come from analyze_article() (topics/sentiment/impact_score,
          // uppercase); mock items are pre-shaped Title Case — normalize both.
          const sentiment = (n.sentiment || "Neutral");
          const sentimentDisplay = sentiment[0] + sentiment.slice(1).toLowerCase();
          const isHigh = n.is_high_impact ?? n.high;
          const impact = n.impact_score ?? n.impact;
          return (
            <div key={n.external_id || i} style={{ display: "flex", gap: 10, paddingBottom: 10, borderBottom: i < items.length - 1 ? `1px solid ${C.border}` : "none" }}>
              <div style={{ width: 4, borderRadius: 4, background: sentimentColor(sentimentDisplay), flexShrink: 0 }} />
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 3, flexWrap: "wrap" }}>
                  {isHigh && <Pill color={C.red} bg={C.redDim}><Flame size={10} /> HIGH IMPACT</Pill>}
                  <span style={{ fontSize: 10.5, color: C.faint }}>{n.source} · {n.time || n.published_at}</span>
                </div>
                <div style={{ fontSize: 13, color: C.text, lineHeight: 1.4, marginBottom: 4 }}>{n.headline}</div>
                <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
                  <Pill color={sentimentColor(sentimentDisplay)} bg={sentimentColor(sentimentDisplay) === C.green ? C.greenDim : sentimentColor(sentimentDisplay) === C.red ? C.redDim : C.amberDim}>{sentimentDisplay}</Pill>
                  <span style={{ fontSize: 10.5, color: C.faint }}>Impact Score: {impact}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ---------- stock detail page ---------- */
function ScoreBreakdown({ breakdown, reasonsPos, reasonsNeg }) {
  const [open, setOpen] = useState(false);
  const data = Object.entries(breakdown).map(([k, v]) => ({ name: k, value: v }));
  return (
    <div style={{ background: C.surfaceAlt, borderRadius: 14, padding: 14 }}>
      <button onClick={() => setOpen(!open)} style={{ display: "flex", alignItems: "center", gap: 6, background: "transparent", border: "none", color: C.cyan, fontSize: 12.5, fontWeight: 600, cursor: "pointer", padding: 0 }}>
        <Info size={13} /> ทำไม AI ถึงให้คะแนนนี้? {open ? "▲" : "▼"}
      </button>
      {open && (
        <div style={{ marginTop: 12 }}>
          <ResponsiveContainer width="100%" height={160}>
            <BarChart data={data} layout="vertical" margin={{ left: 0, right: 10 }}>
              <XAxis type="number" domain={[0, 100]} hide />
              <YAxis type="category" dataKey="name" width={78} tick={{ fill: C.muted, fontSize: 11 }} axisLine={false} tickLine={false} />
              <Tooltip contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }} labelStyle={{ color: C.text }} />
              <Bar dataKey="value" radius={[0, 6, 6, 0]}>
                {data.map((d, i) => <Cell key={i} fill={scoreColor(d.value)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
          <div style={{ display: "flex", gap: 16, marginTop: 8, flexWrap: "wrap" }}>
            <div style={{ flex: 1, minWidth: 140 }}>
              {reasonsPos.map((r) => <div key={r} style={{ fontSize: 12, color: C.muted, marginBottom: 4 }}><span style={{ color: C.green }}>+ </span>{r}</div>)}
            </div>
            <div style={{ flex: 1, minWidth: 140 }}>
              {reasonsNeg.map((r) => <div key={r} style={{ fontSize: 12, color: C.muted, marginBottom: 4 }}><span style={{ color: C.red }}>− </span>{r}</div>)}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PriceChart({ base }) {
  const [range, setRange] = useState("6M");
  const days = { "1M": 30, "3M": 90, "6M": 180, "1Y": 365 }[range];
  const series = useMemo(() => withMA(withMA(genPriceSeries(base, days, base * 0.015), 20), 50), [base, days]);
  return (
    <div>
      <div style={{ display: "flex", gap: 6, marginBottom: 10 }}>
        {["1M", "3M", "6M", "1Y"].map((r) => (
          <button key={r} onClick={() => setRange(r)} style={{
            padding: "4px 10px", borderRadius: 8, fontSize: 11.5, fontWeight: 600, cursor: "pointer",
            border: `1px solid ${range === r ? C.cyan : C.border}`,
            background: range === r ? C.cyanDim : "transparent",
            color: range === r ? C.cyan : C.muted,
          }}>{r}</button>
        ))}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <AreaChart data={series} margin={{ left: -20, right: 10, top: 5 }}>
          <defs>
            <linearGradient id="priceFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={C.cyan} stopOpacity={0.35} />
              <stop offset="100%" stopColor={C.cyan} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke={C.border} vertical={false} />
          <XAxis dataKey="day" hide />
          <YAxis domain={["auto", "auto"]} tick={{ fill: C.faint, fontSize: 10 }} axisLine={false} tickLine={false} width={40} />
          <Tooltip contentStyle={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, fontSize: 12 }} labelFormatter={() => ""} />
          <Area type="monotone" dataKey="price" stroke={C.cyan} strokeWidth={2} fill="url(#priceFill)" />
          <Line type="monotone" dataKey="ma20" stroke={C.amber} dot={false} strokeWidth={1.3} />
          <Line type="monotone" dataKey="ma50" stroke={C.red} dot={false} strokeWidth={1.3} />
        </AreaChart>
      </ResponsiveContainer>
      <div style={{ display: "flex", gap: 14, fontSize: 11, color: C.muted, marginTop: 4 }}>
        <span><span style={{ color: C.cyan }}>●</span> Price</span>
        <span><span style={{ color: C.amber }}>●</span> MA20</span>
        <span><span style={{ color: C.red }}>●</span> MA50</span>
      </div>
    </div>
  );
}

function StockDetail({ stock, onClose }) {
  const base = stockDetails[stock.ticker] || fallbackDetail(stock);
  const [live, setLive] = useState({ quote: null, fundamentals: null, news: null });

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      fetchQuote(stock.ticker),
      fetchFundamentals(stock.ticker),
      fetchStockNews(stock.ticker),
    ]).then(([quote, fundamentals, news]) => {
      if (cancelled) return;
      setLive({
        quote: quote?.meta?.is_available ? quote : null,
        fundamentals: fundamentals?.available ? fundamentals : null,
        news: Array.isArray(news) && news.length > 0 ? news : null,
      });
    });
    return () => { cancelled = true; };
  }, [stock.ticker]);

  const isLive = !!(live.quote || live.fundamentals || live.news);

  // Merge: live values win field-by-field when present, otherwise fall back
  // to the curated/mock detail — so the panel never shows a blank field.
  const d = {
    ...base,
    price: live.quote?.price ?? base.price,
    chg: live.quote?.change_pct ?? base.chg,
    fundamentals: live.fundamentals ? {
      Revenue: live.fundamentals.revenue ?? "—",
      RevGrowth: live.fundamentals.revenue_growth ?? "—",
      EPS: live.fundamentals.eps ?? "—",
      EPSGrowth: live.fundamentals.eps_growth ?? "—",
      GrossMargin: live.fundamentals.gross_margin ?? "—",
      ROE: live.fundamentals.roe ?? "—",
      DebtEquity: live.fundamentals.debt_to_equity ?? "—",
      PE: live.fundamentals.pe ?? "—",
      PB: live.fundamentals.pb ?? "—",
      DivYield: live.fundamentals.dividend_yield ?? "—",
    } : base.fundamentals,
    news: live.news
      ? live.news.slice(0, 5).map((n) => ({
          time: n.published_at || "recent",
          headline: n.headline,
          sentiment: (n.sentiment || "NEUTRAL")[0] + (n.sentiment || "NEUTRAL").slice(1).toLowerCase(),
          impact: n.impact_score,
          high: n.is_high_impact,
        }))
      : base.news,
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(4,7,14,0.72)", backdropFilter: "blur(3px)",
      zIndex: 50, display: "flex", justifyContent: "flex-end",
    }} onClick={onClose}>
      <div onClick={(e) => e.stopPropagation()} style={{
        width: "min(560px, 100%)", height: "100%", background: C.bg, borderLeft: `1px solid ${C.border}`,
        overflowY: "auto", padding: 20,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 18 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 2 }}>
              <span style={{ fontSize: 12, color: C.muted }}>{d.exchange} · {stock.sector}</span>
              <LiveBadge isLive={isLive} />
            </div>
            <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontSize: 22, fontWeight: 700, color: C.text }}>{d.name}</div>
            <div style={{ fontSize: 13, color: C.faint, fontWeight: 600 }}>{stock.ticker}</div>
          </div>
          <button onClick={onClose} style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 10, padding: 6, cursor: "pointer", color: C.muted }}><X size={16} /></button>
        </div>

        <div style={{ display: "flex", gap: 18, alignItems: "center", marginBottom: 18 }}>
          <div>
            <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 30, fontWeight: 700, color: C.text }}>${d.price}</div>
            <ChgTag v={d.chg} />
          </div>
          <Ring value={d.score} size={78} sub="AI SCORE" />
          <div>
            <Pill color={recColor(d.rec)} bg={recColor(d.rec) === C.green ? C.greenDim : recColor(d.rec) === C.amber ? C.amberDim : C.redDim}>{d.rec}</Pill>
            <div style={{ fontSize: 11, color: C.faint, marginTop: 6 }}>{scoreLabel(d.score)}</div>
          </div>
        </div>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 14, marginBottom: 16 }}>
          <div style={{ fontSize: 11, color: C.cyan, fontWeight: 700, marginBottom: 6 }}>🟢 AI VIEW</div>
          <div style={{ fontSize: 13, color: C.muted, lineHeight: 1.5 }}>{d.aiView}</div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <ScoreBreakdown breakdown={d.breakdown} reasonsPos={d.reasonsPos} reasonsNeg={d.reasonsNeg} />
        </div>

        <div style={{ marginBottom: 16 }}>
          <SectionTitle title="Price Analysis" />
          <PriceChart base={d.price} />
          <div style={{ display: "flex", gap: 10, marginTop: 10 }}>
            <div style={{ flex: 1, background: C.surface, borderRadius: 10, padding: 10, textAlign: "center" }}>
              <div style={{ fontSize: 10, color: C.faint }}>Support</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", color: C.red, fontWeight: 600 }}>${d.support}</div>
            </div>
            <div style={{ flex: 1, background: C.surface, borderRadius: 10, padding: 10, textAlign: "center" }}>
              <div style={{ fontSize: 10, color: C.faint }}>Resistance</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", color: C.green, fontWeight: 600 }}>${d.resistance}</div>
            </div>
            <div style={{ flex: 1, background: C.surface, borderRadius: 10, padding: 10, textAlign: "center" }}>
              <div style={{ fontSize: 10, color: C.faint }}>AI Est. Range</div>
              <div style={{ fontFamily: "'JetBrains Mono', monospace", color: C.cyan, fontWeight: 600, fontSize: 12.5 }}>${d.rangeLow}–${d.rangeHigh}</div>
            </div>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <SectionTitle title="AI Price Forecast" right={<Pill color={C.cyan} bg={C.cyanDim}>Confidence {d.confidence}%</Pill>} />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
            {Object.entries({ "7 Days": d.forecast.d7, "30 Days": d.forecast.d30, "3 Months": d.forecast.m3, "12 Months": d.forecast.y1 }).map(([k, v]) => (
              <div key={k} style={{ background: C.surface, borderRadius: 10, padding: 10 }}>
                <div style={{ fontSize: 10.5, color: C.faint }}>{k}</div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12.5, color: C.text }}>${Math.round(v[0])}–${Math.round(v[1])}</div>
              </div>
            ))}
          </div>
          <div style={{ fontSize: 10.5, color: C.faint, marginTop: 6 }}>Confidence คือระดับความมั่นใจของโมเดลต่อสัญญาณข้อมูล ไม่ใช่ความน่าจะเป็นของกำไร</div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <SectionTitle title="Fundamental Snapshot" />
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>
            {Object.entries(d.fundamentals).map(([k, v]) => (
              <div key={k} style={{ background: C.surface, borderRadius: 10, padding: "8px 10px" }}>
                <div style={{ fontSize: 9.5, color: C.faint }}>{k}</div>
                <div style={{ fontFamily: "'JetBrains Mono', monospace", fontSize: 12.5, color: C.text }}>{v}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <SectionTitle title="News for this stock" />
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {d.news.map((n, i) => (
              <div key={i} style={{ background: C.surface, borderRadius: 10, padding: 10 }}>
                <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
                  {n.high && <Pill color={C.red} bg={C.redDim}><Flame size={10} /> HIGH IMPACT</Pill>}
                  <span style={{ fontSize: 10, color: C.faint }}>{n.time}</span>
                </div>
                <div style={{ fontSize: 12.5, color: C.text, marginBottom: 5 }}>{n.headline}</div>
                <Pill color={sentimentColor(n.sentiment)} bg={sentimentColor(n.sentiment) === C.green ? C.greenDim : sentimentColor(n.sentiment) === C.red ? C.redDim : C.amberDim}>{n.sentiment} · {n.impact}</Pill>
              </div>
            ))}
          </div>
        </div>

        <div style={{ background: C.surfaceAlt, borderRadius: 12, padding: 12, display: "flex", gap: 8, alignItems: "flex-start" }}>
          <ShieldAlert size={16} color={C.amber} style={{ flexShrink: 0, marginTop: 1 }} />
          <div style={{ fontSize: 11.5, color: C.muted, lineHeight: 1.5 }}>
            ข้อมูลข้างต้นเป็นข้อมูลตัวอย่างเพื่อสาธิตการทำงานของหน้าจอ (Mock Data) ยังไม่ได้เชื่อมต่อกับผู้ให้บริการข้อมูลจริง การวิเคราะห์และประมาณการนี้จัดทำเพื่อการศึกษาเท่านั้น ไม่ใช่คำแนะนำการลงทุนและไม่รับประกันผลตอบแทน
          </div>
        </div>
      </div>
    </div>
  );
}

/* ---------- search ---------- */
function SearchBar({ onSelect }) {
  const [q, setQ] = useState("");
  const results = q.length > 0
    ? topStocks.filter((s) => s.ticker.toLowerCase().includes(q.toLowerCase()) || s.name.toLowerCase().includes(q.toLowerCase()))
    : [];
  return (
    <div style={{ position: "relative", flex: 1, maxWidth: 420 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, padding: "10px 14px" }}>
        <Search size={16} color={C.faint} />
        <input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="ค้นหาหุ้น เช่น AAPL, NVDA, PTT, DELTA"
          style={{ background: "transparent", border: "none", outline: "none", color: C.text, fontSize: 13, width: "100%" }}
        />
      </div>
      {results.length > 0 && (
        <div style={{ position: "absolute", top: "110%", left: 0, right: 0, background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, overflow: "hidden", zIndex: 10 }}>
          {results.map((s) => (
            <button key={s.ticker} onClick={() => { onSelect(s); setQ(""); }} style={{
              display: "flex", justifyContent: "space-between", width: "100%", padding: "10px 14px",
              background: "transparent", border: "none", borderBottom: `1px solid ${C.border}`, cursor: "pointer", textAlign: "left",
            }}>
              <span style={{ color: C.text, fontSize: 13 }}><b>{s.ticker}</b> <span style={{ color: C.muted, fontWeight: 400 }}>· {s.name}</span></span>
              <ChevronRight size={14} color={C.faint} />
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- app ---------- */
export default function App() {
  const [selected, setSelected] = useState(null);
  const [backendUp, setBackendUp] = useState(false);

  useEffect(() => {
    pingBackend().then(setBackendUp);
  }, []);

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "'Inter', 'Prompt', sans-serif" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@400;500;600;700&family=Prompt:wght@400;500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');
        * { box-sizing: border-box; }
        body { margin: 0; }
        ::-webkit-scrollbar { height: 6px; width: 6px; }
        ::-webkit-scrollbar-thumb { background: ${C.surfaceAlt}; border-radius: 4px; }
        input::placeholder { color: ${C.faint}; }
      `}</style>

      {/* header */}
      <div style={{ borderBottom: `1px solid ${C.border}`, background: C.bg2, position: "sticky", top: 0, zIndex: 20 }}>
        <div style={{ maxWidth: 1080, margin: "0 auto", padding: "16px 20px" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16, flexWrap: "wrap" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ width: 34, height: 34, borderRadius: 9, background: `linear-gradient(135deg, ${C.cyan}, #3B82F6)`, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: "#04121B", fontSize: 15 }}>AI</div>
              <div>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 15, color: C.text, lineHeight: 1.1 }}>AI Smart Stock Analyst</div>
                  <LiveBadge isLive={backendUp} />
                </div>
                <div style={{ fontSize: 10.5, color: C.faint }}>ระบบวิเคราะห์หุ้นอัจฉริยะ</div>
              </div>
            </div>
            <SearchBar onSelect={setSelected} />
          </div>
        </div>
      </div>

      {/* body */}
      <div style={{ maxWidth: 1080, margin: "0 auto", padding: "20px 20px 90px", display: "flex", flexDirection: "column", gap: 20 }}>
        <div>
          <SectionTitle eyebrow="Market Overview" title="ภาพรวมตลาดวันนี้" />
          <MarketOverview />
        </div>

        <SentimentPanel />

        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20 }}>
          <TopTen onSelect={setSelected} />
          <NewsFeed />
        </div>

        <div style={{ background: C.surface, border: `1px solid ${C.border}`, borderRadius: 18, padding: 16, display: "flex", gap: 14, alignItems: "center" }}>
          <div style={{ width: 38, height: 38, borderRadius: 10, background: C.amberDim, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
            <ShieldAlert size={18} color={C.amber} />
          </div>
          <div style={{ fontSize: 12, color: C.muted, lineHeight: 1.5 }}>
            <b style={{ color: C.text }}>Risk Disclaimer:</b> ข้อมูลและการวิเคราะห์จากระบบ AI นี้จัดทำขึ้นเพื่อวัตถุประสงค์ด้านข้อมูลและการศึกษาเท่านั้น ไม่ถือเป็นคำแนะนำในการลงทุน และไม่รับประกันผลตอบแทนหรือผลกำไร ผู้ลงทุนควรศึกษาข้อมูลและประเมินความเสี่ยงด้วยตนเองก่อนตัดสินใจลงทุน ข้อมูลทั้งหมดในหน้าจอนี้เป็นข้อมูลตัวอย่าง (Demo Data)
          </div>
        </div>
      </div>

      {/* mobile bottom nav (visual) */}
      <div style={{
        position: "fixed", bottom: 0, left: 0, right: 0, background: C.bg2, borderTop: `1px solid ${C.border}`,
        display: "flex", justifyContent: "space-around", padding: "10px 0 14px", zIndex: 20,
      }}>
        {[
          { icon: Home, label: "Home", active: true },
          { icon: BarChart2, label: "Market" },
          { icon: Search, label: "Analyze" },
          { icon: Star, label: "Watchlist" },
          { icon: Briefcase, label: "Portfolio" },
        ].map(({ icon: Icon, label, active }) => (
          <div key={label} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 3, color: active ? C.cyan : C.faint }}>
            <Icon size={19} />
            <span style={{ fontSize: 9.5 }}>{label}</span>
          </div>
        ))}
      </div>

      {selected && <StockDetail stock={selected} onClose={() => setSelected(null)} />}
    </div>
  );
}
