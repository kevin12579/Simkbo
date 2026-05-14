/* simkbo — 웹 데스크탑 라이트 테마 / 한국어 / KBO 팀 컬러 / 풀 기능 프로토타입 */

const { useState, useMemo, useEffect } = React;

/* ───────────── 데이터 ───────────── */

const TEAMS = {
  DOO: { code: "DOO", name: "두산",   full: "두산 베어스",   color: "#131230", stadium: "잠실야구장" },
  LGT: { code: "LGT", name: "LG",     full: "LG 트윈스",     color: "#C30452", stadium: "잠실야구장" },
  KIW: { code: "KIW", name: "키움",   full: "키움 히어로즈", color: "#570514", stadium: "고척스카이돔" },
  KTW: { code: "KTW", name: "KT",     full: "KT 위즈",       color: "#000000", stadium: "수원KT위즈파크" },
  SSG: { code: "SSG", name: "SSG",    full: "SSG 랜더스",    color: "#CE0E2D", stadium: "인천SSG랜더스필드" },
  NCD: { code: "NCD", name: "NC",     full: "NC 다이노스",   color: "#315288", stadium: "창원NC파크" },
  KIA: { code: "KIA", name: "KIA",    full: "KIA 타이거즈",  color: "#EA0029", stadium: "광주-기아챔피언스필드" },
  LOT: { code: "LOT", name: "롯데",   full: "롯데 자이언츠", color: "#041E42", stadium: "사직야구장" },
  SAM: { code: "SAM", name: "삼성",   full: "삼성 라이온즈", color: "#074CA1", stadium: "대구삼성라이온즈파크" },
  HAN: { code: "HAN", name: "한화",   full: "한화 이글스",   color: "#FF6600", stadium: "한화생명이글스파크" },
};

const GAMES = [
  { id: 1, time: "18:30", home: "DOO", away: "LGT", homeProb: 0.42, conf: "HIGH",
    homeStarter: { name: "곽빈", era: 3.42, whip: 1.21, k9: 8.4, recent5: 3.78, hand: "우" },
    awayStarter: { name: "임찬규", era: 2.98, whip: 1.08, k9: 9.1, recent5: 2.41, hand: "좌" } },
  { id: 2, time: "18:30", home: "KTW", away: "SSG", homeProb: 0.53, conf: "MEDIUM",
    homeStarter: { name: "벤자민", era: 3.11, whip: 1.18, k9: 8.8, recent5: 2.95, hand: "우" },
    awayStarter: { name: "로무알도", era: 4.05, whip: 1.34, k9: 7.6, recent5: 4.42, hand: "우" } },
  { id: 3, time: "18:30", home: "KIW", away: "NCD", homeProb: 0.39, conf: "MEDIUM",
    homeStarter: { name: "하영민", era: 4.51, whip: 1.42, k9: 6.8, recent5: 5.10, hand: "우" },
    awayStarter: { name: "레예스", era: 2.84, whip: 1.05, k9: 9.4, recent5: 2.31, hand: "우" } },
  { id: 4, time: "18:30", home: "SAM", away: "HAN", homeProb: 0.64, conf: "HIGH",
    homeStarter: { name: "원태인", era: 2.71, whip: 1.04, k9: 8.7, recent5: 2.18, hand: "우" },
    awayStarter: { name: "류현진", era: 3.34, whip: 1.18, k9: 7.9, recent5: 3.55, hand: "좌" } },
  { id: 5, time: "18:30", home: "KIA", away: "LOT", homeProb: 0.51, conf: "LOW",
    homeStarter: null,
    awayStarter: { name: "반즈", era: 3.78, whip: 1.25, k9: 8.1, recent5: 3.92, hand: "우" } },
];

const STANDINGS = [
  { code: "LGT", w: 21, l: 11, d: 0, wr: .656, last10: "7승 3패", str: { type: "W", n: 4 }, ops: .751, era: 3.87 },
  { code: "KIA", w: 19, l: 12, d: 1, wr: .613, last10: "6승 4패", str: { type: "W", n: 2 }, ops: .748, era: 3.95 },
  { code: "DOO", w: 18, l: 14, d: 0, wr: .563, last10: "5승 5패", str: { type: "L", n: 1 }, ops: .724, era: 4.12 },
  { code: "SAM", w: 17, l: 14, d: 1, wr: .548, last10: "6승 4패", str: { type: "W", n: 1 }, ops: .732, era: 3.66 },
  { code: "NCD", w: 17, l: 15, d: 0, wr: .531, last10: "5승 5패", str: { type: "W", n: 1 }, ops: .716, era: 4.08 },
  { code: "KTW", w: 15, l: 16, d: 1, wr: .484, last10: "4승 6패", str: { type: "L", n: 2 }, ops: .708, era: 4.21 },
  { code: "SSG", w: 14, l: 17, d: 1, wr: .452, last10: "4승 6패", str: { type: "L", n: 1 }, ops: .701, era: 4.45 },
  { code: "KIW", w: 13, l: 18, d: 1, wr: .419, last10: "3승 7패", str: { type: "L", n: 3 }, ops: .682, era: 4.68 },
  { code: "LOT", w: 12, l: 19, d: 1, wr: .387, last10: "3승 7패", str: { type: "L", n: 1 }, ops: .695, era: 4.71 },
  { code: "HAN", w: 11, l: 20, d: 1, wr: .355, last10: "4승 6패", str: { type: "L", n: 2 }, ops: .678, era: 4.92 },
];

/* ───────────── 공용 컴포넌트 ───────────── */

function TeamMark({ code, size = 36, ring = false }) {
  const t = TEAMS[code];
  return (
    <div style={{
      width: size, height: size, borderRadius: 6,
      background: t.color, color: "#fff",
      display: "grid", placeItems: "center",
      fontFamily: "var(--font-mono)", fontSize: size * 0.34,
      fontWeight: 700, letterSpacing: "0.02em",
      boxShadow: ring ? "0 0 0 3px #fff, 0 0 0 4px " + t.color : "none",
      flexShrink: 0,
    }}>{t.name}</div>
  );
}

function ConfPill({ level }) {
  const map = {
    HIGH:   { bg: "#e8f5ec", fg: "#1a7a3a", label: "신뢰도 높음"   },
    MEDIUM: { bg: "#fdf4e1", fg: "#9a6f0a", label: "신뢰도 보통"   },
    LOW:    { bg: "#f0f0ee", fg: "#7a7a78", label: "신뢰도 낮음"   },
  };
  const s = map[level];
  return (
    <span style={{
      background: s.bg, color: s.fg,
      fontSize: 11, fontWeight: 600,
      padding: "4px 9px", borderRadius: 4,
      display: "inline-flex", alignItems: "center", gap: 5,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 3, background: s.fg }} />
      {s.label}
    </span>
  );
}

function ProbBar({ home, away, homeCode, awayCode, height = 10 }) {
  const hPct = Math.round(home * 100);
  const aPct = 100 - hPct;
  const ht = TEAMS[homeCode], at = TEAMS[awayCode];
  return (
    <div style={{ display: "flex", height, borderRadius: 999, overflow: "hidden", background: "#eeeeec" }}>
      <div style={{ width: `${hPct}%`, background: ht.color, transition: "width 0.4s" }} />
      <div style={{ width: `${aPct}%`, background: at.color, transition: "width 0.4s" }} />
    </div>
  );
}

function Button({ children, onClick, variant = "primary", size = "md", icon }) {
  const variants = {
    primary: { bg: "#0a0a0a", fg: "#fff", border: "#0a0a0a", hov: "#0a2a5e" },
    ghost:   { bg: "transparent", fg: "#0a0a0a", border: "#c0cce0", hov: "#eef2f9" },
    accent:  { bg: "#c8102e", fg: "#fff", border: "#c8102e", hov: "#a30d24" },
  };
  const v = variants[variant];
  const sizes = { sm: "6px 10px", md: "9px 16px", lg: "12px 22px" };
  const [hov, setHov] = useState(false);
  return (
    <button onClick={onClick}
      onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        background: hov ? v.hov : v.bg, color: v.fg,
        border: `1px solid ${v.border}`, borderRadius: 6,
        padding: sizes[size], fontSize: 13, fontWeight: 500,
        cursor: "pointer", fontFamily: "var(--font-sans)",
        display: "inline-flex", alignItems: "center", gap: 6,
        transition: "background 0.15s",
      }}>
      {icon}{children}
    </button>
  );
}

function Toast({ msg, onClose }) {
  useEffect(() => {
    if (!msg) return;
    const t = setTimeout(onClose, 2400);
    return () => clearTimeout(t);
  }, [msg]);
  if (!msg) return null;
  return (
    <div style={{
      position: "fixed", bottom: 32, left: "50%", transform: "translateX(-50%)",
      background: "#0a0a0a", color: "#fff", padding: "12px 18px",
      borderRadius: 8, fontSize: 13, fontWeight: 500, zIndex: 100,
      boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
    }}>
      {msg}
    </div>
  );
}

/* ───────────── 헤더 / 네비 ───────────── */

function TopNav({ page, setPage, favorites }) {
  const items = [
    { id: "home",    label: "오늘의 경기" },
    { id: "stats",   label: "통계" },
    { id: "mypicks", label: "마이픽" },
    { id: "model",   label: "모델 성능" },
  ];
  return (
    <header style={{
      borderBottom: "1px solid #dce4f0", background: "#ffffff",
      position: "sticky", top: 0, zIndex: 50,
    }}>
      <div style={{
        maxWidth: 1280, margin: "0 auto", padding: "0 32px",
        height: 64, display: "flex", alignItems: "center", gap: 40,
      }}>
        <div onClick={() => setPage("home")} style={{ cursor: "pointer", display: "flex", alignItems: "center", gap: 8 }}>
          <div style={{
            width: 26, height: 26, borderRadius: 6,
            background: "#c8102e", display: "grid", placeItems: "center",
            color: "#fff", fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 13,
          }}>S</div>
          <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 18, letterSpacing: "-0.01em" }}>
            simkbo
          </span>
        </div>

        <nav style={{ display: "flex", gap: 4, flex: 1 }}>
          {items.map(it => (
            <button key={it.id} onClick={() => setPage(it.id)}
              style={{
                background: "transparent", border: "none", cursor: "pointer",
                padding: "8px 14px", fontSize: 14, fontFamily: "var(--font-sans)",
                fontWeight: 500,
                color: page === it.id ? "#0a0a0a" : "#4a5872",
                position: "relative",
                borderBottom: page === it.id ? "2px solid #c8102e" : "2px solid transparent",
                marginBottom: -1,
              }}>
              {it.label}
            </button>
          ))}
        </nav>

        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, color: "#4a5872", fontFamily: "var(--font-mono)" }}>
            <span style={{ width: 6, height: 6, borderRadius: 3, background: "#1a7a3a" }} />
            모델 v1.0 · 18:14 갱신
          </div>
          <button onClick={() => setPage("mypicks")} style={{
            background: "#eef2f9", border: "1px solid #dce4f0", borderRadius: 999,
            padding: "6px 12px", fontSize: 12, cursor: "pointer", fontFamily: "var(--font-mono)",
            display: "flex", alignItems: "center", gap: 5,
          }}>
            ★ {favorites.size}
          </button>
          <div style={{
            width: 32, height: 32, borderRadius: 16, background: "#0a2a5e",
            color: "#fff", display: "grid", placeItems: "center",
            fontSize: 11, fontWeight: 600,
          }}>SU</div>
        </div>
      </div>
    </header>
  );
}

/* ───────────── 홈 — 오늘의 경기 ───────────── */

function HomePage({ setPage, setSelectedGame, favorites, toggleFavorite, picks, setPick, showToast }) {
  const [tab, setTab] = useState("today");
  const [filter, setFilter] = useState("all");

  const filtered = useMemo(() => {
    if (filter === "all") return GAMES;
    if (filter === "high") return GAMES.filter(g => g.conf === "HIGH");
    if (filter === "close") return GAMES.filter(g => Math.abs(g.homeProb - 0.5) < 0.1);
    return GAMES;
  }, [filter]);

  const bestPick = [...GAMES].sort((a, b) => Math.abs(b.homeProb - 0.5) - Math.abs(a.homeProb - 0.5))[0];

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      {/* 상단 헤더 영역 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 13, color: "#4a5872", fontFamily: "var(--font-mono)", letterSpacing: "0.04em" }}>
            2026.05.12 · 화요일
          </div>
          <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0" }}>
            오늘의 KBO 승부예측
          </h1>
          <p style={{ fontSize: 14, color: "#4a5872", marginTop: 6 }}>
            5경기 · XGBoost + LSTM 앙상블 모델이 분석한 승리 확률
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Button variant="ghost" size="sm" onClick={() => showToast("예측을 새로고침합니다")}>↻ 새로고침</Button>
          <Button variant="ghost" size="sm" onClick={() => setPage("stats")}>통계 보기 →</Button>
        </div>
      </div>

      {/* 오늘의 강력 추천 */}
      <div onClick={() => { setSelectedGame(bestPick.id); setPage("game"); }}
        style={{
          background: "linear-gradient(135deg, #0a2a5e 0%, #1a3a6e 100%)",
          color: "#fff", borderRadius: 16, padding: "28px 32px",
          display: "grid", gridTemplateColumns: "1fr auto", gap: 32,
          cursor: "pointer", marginBottom: 32, position: "relative", overflow: "hidden",
        }}>
        <div style={{ position: "absolute", right: -40, top: -40, width: 240, height: 240, borderRadius: "50%", background: "rgba(200,16,46,0.25)", filter: "blur(60px)" }} />
        <div style={{ zIndex: 1 }}>
          <div style={{ fontSize: 11, letterSpacing: "0.14em", color: "#9bb6e6", fontFamily: "var(--font-mono)", fontWeight: 600, marginBottom: 14 }}>
            ★ 오늘의 강력 추천
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 16 }}>
            <TeamMark code={bestPick.homeProb >= 0.5 ? bestPick.home : bestPick.away} size={56} />
            <div>
              <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>
                {TEAMS[bestPick.homeProb >= 0.5 ? bestPick.home : bestPick.away].full}
              </div>
              <div style={{ fontSize: 13, color: "#9bb6e6", marginTop: 4 }}>
                {bestPick.homeProb >= 0.5 ? "홈" : "원정"} · vs {TEAMS[bestPick.homeProb >= 0.5 ? bestPick.away : bestPick.home].full}
              </div>
            </div>
          </div>
          <div style={{ fontSize: 13, color: "#cfdcf2", lineHeight: 1.65, maxWidth: 540 }}>
            선발 매치업과 최근 폼이 일치하는 가장 신뢰도 높은 경기입니다.
            모델이 확률 격차 <b style={{ color: "#fff" }}>{Math.round(Math.abs(bestPick.homeProb - 0.5) * 200)}%p</b> 를 예측했습니다.
          </div>
        </div>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "center", alignItems: "flex-end", zIndex: 1 }}>
          <div style={{
            fontFamily: "var(--font-mono)", fontSize: 72, fontWeight: 700,
            letterSpacing: "-0.04em", lineHeight: 1, color: "#fff",
          }}>
            {Math.round(Math.max(bestPick.homeProb, 1 - bestPick.homeProb) * 100)}<span style={{ fontSize: 32, color: "#9bb6e6" }}>%</span>
          </div>
          <div style={{ fontSize: 12, color: "#9bb6e6", marginTop: 6, letterSpacing: "0.08em" }}>승리 확률</div>
          <div style={{ marginTop: 18, fontSize: 12, color: "#fff", opacity: 0.8 }}>
            상세 분석 보기 →
          </div>
        </div>
      </div>

      {/* 탭 + 필터 */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, borderBottom: "1px solid #dce4f0" }}>
        <div style={{ display: "flex", gap: 4 }}>
          {[
            { id: "today", label: "오늘", count: 5 },
            { id: "live", label: "실시간", count: 0 },
            { id: "results", label: "결과", count: 8 },
          ].map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              style={{
                background: "transparent", border: "none", cursor: "pointer",
                padding: "10px 14px", fontSize: 14, fontWeight: 500,
                color: tab === t.id ? "#0a0a0a" : "#7886a0",
                borderBottom: tab === t.id ? "2px solid #0a0a0a" : "2px solid transparent",
                marginBottom: -1, fontFamily: "var(--font-sans)",
              }}>
              {t.label} <span style={{ color: "#9aa5bd", fontFamily: "var(--font-mono)", fontSize: 11 }}>{t.count}</span>
            </button>
          ))}
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          {[
            { id: "all", label: "전체" },
            { id: "high", label: "신뢰도 높음" },
            { id: "close", label: "박빙" },
          ].map(f => (
            <button key={f.id} onClick={() => setFilter(f.id)}
              style={{
                background: filter === f.id ? "#0a0a0a" : "transparent",
                color: filter === f.id ? "#fff" : "#4a5872",
                border: filter === f.id ? "1px solid #0a0a0a" : "1px solid #c0cce0",
                borderRadius: 999, padding: "5px 12px", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap",
              }}>
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 경기 카드 그리드 */}
      {tab === "today" && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))", gap: 16, marginTop: 20 }}>
          {filtered.map(g => (
            <GameCard key={g.id} g={g}
              onOpen={() => { setSelectedGame(g.id); setPage("game"); }}
              isFav={favorites.has(g.id)}
              onToggleFav={() => toggleFavorite(g.id)}
              myPick={picks[g.id]}
              onPick={(side) => { setPick(g.id, side); showToast(`${TEAMS[side === "home" ? g.home : g.away].full} 픽 저장됨`); }}
            />
          ))}
        </div>
      )}
      {tab === "live" && (
        <EmptyState icon="⚾" title="진행 중인 경기가 없습니다" desc="첫 경기 시작은 18:30 입니다" />
      )}
      {tab === "results" && (
        <div style={{ marginTop: 20 }}><ResultsList /></div>
      )}
    </main>
  );
}

function GameCard({ g, onOpen, isFav, onToggleFav, myPick, onPick }) {
  const hPct = Math.round(g.homeProb * 100);
  const aPct = 100 - hPct;
  const favHome = g.homeProb >= 0.5;
  const home = TEAMS[g.home], away = TEAMS[g.away];
  const [hov, setHov] = useState(false);

  return (
    <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        background: "#fff", border: "1px solid #dce4f0", borderRadius: 12,
        padding: 20, transition: "all 0.15s", position: "relative", overflow: "hidden",
        boxShadow: hov ? "0 8px 24px rgba(10,42,94,0.10)" : "0 1px 2px rgba(10,42,94,0.03)",
        transform: hov ? "translateY(-2px)" : "translateY(0)",
      }}>
      {/* Team color split accent */}
      <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 4, display: "flex" }}>
        <div style={{ flex: g.homeProb, background: home.color }} />
        <div style={{ flex: 1 - g.homeProb, background: away.color }} />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 600 }}>{g.time}</span>
          <span style={{ color: "#c0cce0" }}>·</span>
          <span style={{ fontSize: 12, color: "#7886a0" }}>{home.stadium}</span>
        </div>
        <button onClick={onToggleFav}
          style={{ background: "transparent", border: "none", cursor: "pointer", fontSize: 18, color: isFav ? "#d4a017" : "#c0cce0" }}>
          {isFav ? "★" : "☆"}
        </button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 12, marginBottom: 14 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, opacity: favHome ? 1 : 0.55, minWidth: 0 }}>
          <TeamMark code={g.home} size={36} />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 15, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: favHome ? home.color : "#0a0a0a" }}>{home.full}</div>
            <div style={{ fontSize: 11, color: "#7886a0", marginTop: 2 }}>홈</div>
          </div>
        </div>
        <div style={{ textAlign: "center", fontFamily: "var(--font-mono)" }}>
          <div style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em" }}>
            <span style={{ color: favHome ? home.color : "#c0cce0" }}>{hPct}</span>
            <span style={{ color: "#c0cce0", margin: "0 4px" }}>:</span>
            <span style={{ color: !favHome ? away.color : "#c0cce0" }}>{aPct}</span>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10, opacity: !favHome ? 1 : 0.55, justifyContent: "flex-end", minWidth: 0 }}>
          <div style={{ textAlign: "right", minWidth: 0 }}>
            <div style={{ fontSize: 15, fontWeight: 600, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", color: !favHome ? away.color : "#0a0a0a" }}>{away.full}</div>
            <div style={{ fontSize: 11, color: "#7886a0", marginTop: 2 }}>원정</div>
          </div>
          <TeamMark code={g.away} size={36} />
        </div>
      </div>

      <ProbBar home={g.homeProb} away={1 - g.homeProb} homeCode={g.home} awayCode={g.away} height={6} />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginTop: 14, fontSize: 12, fontFamily: "var(--font-mono)" }}>
        <div style={{ color: "#4a5872" }}>
          {g.homeStarter ? <><b style={{ color: "#0a0a0a" }}>{g.homeStarter.name}</b> ERA {g.homeStarter.era}</> : <span style={{ color: "#9aa5bd" }}>선발 미정</span>}
        </div>
        <div style={{ color: "#4a5872", textAlign: "right" }}>
          {g.awayStarter ? <><b style={{ color: "#0a0a0a" }}>{g.awayStarter.name}</b> ERA {g.awayStarter.era}</> : <span style={{ color: "#9aa5bd" }}>선발 미정</span>}
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 16, paddingTop: 14, borderTop: "1px solid #e8eef7" }}>
        <ConfPill level={g.conf} />
        <div style={{ display: "flex", gap: 6 }}>
          <button onClick={() => onPick("home")}
            style={{
              fontSize: 11, padding: "5px 9px", borderRadius: 5, cursor: "pointer",
              background: myPick === "home" ? home.color : "transparent",
              color: myPick === "home" ? "#fff" : home.color,
              border: `1px solid ${myPick === "home" ? home.color : "#dce4f0"}`,
              fontWeight: 600, whiteSpace: "nowrap",
            }}>{home.name}</button>
          <button onClick={() => onPick("away")}
            style={{
              fontSize: 11, padding: "5px 9px", borderRadius: 5, cursor: "pointer",
              background: myPick === "away" ? away.color : "transparent",
              color: myPick === "away" ? "#fff" : away.color,
              border: `1px solid ${myPick === "away" ? away.color : "#dce4f0"}`,
              fontWeight: 600, whiteSpace: "nowrap",
            }}>{away.name}</button>
          <button onClick={onOpen} style={{
            fontSize: 11, padding: "5px 10px", borderRadius: 5, cursor: "pointer",
            background: "#0a0a0a", color: "#fff", border: "1px solid #0a0a0a", fontWeight: 600, whiteSpace: "nowrap",
          }}>상세 →</button>
        </div>
      </div>
    </div>
  );
}

function EmptyState({ icon, title, desc }) {
  return (
    <div style={{ textAlign: "center", padding: "80px 0", color: "#7886a0" }}>
      <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.5 }}>{icon}</div>
      <div style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 4 }}>{title}</div>
      <div style={{ fontSize: 13 }}>{desc}</div>
    </div>
  );
}

function ResultsList() {
  const results = [
    { date: "05.11", home: "LGT", away: "DOO", hs: 7, as: 3, pred: 0.58, correct: true },
    { date: "05.11", home: "SAM", away: "KIA", hs: 4, as: 5, pred: 0.52, correct: false },
    { date: "05.11", home: "NCD", away: "KTW", hs: 6, as: 2, pred: 0.61, correct: true },
    { date: "05.10", home: "HAN", away: "LOT", hs: 3, as: 5, pred: 0.38, correct: true },
    { date: "05.10", home: "SSG", away: "KIW", hs: 8, as: 4, pred: 0.55, correct: true },
  ];
  return (
    <div style={{ border: "1px solid #dce4f0", borderRadius: 10, overflow: "hidden", background: "#fff" }}>
      {results.map((r, i) => {
        const homeWon = r.hs > r.as;
        return (
          <div key={i} style={{
            display: "grid", gridTemplateColumns: "70px 1fr 100px 120px 80px", gap: 16,
            alignItems: "center", padding: "14px 20px",
            borderBottom: i < results.length - 1 ? "1px solid #e8eef7" : "none",
            fontSize: 13,
          }}>
            <span style={{ fontFamily: "var(--font-mono)", color: "#7886a0" }}>{r.date}</span>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <TeamMark code={r.home} size={24} />
              <span style={{ fontWeight: homeWon ? 600 : 400, color: homeWon ? "#0a0a0a" : "#7886a0" }}>{TEAMS[r.home].full}</span>
              <span style={{ color: "#c0cce0" }}>vs</span>
              <TeamMark code={r.away} size={24} />
              <span style={{ fontWeight: !homeWon ? 600 : 400, color: !homeWon ? "#0a0a0a" : "#7886a0" }}>{TEAMS[r.away].full}</span>
            </div>
            <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 15 }}>
              {r.hs} : {r.as}
            </span>
            <span style={{ fontFamily: "var(--font-mono)", fontSize: 12, color: "#4a5872" }}>
              예측 홈 {Math.round(r.pred * 100)}%
            </span>
            <span style={{
              fontSize: 11, fontWeight: 600, padding: "3px 8px", borderRadius: 4,
              background: r.correct ? "#e8f5ec" : "#fde8eb",
              color: r.correct ? "#1a7a3a" : "#c8102e", justifySelf: "flex-end",
            }}>
              {r.correct ? "적중" : "실패"}
            </span>
          </div>
        );
      })}
    </div>
  );
}

/* ───────────── 경기 상세 ───────────── */

function GamePage({ gameId, setPage, favorites, toggleFavorite, picks, setPick, showToast }) {
  const g = GAMES.find(x => x.id === gameId) || GAMES[0];
  const home = TEAMS[g.home], away = TEAMS[g.away];
  const [showAllFactors, setShowAllFactors] = useState(false);

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      <button onClick={() => setPage("home")}
        style={{
          background: "transparent", border: "none", cursor: "pointer",
          fontSize: 13, color: "#4a5872", padding: 0, marginBottom: 20,
          display: "flex", alignItems: "center", gap: 6,
        }}>← 오늘의 경기로</button>

      {/* 매치업 헤더 */}
      <div style={{
        background: "#fff", border: "1px solid #dce4f0", borderRadius: 16,
        padding: "32px 40px", marginBottom: 20,
      }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24, fontSize: 13, color: "#4a5872", fontFamily: "var(--font-mono)" }}>
          <span>2026.05.12 화 · {g.time} KST · {home.stadium}</span>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => toggleFavorite(g.id)} style={{
              background: "transparent", border: "1px solid #dce4f0", borderRadius: 6,
              padding: "5px 11px", fontSize: 12, cursor: "pointer", color: favorites.has(g.id) ? "#d4a017" : "#4a5872",
            }}>{favorites.has(g.id) ? "★ 저장됨" : "☆ 저장"}</button>
            <button onClick={() => showToast("링크가 복사되었습니다")} style={{
              background: "transparent", border: "1px solid #dce4f0", borderRadius: 6,
              padding: "5px 11px", fontSize: 12, cursor: "pointer", color: "#4a5872",
            }}>↗ 공유</button>
          </div>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <TeamMark code={g.home} size={72} />
            <div style={{ fontSize: 22, fontWeight: 700 }}>{home.full}</div>
            <div style={{ fontSize: 12, color: "#4a5872", fontFamily: "var(--font-mono)" }}>
              홈 · 18승 14패 · 5할6푼3리
            </div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 32, color: "#c0cce0", fontFamily: "var(--font-mono)", letterSpacing: "0.1em" }}>VS</div>
            <div style={{ fontSize: 11, color: "#7886a0", marginTop: 6, padding: "4px 10px", background: "#eef2f9", borderRadius: 4, fontFamily: "var(--font-mono)" }}>
              상대전적 4승 6패
            </div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <TeamMark code={g.away} size={72} />
            <div style={{ fontSize: 22, fontWeight: 700 }}>{away.full}</div>
            <div style={{ fontSize: 12, color: "#4a5872", fontFamily: "var(--font-mono)" }}>
              원정 · 21승 11패 · 6할5푼6리
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20 }}>
        {/* 왼쪽 컬럼 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* 큰 확률 카드 */}
          <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 28 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>승리 확률</h2>
              <ConfPill level={g.conf} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", alignItems: "center", gap: 20 }}>
              <div>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 42, fontWeight: 700, letterSpacing: "-0.03em", color: g.homeProb >= 0.5 ? home.color : "#9aa5bd" }}>
                  {Math.round(g.homeProb * 100)}<span style={{ fontSize: 22 }}>%</span>
                </div>
                <div style={{ fontSize: 12, color: "#4a5872", letterSpacing: "0.06em", marginTop: 2 }}>{home.full}</div>
              </div>
              <div>
                <ProbBar home={g.homeProb} away={1 - g.homeProb} homeCode={g.home} awayCode={g.away} height={14} />
                <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 11, color: "#7886a0", fontFamily: "var(--font-mono)" }}>
                  <span>업데이트 18:14</span>
                  <span>모델 v1.0-xgb+lstm</span>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontFamily: "var(--font-mono)", fontSize: 42, fontWeight: 700, letterSpacing: "-0.03em", color: g.homeProb < 0.5 ? away.color : "#9aa5bd" }}>
                  {Math.round((1 - g.homeProb) * 100)}<span style={{ fontSize: 22 }}>%</span>
                </div>
                <div style={{ fontSize: 12, color: "#4a5872", letterSpacing: "0.06em", marginTop: 2 }}>{away.full}</div>
              </div>
            </div>

            {/* 모델 분해 */}
            <div style={{ marginTop: 24, paddingTop: 20, borderTop: "1px solid #e8eef7" }}>
              <div style={{ fontSize: 11, color: "#7886a0", letterSpacing: "0.1em", marginBottom: 12, fontWeight: 600 }}>
                모델 분해
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <ModelBar label="XGBoost" home={0.40} away={0.60} weight="0.60" homeCode={g.home} awayCode={g.away} />
                <ModelBar label="LSTM" home={0.45} away={0.55} weight="0.40" homeCode={g.home} awayCode={g.away} />
                <ModelBar label="앙상블" home={g.homeProb} away={1 - g.homeProb} weight="최종" homeCode={g.home} awayCode={g.away} highlight />
              </div>
            </div>
          </div>

          {/* 픽 버튼 */}
          <div style={{ background: "#f5f8fd", border: "1px dashed #c0cce0", borderRadius: 12, padding: 20, display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ flex: 1 }}>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 2 }}>나의 픽</div>
              <div style={{ fontSize: 12, color: "#4a5872" }}>예측을 저장하면 마이픽 페이지에서 정확도를 추적합니다</div>
            </div>
            <button onClick={() => { setPick(g.id, "home"); showToast(`${home.full} 픽 저장됨`); }}
              style={{
                background: picks[g.id] === "home" ? home.color : "#fff",
                color: picks[g.id] === "home" ? "#fff" : home.color,
                border: `1.5px solid ${home.color}`, borderRadius: 6,
                padding: "10px 18px", fontSize: 13, fontWeight: 600, cursor: "pointer",
              }}>{home.name} 픽</button>
            <button onClick={() => { setPick(g.id, "away"); showToast(`${away.full} 픽 저장됨`); }}
              style={{
                background: picks[g.id] === "away" ? away.color : "#fff",
                color: picks[g.id] === "away" ? "#fff" : away.color,
                border: `1.5px solid ${away.color}`, borderRadius: 6,
                padding: "10px 18px", fontSize: 13, fontWeight: 600, cursor: "pointer",
              }}>{away.name} 픽</button>
          </div>

          {/* 핵심 요인 */}
          <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 24 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
              <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>예측 핵심 요인</h2>
              <button onClick={() => setShowAllFactors(!showAllFactors)} style={{
                background: "transparent", border: "none", color: "#4a5872",
                fontSize: 12, cursor: "pointer", fontFamily: "var(--font-sans)",
              }}>{showAllFactors ? "접기 ↑" : "전체 보기 ↓"}</button>
            </div>
            <FactorList all={showAllFactors} home={g.home} away={g.away} />
          </div>
        </div>

        {/* 오른쪽 컬럼 */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          {/* AI 분석 */}
          <div style={{
            background: "linear-gradient(160deg, #eef2fa, #f5f8fd)",
            border: "1px solid #dce4f0", borderRadius: 12, padding: 22,
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
              <span style={{ color: "#9a6f0a", fontSize: 16 }}>✦</span>
              <span style={{ fontSize: 14, fontWeight: 600 }}>AI 분석 근거</span>
              <span style={{ marginLeft: "auto", fontSize: 10, color: "#7886a0", fontFamily: "var(--font-mono)" }}>Claude · 3초 전</span>
            </div>
            <p style={{ fontSize: 13.5, lineHeight: 1.75, color: "#2a3548", margin: 0, textWrap: "pretty" }}>
              {away.full}이 선발 매치업에서 명확한 우위를 가져갑니다. 임찬규의 최근 5경기 평균자책점{" "}
              <b style={{ background: "#fdf4e1", padding: "0 4px" }}>2.98</b>과 WHIP 1.08은 최근 10경기 타율{" "}
              <b>.241</b>에 그친 {home.full} 타선을 상대로 명확한 실점 억제 우위를 만들어줍니다.
              잠실 홈 어드밴티지가 격차를 다소 좁히지만, 시즌 승률 차이(.656 vs .563)와 LG의 4연승이
              모델을 원정팀 쪽으로 기울이게 합니다.
            </p>
            <div style={{ display: "flex", gap: 6, marginTop: 14, flexWrap: "wrap" }}>
              {["선발투수 ERA", "최근 10경기", "시즌 승률"].map(t => (
                <span key={t} style={{
                  fontSize: 11, padding: "3px 8px", borderRadius: 4,
                  background: "#fff", color: "#4a5872", border: "1px solid #dce4f0",
                }}>#{t}</span>
              ))}
            </div>
          </div>

          {/* 선발 투수 */}
          <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 24 }}>
            <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 16px" }}>선발 투수 매치업</h2>
            <PitcherCard team={g.home} pitcher={g.homeStarter} side="홈" />
            <div style={{ height: 1, background: "#e8eef7", margin: "16px 0" }} />
            <PitcherCard team={g.away} pitcher={g.awayStarter} side="원정" highlight />
          </div>

          {/* 날씨 */}
          <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 20 }}>
            <div style={{ fontSize: 12, color: "#7886a0", letterSpacing: "0.1em", marginBottom: 12, fontWeight: 600 }}>
              경기 환경
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
              {[
                ["기온", "18°C"], ["강수확률", "10%"], ["풍속", "2.3 m/s"],
              ].map(([k, v]) => (
                <div key={k}>
                  <div style={{ fontSize: 11, color: "#7886a0", letterSpacing: "0.04em" }}>{k}</div>
                  <div style={{ fontSize: 17, fontWeight: 600, fontFamily: "var(--font-mono)", marginTop: 2 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}

function ModelBar({ label, home, away, weight, homeCode, awayCode, highlight }) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "70px 1fr 50px", alignItems: "center", gap: 12 }}>
      <span style={{ fontSize: 12, fontWeight: highlight ? 700 : 500, color: highlight ? "#0a0a0a" : "#4a5872", fontFamily: "var(--font-mono)" }}>
        {label}
      </span>
      <div style={{ position: "relative", height: 24, background: "#eef2f9", borderRadius: 4, overflow: "hidden", display: "flex" }}>
        <div style={{ width: `${home * 100}%`, background: TEAMS[homeCode].color, opacity: highlight ? 1 : 0.7 }} />
        <div style={{ width: `${away * 100}%`, background: TEAMS[awayCode].color, opacity: highlight ? 1 : 0.7 }} />
        <span style={{
          position: "absolute", inset: 0, display: "grid", placeItems: "center",
          fontSize: 11, fontFamily: "var(--font-mono)", color: "#fff", fontWeight: 600,
          textShadow: "0 0 4px rgba(0,0,0,0.4)",
        }}>
          {Math.round(home * 100)} / {Math.round(away * 100)}
        </span>
      </div>
      <span style={{ fontSize: 11, color: "#7886a0", fontFamily: "var(--font-mono)", textAlign: "right" }}>{weight}</span>
    </div>
  );
}

function PitcherCard({ team, pitcher, side, highlight }) {
  const t = TEAMS[team];
  if (!pitcher) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <TeamMark code={team} size={32} />
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#9aa5bd" }}>선발 미정</div>
          <div style={{ fontSize: 11, color: "#9aa5bd", marginTop: 2 }}>{side}</div>
        </div>
      </div>
    );
  }
  return (
    <div>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
        <TeamMark code={team} size={32} />
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 600 }}>{pitcher.name}</div>
          <div style={{ fontSize: 11, color: "#7886a0", marginTop: 1 }}>{side} · {pitcher.hand}투</div>
        </div>
        {highlight && (
          <span style={{ fontSize: 10, padding: "3px 7px", background: "#e8f5ec", color: "#1a7a3a", borderRadius: 4, fontWeight: 600 }}>
            우세
          </span>
        )}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
        {[
          ["ERA", pitcher.era], ["WHIP", pitcher.whip],
          ["K/9", pitcher.k9], ["최근 5", pitcher.recent5],
        ].map(([k, v]) => (
          <div key={k} style={{ background: "#f5f8fd", borderRadius: 6, padding: "8px 10px" }}>
            <div style={{ fontSize: 10, color: "#7886a0", letterSpacing: "0.06em" }}>{k}</div>
            <div style={{ fontSize: 15, fontWeight: 700, fontFamily: "var(--font-mono)", marginTop: 2 }}>{v}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function FactorList({ all, home, away }) {
  const factors = [
    { label: "선발 ERA",         hv: "3.42", av: "2.98", edge: "away", delta: "+0.44" },
    { label: "최근 10경기 승률", hv: ".500", av: ".700", edge: "away", delta: "+.200" },
    { label: "팀 OPS",           hv: ".724", av: ".751", edge: "away", delta: "+.027" },
    { label: "불펜 ERA",         hv: "4.12", av: "3.87", edge: "away", delta: "+0.25" },
    { label: "휴식일",           hv: "1일",  av: "2일",  edge: "away", delta: "+1일" },
    { label: "홈 어드밴티지",    hv: "+6%",  av: "—",    edge: "home", delta: "기본"  },
    { label: "팀 ERA",           hv: "4.12", av: "3.87", edge: "away", delta: "+0.25" },
    { label: "연승/연패",        hv: "L1",   av: "W4",   edge: "away", delta: "5"    },
  ];
  const visible = all ? factors : factors.slice(0, 5);
  return (
    <div style={{ border: "1px solid #e8eef7", borderRadius: 8, overflow: "hidden" }}>
      <div style={{
        display: "grid", gridTemplateColumns: "1fr 1.4fr 1fr 80px",
        padding: "8px 16px", fontSize: 10, color: "#7886a0",
        letterSpacing: "0.1em", fontWeight: 600,
        background: "#f5f8fd", borderBottom: "1px solid #e8eef7",
      }}>
        <span style={{ textAlign: "right" }}>{TEAMS[home].name}</span>
        <span style={{ textAlign: "center" }}>지표</span>
        <span>{TEAMS[away].name}</span>
        <span style={{ textAlign: "right" }}>차이</span>
      </div>
      {visible.map((f, i) => (
        <div key={i} style={{
          display: "grid", gridTemplateColumns: "1fr 1.4fr 1fr 80px",
          padding: "10px 16px", fontSize: 13, fontFamily: "var(--font-mono)",
          borderBottom: i < visible.length - 1 ? "1px solid #eef2f9" : "none",
          alignItems: "center",
        }}>
          <span style={{ textAlign: "right", fontWeight: 600, color: f.edge === "home" ? "#1a7a3a" : "#4a5872" }}>{f.hv}</span>
          <span style={{ textAlign: "center", color: "#4a5872", fontSize: 12, fontFamily: "var(--font-sans)" }}>{f.label}</span>
          <span style={{ fontWeight: 600, color: f.edge === "away" ? "#1a7a3a" : "#4a5872" }}>{f.av}</span>
          <span style={{ textAlign: "right", fontSize: 11, color: "#c8102e", fontWeight: 600 }}>{f.delta}</span>
        </div>
      ))}
    </div>
  );
}

/* ───────────── 통계 페이지 ───────────── */

function StatsPage({ setPage }) {
  const [tab, setTab] = useState("standings");
  const [sort, setSort] = useState("wr");

  const sorted = useMemo(() => {
    const arr = [...STANDINGS];
    arr.sort((a, b) => {
      if (sort === "wr") return b.wr - a.wr;
      if (sort === "ops") return b.ops - a.ops;
      if (sort === "era") return a.era - b.era;
      return 0;
    });
    return arr;
  }, [sort]);

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 13, color: "#4a5872", fontFamily: "var(--font-mono)" }}>2026 KBO 정규시즌</div>
        <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0" }}>통계</h1>
      </div>

      <div style={{ borderBottom: "1px solid #dce4f0", display: "flex", gap: 4, marginBottom: 24 }}>
        {[
          { id: "standings", label: "팀 순위" },
          { id: "pitchers", label: "투수" },
          { id: "batters", label: "타자" },
          { id: "h2h", label: "상대전적" },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{
              background: "transparent", border: "none", cursor: "pointer",
              padding: "10px 16px", fontSize: 14, fontWeight: 500,
              color: tab === t.id ? "#0a0a0a" : "#7886a0",
              borderBottom: tab === t.id ? "2px solid #c8102e" : "2px solid transparent",
              marginBottom: -1,
            }}>{t.label}</button>
        ))}
      </div>

      {tab === "standings" && (
        <>
          <div style={{ display: "flex", gap: 6, marginBottom: 14 }}>
            {[
              { id: "wr", label: "승률순" },
              { id: "ops", label: "OPS순" },
              { id: "era", label: "ERA순" },
            ].map(s => (
              <button key={s.id} onClick={() => setSort(s.id)} style={{
                background: sort === s.id ? "#0a0a0a" : "transparent",
                color: sort === s.id ? "#fff" : "#4a5872",
                border: `1px solid ${sort === s.id ? "#0a0a0a" : "#c0cce0"}`,
                borderRadius: 999, padding: "5px 12px", fontSize: 12, cursor: "pointer", whiteSpace: "nowrap",
              }}>{s.label}</button>
            ))}
          </div>
          <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 10, overflow: "hidden" }}>
            <div style={{
              display: "grid", gridTemplateColumns: "50px 2fr 100px 80px 80px 110px 90px 80px",
              padding: "12px 20px", fontSize: 11, color: "#7886a0", letterSpacing: "0.08em", fontWeight: 600,
              background: "#f5f8fd", borderBottom: "1px solid #dce4f0",
            }}>
              <span>순위</span>
              <span>팀</span>
              <span style={{ textAlign: "right" }}>경기</span>
              <span style={{ textAlign: "right" }}>승</span>
              <span style={{ textAlign: "right" }}>패</span>
              <span style={{ textAlign: "right" }}>승률</span>
              <span style={{ textAlign: "right" }}>최근 10</span>
              <span style={{ textAlign: "right" }}>연속</span>
            </div>
            {sorted.map((row, i) => (
              <div key={row.code} style={{
                display: "grid", gridTemplateColumns: "50px 2fr 100px 80px 80px 110px 90px 80px",
                padding: "14px 20px", fontSize: 13, alignItems: "center",
                borderBottom: i < sorted.length - 1 ? "1px solid #eef2f9" : "none",
                background: i < 5 ? "#fff" : "#fafcff",
              }}>
                <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: i < 5 ? "#c8102e" : "#9aa5bd" }}>
                  {String(i + 1).padStart(2, "0")}
                </span>
                <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <TeamMark code={row.code} size={28} />
                  <span style={{ fontWeight: 600 }}>{TEAMS[row.code].full}</span>
                </span>
                <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: "#4a5872" }}>{row.w + row.l + row.d}</span>
                <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 600 }}>{row.w}</span>
                <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: "#4a5872" }}>{row.l}</span>
                <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 14 }}>
                  .{String(row.wr.toFixed(3)).split(".")[1]}
                </span>
                <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 12, color: "#4a5872" }}>{row.last10}</span>
                <span style={{
                  textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 13,
                  color: row.str.type === "W" ? "#1a7a3a" : "#c8102e",
                }}>
                  {row.str.type === "W" ? `${row.str.n}연승` : `${row.str.n}연패`}
                </span>
              </div>
            ))}
          </div>
        </>
      )}

      {tab === "pitchers" && <PitcherRanking />}
      {tab === "batters" && <EmptyState icon="🏏" title="타자 통계 준비 중" desc="다음 업데이트에서 제공됩니다" />}
      {tab === "h2h" && <H2HMatrix />}
    </main>
  );
}

function PitcherRanking() {
  const pitchers = [
    { name: "임찬규",   team: "LGT", era: 2.98, whip: 1.08, k9: 9.1, w: 5, l: 1 },
    { name: "원태인",   team: "SAM", era: 2.71, whip: 1.04, k9: 8.7, w: 6, l: 2 },
    { name: "레예스",   team: "NCD", era: 2.84, whip: 1.05, k9: 9.4, w: 4, l: 2 },
    { name: "벤자민",   team: "KTW", era: 3.11, whip: 1.18, k9: 8.8, w: 5, l: 2 },
    { name: "류현진",   team: "HAN", era: 3.34, whip: 1.18, k9: 7.9, w: 3, l: 3 },
    { name: "곽빈",     team: "DOO", era: 3.42, whip: 1.21, k9: 8.4, w: 4, l: 3 },
    { name: "반즈",     team: "LOT", era: 3.78, whip: 1.25, k9: 8.1, w: 3, l: 3 },
    { name: "네일",     team: "KIA", era: 3.85, whip: 1.22, k9: 7.6, w: 4, l: 2 },
  ];
  return (
    <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 10, overflow: "hidden" }}>
      <div style={{
        display: "grid", gridTemplateColumns: "60px 2fr 1fr 80px 80px 80px 80px",
        padding: "12px 20px", fontSize: 11, color: "#7886a0", letterSpacing: "0.08em", fontWeight: 600,
        background: "#f5f8fd", borderBottom: "1px solid #dce4f0",
      }}>
        <span>순위</span><span>투수</span><span>팀</span>
        <span style={{ textAlign: "right" }}>ERA</span>
        <span style={{ textAlign: "right" }}>WHIP</span>
        <span style={{ textAlign: "right" }}>K/9</span>
        <span style={{ textAlign: "right" }}>W-L</span>
      </div>
      {pitchers.map((p, i) => (
        <div key={p.name} style={{
          display: "grid", gridTemplateColumns: "60px 2fr 1fr 80px 80px 80px 80px",
          padding: "12px 20px", fontSize: 13, alignItems: "center",
          borderBottom: i < pitchers.length - 1 ? "1px solid #eef2f9" : "none",
        }}>
          <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700, color: i < 3 ? "#c8102e" : "#9aa5bd" }}>
            {String(i + 1).padStart(2, "0")}
          </span>
          <span style={{ fontWeight: 600 }}>{p.name}</span>
          <span style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <TeamMark code={p.team} size={22} />
            <span style={{ fontSize: 12, color: "#4a5872" }}>{TEAMS[p.team].name}</span>
          </span>
          <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700 }}>{p.era}</span>
          <span style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{p.whip}</span>
          <span style={{ textAlign: "right", fontFamily: "var(--font-mono)" }}>{p.k9}</span>
          <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: "#4a5872" }}>{p.w}-{p.l}</span>
        </div>
      ))}
    </div>
  );
}

function H2HMatrix() {
  const codes = ["LGT", "KIA", "DOO", "SAM", "NCD", "KTW", "SSG", "KIW", "LOT", "HAN"];
  return (
    <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 10, padding: 16, overflowX: "auto" }}>
      <table style={{ borderCollapse: "collapse", fontSize: 12, fontFamily: "var(--font-mono)" }}>
        <thead>
          <tr>
            <th style={{ padding: 8 }}></th>
            {codes.map(c => (
              <th key={c} style={{ padding: 8 }}><TeamMark code={c} size={24} /></th>
            ))}
          </tr>
        </thead>
        <tbody>
          {codes.map((r, ri) => (
            <tr key={r}>
              <th style={{ padding: 8 }}><TeamMark code={r} size={24} /></th>
              {codes.map((c, ci) => {
                if (r === c) return <td key={c} style={{ padding: 6, background: "#eef2f9" }}></td>;
                const w = ((ri * 3 + ci * 7) % 7) + 2;
                const l = 10 - w;
                const win = w > l;
                return (
                  <td key={c} style={{
                    padding: "8px 10px", textAlign: "center",
                    background: win ? `rgba(26,122,58,${(w - 5) * 0.1})` : `rgba(200,16,46,${(5 - w) * 0.1})`,
                    fontWeight: 600,
                  }}>{w}-{l}</td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ───────────── 마이픽 ───────────── */

function MyPicksPage({ picks, setPick, setPage, setSelectedGame }) {
  const pickEntries = Object.entries(picks);
  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.02em", margin: 0 }}>마이픽</h1>
        <p style={{ fontSize: 14, color: "#4a5872", marginTop: 6 }}>
          내가 저장한 예측 · 적중률 추적
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 24 }}>
        {[
          { label: "총 픽", v: pickEntries.length, sub: "이번 시즌" },
          { label: "적중", v: "12", sub: "지난 30일" },
          { label: "적중률", v: "63%", sub: "+4%p vs 모델" },
          { label: "수익률", v: "+8.2%", sub: "균등 베팅 기준" },
        ].map(s => (
          <div key={s.label} style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 10, padding: 18 }}>
            <div style={{ fontSize: 11, color: "#7886a0", letterSpacing: "0.06em" }}>{s.label}</div>
            <div style={{ fontSize: 32, fontWeight: 700, fontFamily: "var(--font-mono)", letterSpacing: "-0.02em", marginTop: 4 }}>{s.v}</div>
            <div style={{ fontSize: 11, color: "#4a5872", marginTop: 2 }}>{s.sub}</div>
          </div>
        ))}
      </div>

      <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>오늘의 픽</h2>
      {pickEntries.length === 0 ? (
        <EmptyState icon="◇" title="저장된 픽이 없습니다" desc="오늘의 경기에서 팀을 선택해보세요" />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {pickEntries.map(([gid, side]) => {
            const g = GAMES.find(x => x.id === Number(gid));
            if (!g) return null;
            const team = TEAMS[side === "home" ? g.home : g.away];
            const otherTeam = TEAMS[side === "home" ? g.away : g.home];
            const prob = side === "home" ? g.homeProb : 1 - g.homeProb;
            return (
              <div key={gid} style={{
                background: "#fff", border: "1px solid #dce4f0", borderRadius: 10,
                padding: "16px 20px", display: "grid", gridTemplateColumns: "auto 1fr 100px auto",
                alignItems: "center", gap: 16,
              }}>
                <TeamMark code={team.code} size={36} />
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{team.full} 승리</div>
                  <div style={{ fontSize: 12, color: "#4a5872", marginTop: 2 }}>
                    vs {otherTeam.full} · {g.time}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 18, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{Math.round(prob * 100)}%</div>
                  <div style={{ fontSize: 10, color: "#7886a0" }}>모델 확률</div>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button onClick={() => { setSelectedGame(g.id); setPage("game"); }} style={{
                    background: "transparent", border: "1px solid #dce4f0", borderRadius: 6,
                    padding: "6px 12px", fontSize: 12, cursor: "pointer", color: "#4a5872",
                  }}>상세</button>
                  <button onClick={() => setPick(g.id, null)} style={{
                    background: "transparent", border: "1px solid #dce4f0", borderRadius: 6,
                    padding: "6px 10px", fontSize: 12, cursor: "pointer", color: "#c8102e",
                  }}>✕</button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </main>
  );
}

/* ───────────── 모델 성능 ───────────── */

function ModelPage() {
  const acc = [58, 60, 57, 62, 59, 63, 61, 64, 60, 62, 61, 63, 62, 61.4];
  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      <div style={{ marginBottom: 24 }}>
        <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.02em", margin: 0 }}>모델 성능</h1>
        <p style={{ fontSize: 14, color: "#4a5872", marginTop: 6 }}>
          XGBoost + LSTM 앙상블 · 모델 v1.0 · 최근 30일 기준
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20, marginBottom: 20 }}>
        <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 28 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 11, color: "#7886a0", letterSpacing: "0.1em", fontWeight: 600 }}>예측 정확도 (최근 14일)</div>
              <div style={{ fontSize: 48, fontWeight: 700, fontFamily: "var(--font-mono)", letterSpacing: "-0.03em", marginTop: 6 }}>
                61.4<span style={{ fontSize: 24, color: "#7886a0" }}>%</span>
              </div>
            </div>
            <span style={{ fontSize: 12, color: "#1a7a3a", background: "#e8f5ec", padding: "4px 10px", borderRadius: 4, fontWeight: 600 }}>
              ▲ +2.1%p vs 지난주
            </span>
          </div>
          <div style={{ display: "flex", gap: 3, alignItems: "flex-end", height: 100, marginTop: 24 }}>
            {acc.map((v, i) => (
              <div key={i} style={{
                flex: 1, height: `${(v - 50) * 5.5}px`,
                background: i === acc.length - 1 ? "#c8102e" : "#0a2a5e",
                borderRadius: 2,
                opacity: i === acc.length - 1 ? 1 : 0.6 + i * 0.025,
              }} />
            ))}
          </div>
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 8, fontSize: 10, color: "#7886a0", fontFamily: "var(--font-mono)" }}>
            <span>4.29</span><span>오늘</span>
          </div>
        </div>

        <div style={{ display: "grid", gap: 12 }}>
          {[
            { k: "Brier Score", v: "0.218", sub: "낮을수록 좋음" },
            { k: "Log Loss", v: "0.612", sub: "낮을수록 좋음" },
            { k: "ROC AUC", v: "0.687", sub: "1에 가까울수록 좋음" },
            { k: "Calibration", v: "Good", sub: "신뢰도 보정 양호" },
          ].map(m => (
            <div key={m.k} style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 10, padding: "14px 18px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600 }}>{m.k}</div>
                <div style={{ fontSize: 11, color: "#7886a0", marginTop: 2 }}>{m.sub}</div>
              </div>
              <div style={{ fontSize: 22, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{m.v}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 24 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 16px" }}>피처 중요도 (XGBoost)</h2>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          {[
            ["선발 ERA 차이", 100],
            ["최근 10경기 승률 차이", 82],
            ["팀 OPS 차이", 68],
            ["선발 WHIP 차이", 56],
            ["불펜 ERA 차이", 48],
            ["시즌 승률 차이", 41],
            ["연승/연패", 28],
            ["홈/원정 승률", 22],
            ["휴식일 차이", 15],
            ["상대전적", 11],
          ].map(([label, v]) => (
            <div key={label} style={{ display: "grid", gridTemplateColumns: "180px 1fr 40px", alignItems: "center", gap: 12 }}>
              <span style={{ fontSize: 12, color: "#2a3548" }}>{label}</span>
              <div style={{ height: 14, background: "#eef2f9", borderRadius: 3, overflow: "hidden" }}>
                <div style={{ width: `${v}%`, height: "100%", background: "linear-gradient(90deg, #0a2a5e, #c8102e)" }} />
              </div>
              <span style={{ fontSize: 11, fontFamily: "var(--font-mono)", textAlign: "right", color: "#4a5872" }}>0.{String(v).padStart(2, "0")}</span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}

/* ───────────── 광고 사이드 레일 ───────────── */

function AdRail({ side }) {
  // 사이드 광고 (Google AdSense 스타일) — 1600px 이상에서만 표시
  const ads = side === "left"
    ? [
        { kind: "promo", title: "두산 베어스 굿즈", body: "공식 스토어 신상품 출시", cta: "쇼핑하기", color: "#131230", tag: "스폰서" },
        { kind: "stat",  title: "오늘의 KBO 통계", body: "선발 매치업 분석 리포트 무료 다운로드", cta: "받아보기", color: "#0a2a5e", tag: "광고" },
        { kind: "image", title: "한화생명 이글스파크", body: "야구장 투어 패키지 ₩29,000", cta: "예약하기", color: "#FF6600", tag: "AD" },
      ]
    : [
        { kind: "promo", title: "삼성 라이온즈 시즌권", body: "2026 시즌 조기 예매 10% 할인", cta: "구매하기", color: "#074CA1", tag: "스폰서" },
        { kind: "stat",  title: "프리미엄 멤버십", body: "광고 없이 모든 통계와 예측을 무제한 이용", cta: "월 ₩3,900", color: "#c8102e", tag: "AD" },
        { kind: "image", title: "KBO 공식 굿즈샵", body: "신상 유니폼 · 모자 · 응원도구", cta: "둘러보기", color: "#EA0029", tag: "광고" },
      ];

  return (
    <aside style={{
      position: "fixed",
      top: 84,
      [side]: 8,
      width: 160,
      display: "flex", flexDirection: "column", gap: 16,
      zIndex: 10,
      pointerEvents: "auto",
    }}>
      <div style={{
        fontSize: 9, color: "#9aa5bd", letterSpacing: "0.16em", fontWeight: 600,
        fontFamily: "var(--font-mono)", textAlign: "center",
        padding: "2px 0", borderBottom: "1px solid #e8eef7",
      }}>
        ADVERTISEMENT
      </div>
      {ads.map((ad, i) => <AdCard key={i} ad={ad} />)}
      <div style={{
        fontSize: 9, color: "#9aa5bd", letterSpacing: "0.04em", textAlign: "center",
        fontFamily: "var(--font-mono)",
      }}>
        Ads by simkbo · <a href="#" style={{ color: "#9aa5bd" }}>광고 정보</a>
      </div>
    </aside>
  );
}

function AdCard({ ad }) {
  const [hov, setHov] = React.useState(false);
  return (
    <div onMouseEnter={() => setHov(true)} onMouseLeave={() => setHov(false)}
      style={{
        background: "#fff",
        border: "1px solid #dce4f0",
        borderRadius: 8,
        overflow: "hidden",
        cursor: "pointer",
        transition: "all 0.15s",
        boxShadow: hov ? "0 4px 12px rgba(10,42,94,0.10)" : "none",
        position: "relative",
      }}>
      {/* 광고 라벨 */}
      <div style={{
        position: "absolute", top: 6, right: 6, zIndex: 2,
        background: "rgba(255,255,255,0.95)",
        color: "#7886a0", fontSize: 8, fontWeight: 700,
        padding: "1px 5px", borderRadius: 2, letterSpacing: "0.08em",
        border: "1px solid #dce4f0", fontFamily: "var(--font-mono)",
      }}>{ad.tag}</div>

      {/* 비주얼 영역 */}
      <div style={{
        height: 100, background: ad.color, position: "relative",
        display: "grid", placeItems: "center", color: "#fff",
        overflow: "hidden",
      }}>
        {/* 베이스볼 텍스처 */}
        <div style={{
          position: "absolute", inset: 0,
          background: `radial-gradient(circle at 30% 30%, rgba(255,255,255,0.18) 0%, transparent 50%)`,
        }} />
        <div style={{ fontSize: 28, opacity: 0.9, position: "relative", zIndex: 1 }}>⚾</div>
        <div style={{
          position: "absolute", left: 8, bottom: 6,
          fontSize: 9, fontFamily: "var(--font-mono)",
          color: "rgba(255,255,255,0.7)", letterSpacing: "0.08em",
        }}>160 × 100</div>
      </div>

      {/* 카피 */}
      <div style={{ padding: "10px 12px 12px" }}>
        <div style={{ fontSize: 12, fontWeight: 700, lineHeight: 1.3, marginBottom: 4, color: "#0a0a0a" }}>
          {ad.title}
        </div>
        <div style={{ fontSize: 11, color: "#4a5872", lineHeight: 1.45, marginBottom: 10 }}>
          {ad.body}
        </div>
        <div style={{
          display: "inline-block", fontSize: 10, fontWeight: 700,
          color: ad.color, padding: "4px 9px",
          border: `1px solid ${ad.color}`, borderRadius: 4,
        }}>
          {ad.cta} →
        </div>
      </div>
    </div>
  );
}

/* ───────────── 상단 띠 광고 (배너) ───────────── */

function TopBanner() {
  return (
    <div style={{
      maxWidth: 1280, margin: "16px auto 0", padding: "0 32px",
    }}>
      <div style={{
        background: "linear-gradient(90deg, #f5f8fd 0%, #ffffff 100%)",
        border: "1px solid #dce4f0", borderRadius: 8,
        padding: "10px 18px",
        display: "flex", alignItems: "center", gap: 16,
        fontSize: 12, fontFamily: "var(--font-sans)",
        position: "relative",
      }}>
        <span style={{
          fontSize: 8, color: "#7886a0", fontWeight: 700,
          letterSpacing: "0.12em", fontFamily: "var(--font-mono)",
          padding: "2px 6px", border: "1px solid #c0cce0", borderRadius: 2,
        }}>AD</span>
        <div style={{ width: 28, height: 28, borderRadius: 4, background: "#0a2a5e", display: "grid", placeItems: "center", color: "#fff", fontSize: 14 }}>⚾</div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <span style={{ fontWeight: 700, color: "#0a0a0a" }}>티빙 KBO 라이브</span>
          <span style={{ color: "#4a5872", marginLeft: 10 }}>전 구단 경기 무광고 시청 · 첫 달 ₩100</span>
        </div>
        <button style={{
          background: "#c8102e", color: "#fff", border: "none", borderRadius: 4,
          padding: "6px 14px", fontSize: 12, fontWeight: 600, cursor: "pointer",
          whiteSpace: "nowrap",
        }}>지금 가입 →</button>
        <button style={{ background: "transparent", border: "none", cursor: "pointer", color: "#9aa5bd", fontSize: 14 }}>✕</button>
      </div>
    </div>
  );
}

/* ───────────── App ───────────── */

function App() {
  const [page, setPage] = useState("home");
  const [selectedGame, setSelectedGame] = useState(1);
  const [favorites, setFavorites] = useState(new Set([1, 4]));
  const [picks, setPicks] = useState({ 4: "home" });
  const [toast, setToast] = useState("");

  const toggleFavorite = (id) => {
    setFavorites(prev => {
      const s = new Set(prev);
      if (s.has(id)) { s.delete(id); setToast("저장에서 제거됨"); }
      else { s.add(id); setToast("저장 완료"); }
      return s;
    });
  };

  const setPick = (gameId, side) => {
    setPicks(prev => {
      const next = { ...prev };
      if (side === null) delete next[gameId];
      else next[gameId] = side;
      return next;
    });
  };

  return (
    <div style={{ minHeight: "100vh", background: "#ffffff", position: "relative" }}>
      {/* KBO top accent band */}
      <div style={{ height: 3, background: "linear-gradient(90deg, #0a2a5e 0%, #0a2a5e 50%, #c8102e 50%, #c8102e 100%)" }} />
      <AdRail side="left" />
      <AdRail side="right" />
      <TopNav page={page} setPage={setPage} favorites={favorites} />
      <TopBanner />
      {page === "home" && (
        <HomePage setPage={setPage} setSelectedGame={setSelectedGame}
          favorites={favorites} toggleFavorite={toggleFavorite}
          picks={picks} setPick={setPick} showToast={setToast} />
      )}
      {page === "game" && (
        <GamePage gameId={selectedGame} setPage={setPage}
          favorites={favorites} toggleFavorite={toggleFavorite}
          picks={picks} setPick={setPick} showToast={setToast} />
      )}
      {page === "stats" && <StatsPage setPage={setPage} />}
      {page === "mypicks" && (
        <MyPicksPage picks={picks} setPick={setPick} setPage={setPage} setSelectedGame={setSelectedGame} />
      )}
      {page === "model" && <ModelPage />}

      <footer style={{
        maxWidth: 1280, margin: "40px auto 0", padding: "24px 32px",
        borderTop: "1px solid #dce4f0", color: "#7886a0", fontSize: 12,
        display: "flex", justifyContent: "space-between",
      }}>
        <span>© 2026 simkbo · KBO 야구 승부예측 AI</span>
        <span style={{ fontFamily: "var(--font-mono)" }}>모델 v1.0 · 데이터 최종 갱신 18:14 KST</span>
      </footer>

      <Toast msg={toast} onClose={() => setToast("")} />
    </div>
  );
}

Object.assign(window, { App, AdRail, AdCard, TopBanner });
