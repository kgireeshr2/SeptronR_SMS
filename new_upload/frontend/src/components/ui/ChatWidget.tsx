/**
 * ChatWidget — School AI Agent (v2)
 *
 * Two modes:
 *   1. Free-text Q&A  → POST /chat/query  (legacy, unchanged)
 *   2. Guided flows   → POST /chat/message (stateful, role-based menus)
 *
 * Guided flows: student attendance, staff attendance, fee, leave, marks, student info.
 * WhatsApp: same flows work via WA numeric menus — the UI renders rich buttons/tables.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import apiClient from '@/api/axios';

// Map page paths → guided flow IDs (sent directly to the backend flow engine)
const PATH_TO_FLOW: Record<string, string> = {
  '/attendance':        'attendance_view',
  '/attendance-today':  'attendance_today',
  '/fees':              'fee',
  '/leaves':            'leave',
  '/exams':             'marks',
  '/students':          'student_details',
  '/accounting':        'accounting',
  '/super-admin':       'sa_schools',
};

// ─── Types ────────────────────────────────────────────────────────────────────

interface StatItem { label: string; value: string; color?: string }
interface StatsCard { type: 'stats'; stats: StatItem[] }
interface TableCard { type: 'table'; title: string; headers: string[]; rows: string[][] }
type Card = StatsCard | TableCard;

interface NavAction { label: string; path: string }

interface BotOption { id: string; label: string; description?: string }

interface AttendanceRow {
  student_id: string;
  name: string;
  roll_number: string;
  default_status: 'present' | 'absent';
}

interface Message {
  id: number;
  role: 'user' | 'bot';
  text: string;
  type?: string;
  cards?: Card[];
  actions?: NavAction[];
  suggestions?: string[];
  options?: BotOption[];
  attendance_rows?: AttendanceRow[];
  breadcrumb?: string;
  session_ended?: boolean;
  ts: Date;
  loading?: boolean;
}

interface ConvMessage { role: string; content: string }
interface Suggestions { data_queries: string[]; how_to: string[] }

const SESSION_KEY = 'sms-chat-session-id';

// ─── Markdown renderer ────────────────────────────────────────────────────────

function Md({ text }: { text: string }) {
  const lines = text.split('\n');
  const els: React.ReactNode[] = [];
  let listBuf: React.ReactNode[] = [];

  function flushList() {
    if (listBuf.length) { els.push(<ul key={els.length} className="my-1 space-y-0.5">{listBuf}</ul>); listBuf = []; }
  }

  lines.forEach((line, i) => {
    const isBullet = /^[•\-\*]\s/.test(line);
    const isNum = /^\d+\.\s/.test(line);

    const styled = line.split(/(\*\*[^*]+\*\*|_[^_]+_)/g).map((p, j) => {
      if (p.startsWith('**') && p.endsWith('**')) return <strong key={j}>{p.slice(2,-2)}</strong>;
      if (p.startsWith('_') && p.endsWith('_')) return <em key={j}>{p.slice(1,-1)}</em>;
      return p;
    });

    if (isBullet || isNum) {
      const content = line.replace(/^[•\-\*\d\.]\s+/, '');
      const cStyled = content.split(/(\*\*[^*]+\*\*)/g).map((p,j) =>
        p.startsWith('**') && p.endsWith('**') ? <strong key={j}>{p.slice(2,-2)}</strong> : p
      );
      listBuf.push(<li key={i} className="flex gap-1.5 text-xs leading-snug"><span className="text-blue-400 flex-shrink-0 mt-0.5">{isNum ? `${listBuf.length+1}.` : '•'}</span><span>{cStyled}</span></li>);
    } else {
      flushList();
      if (!line.trim()) { els.push(<div key={i} className="h-1" />); }
      else { els.push(<span key={i} className="block leading-snug text-xs">{styled}</span>); }
    }
  });
  flushList();
  return <>{els}</>;
}

// ─── Card renderers ───────────────────────────────────────────────────────────

const colorMap: Record<string, string> = {
  green: 'text-emerald-600', red: 'text-red-500', orange: 'text-amber-500',
  blue: 'text-blue-600', gray: 'text-gray-500',
};

function StatsPanel({ card }: { card: StatsCard }) {
  return (
    <div className="grid grid-cols-2 gap-2 my-2">
      {card.stats.map((s, i) => (
        <div key={i} className="bg-white rounded-xl border border-gray-100 px-3 py-2 text-center shadow-sm">
          <div className={`text-base font-bold ${colorMap[s.color || 'blue'] || 'text-blue-600'}`}>{s.value}</div>
          <div className="text-[10px] text-gray-400 mt-0.5 leading-tight">{s.label}</div>
        </div>
      ))}
    </div>
  );
}

function TablePanel({ card }: { card: TableCard }) {
  const [expanded, setExpanded] = useState(card.rows.length <= 6);
  const visible = expanded ? card.rows : card.rows.slice(0, 5);
  return (
    <div className="my-2 rounded-xl overflow-hidden border border-gray-100 shadow-sm">
      <div className="bg-gray-50 px-3 py-1.5 text-[11px] font-semibold text-gray-600 border-b border-gray-100">
        {card.title}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-[11px]">
          <thead>
            <tr className="bg-gray-50">
              {card.headers.map((h, i) => (
                <th key={i} className="px-2.5 py-1.5 text-left text-gray-500 font-medium border-b border-gray-100 whitespace-nowrap">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((row, i) => (
              <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}>
                {row.map((cell, j) => (
                  <td key={j} className="px-2.5 py-1.5 text-gray-700 border-b border-gray-50 whitespace-nowrap">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!expanded && card.rows.length > 5 && (
        <button onClick={() => setExpanded(true)}
          className="w-full py-1.5 text-[10px] text-blue-500 hover:bg-blue-50 transition text-center">
          Show {card.rows.length - 5} more rows ↓
        </button>
      )}
    </div>
  );
}

function Cards({ cards }: { cards: Card[] }) {
  return (
    <>
      {cards.map((card, i) =>
        card.type === 'stats'
          ? <StatsPanel key={i} card={card} />
          : <TablePanel key={i} card={card} />
      )}
    </>
  );
}

// ─── Option Buttons ───────────────────────────────────────────────────────────
function OptionButtons({ options, onSelect }: { options: BotOption[]; onSelect: (id: string, label: string) => void }) {
  return (
    <div className="mt-2 flex flex-col gap-1.5">
      {options.map(opt => (
        <button key={opt.id} onClick={() => onSelect(opt.id, opt.label)}
          className="text-left rounded-xl border border-indigo-100 bg-gradient-to-r from-indigo-50 to-white px-3 py-2 hover:border-indigo-300 hover:bg-indigo-50 transition-all shadow-sm">
          <div className="text-[12px] font-semibold text-indigo-800">{opt.label}</div>
          {opt.description && <div className="text-[10px] text-gray-400 mt-0.5">{opt.description}</div>}
        </button>
      ))}
    </div>
  );
}

// ─── Attendance Table ─────────────────────────────────────────────────────────
interface AttendanceTableProps {
  rows: AttendanceRow[];
  label: string;
  onSave: (payload: { present_ids: string[]; absent_ids: string[] }) => void;
}

function AttendanceTable({ rows, label, onSave }: AttendanceTableProps) {
  const [statuses, setStatuses] = useState<Record<string, 'present' | 'absent'>>(() => {
    const init: Record<string, 'present' | 'absent'> = {};
    rows.forEach(r => { init[r.student_id] = r.default_status; });
    return init;
  });
  const toggle = (id: string) => setStatuses(s => ({ ...s, [id]: s[id]==='present'?'absent':'present' }));
  const markAll = (status: 'present' | 'absent') => setStatuses(() => Object.fromEntries(rows.map(r=>[r.student_id,status])));
  const present_ids = rows.filter(r=>statuses[r.student_id]==='present').map(r=>r.student_id);
  const absent_ids  = rows.filter(r=>statuses[r.student_id]==='absent').map(r=>r.student_id);

  return (
    <div className="mt-2 rounded-xl border border-gray-100 overflow-hidden shadow-sm bg-white">
      <div className="flex items-center justify-between bg-indigo-600 px-3 py-2">
        <span className="text-[11px] font-semibold text-white">{label}</span>
        <div className="flex gap-1">
          <button onClick={()=>markAll('present')} className="text-[10px] px-2 py-0.5 rounded bg-emerald-400 text-white hover:bg-emerald-500">All ✔</button>
          <button onClick={()=>markAll('absent')} className="text-[10px] px-2 py-0.5 rounded bg-red-400 text-white hover:bg-red-500">All ✖</button>
        </div>
      </div>
      <div className="flex gap-4 px-3 py-1.5 bg-gray-50 border-b border-gray-100">
        <span className="text-[11px] text-emerald-600 font-medium">✔ Present: {present_ids.length}</span>
        <span className="text-[11px] text-red-500 font-medium">✖ Absent: {absent_ids.length}</span>
      </div>
      <div className="max-h-52 overflow-y-auto divide-y divide-gray-50">
        {rows.map(r => {
          const isP = statuses[r.student_id]==='present';
          return (
            <button key={r.student_id} onClick={()=>toggle(r.student_id)}
              className={`w-full flex items-center justify-between px-3 py-1.5 hover:bg-gray-50 transition ${isP?'':'bg-red-50'}`}>
              <div className="flex items-center gap-2">
                <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold flex-shrink-0 ${isP?'bg-emerald-100 text-emerald-600':'bg-red-100 text-red-500'}`}>{isP?'✔':'✖'}</span>
                <div className="text-left">
                  <div className="text-[12px] font-medium text-gray-800">{r.name}</div>
                  {r.roll_number && <div className="text-[10px] text-gray-400">Roll #{r.roll_number}</div>}
                </div>
              </div>
              <span className={`text-[10px] font-semibold ${isP?'text-emerald-600':'text-red-500'}`}>{isP?'P':'A'}</span>
            </button>
          );
        })}
      </div>
      <div className="px-3 py-2 bg-gray-50 border-t border-gray-100">
        <button onClick={()=>onSave({present_ids,absent_ids})}
          className="w-full rounded-lg bg-indigo-600 text-white text-[12px] font-semibold py-2 hover:bg-indigo-700 transition">
          💾 Save Attendance
        </button>
      </div>
    </div>
  );
}

// ─── Breadcrumb ───────────────────────────────────────────────────────────────
function Breadcrumb({ text, onMenu }: { text: string; onMenu: () => void }) {
  return (
    <div className="flex items-center gap-1.5 mt-1.5">
      <button onClick={onMenu} className="text-[10px] text-blue-500 hover:text-blue-700 border border-blue-200 rounded-full px-2 py-0.5 hover:bg-blue-50 transition">← Menu</button>
      <span className="text-[10px] text-gray-400">{text}</span>
    </div>
  );
}

// ─── Main Widget ──────────────────────────────────────────────────────────────

const WELCOME_MSG: Message = {
  id: 0, role: 'bot', ts: new Date(), type: 'welcome',
  text: "👋 Hi! I'm your **School Agent**.\n\nAsk me anything or tap **🎯 Guided Actions** for step-by-step workflows:\n• _How many students in class 5?_\n• _Who is absent today?_\n• _Mark class attendance_\n• _Apply for leave_",
  suggestions: ["Total students","Today's attendance","Fee defaulters","🎯 Guided Actions"],
};

const ChatWidget: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [tab, setTab] = useState<'chat' | 'faq'>('chat');
  const [messages, setMessages] = useState<Message[]>([WELCOME_MSG]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<Suggestions | null>(null);
  const [faqList, setFaqList] = useState<{ question: string; answer: string; category: string }[]>([]);
  const [faqOpen, setFaqOpen] = useState<number | null>(null);
  const [faqSearch, setFaqSearch] = useState('');
  const [unread, setUnread] = useState(0);
  // Flow state
  const [sessionId, setSessionId] = useState<string | null>(
    () => sessionStorage.getItem(SESSION_KEY)
  );
  const [flowActive, setFlowActive] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const msgId = useRef(1);

  useEffect(() => {
    if (open && !suggestions) {
      apiClient.get('/chat/suggestions').then((r: any) => setSuggestions(r as Suggestions)).catch(()=>{});
      apiClient.get('/chat/faq').then((r: any) => setFaqList(Array.isArray(r)?r:[])).catch(()=>{});
      setUnread(0);
    }
  }, [open, suggestions]);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, open]);

  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 150);
  }, [open]);

  useEffect(() => {
    if (sessionId) sessionStorage.setItem(SESSION_KEY, sessionId);
    else sessionStorage.removeItem(SESSION_KEY);
  }, [sessionId]);

  const buildHistory = useCallback((): ConvMessage[] =>
    messages.filter(m=>!m.loading&&m.id>0).slice(-10).map(m=>({role:m.role==='user'?'user':'assistant',content:m.text})),
  [messages]);

  // ── Flow message (guided) ─────────────────────────────────────────────────
  const sendFlowMessage = useCallback(async (
    text: string,
    payload?: Record<string, any>,
    displayText?: string,
  ) => {
    if (loading) return;
    const displayMsg = displayText ?? text;
    const userMsg: Message = { id: msgId.current++, role: 'user', text: displayMsg, ts: new Date() };
    const thinkingMsg: Message = { id: msgId.current++, role: 'bot', text: '', ts: new Date(), loading: true };
    setMessages(prev => [...prev, userMsg, thinkingMsg]);
    setLoading(true);
    try {
      const res: any = await apiClient.post('/chat/message', {
        session_id: sessionId,
        message: text,
        payload: payload ?? null,
      });
      if (res.session_id) setSessionId(res.session_id);
      if (res.session_ended) setFlowActive(false);
      const tid = thinkingMsg.id;
      setMessages(prev => prev.map(m => m.id === tid ? {
        ...m, loading: false,
        text: res.text ?? '',
        type: res.type,
        options: res.options ?? [],
        attendance_rows: res.attendance_rows ?? [],
        breadcrumb: res.breadcrumb ?? '',
        session_ended: res.session_ended ?? false,
        cards: res.cards ?? [],
        actions: res.actions ?? [],
        suggestions: res.suggestions ?? [],
      } : m));
      if (!open) setUnread(n=>n+1);
    } catch {
      const tid = thinkingMsg.id;
      setMessages(prev => prev.map(m => m.id === tid ? {
        ...m, loading: false, text: '⚠️ Could not reach the server.', type: 'error',
      } : m));
      setFlowActive(false);
    } finally { setLoading(false); }
  }, [loading, sessionId, open]);

  // ── Free-text message (Q&A) ───────────────────────────────────────────────
  const sendQueryMessage = useCallback(async (text: string) => {
    if (loading) return;
    setInput('');
    const userMsg: Message = { id: msgId.current++, role: 'user', text, ts: new Date() };
    const thinkingMsg: Message = { id: msgId.current++, role: 'bot', text: '', ts: new Date(), loading: true };
    setMessages(prev => [...prev, userMsg, thinkingMsg]);
    setLoading(true);
    const history = buildHistory();
    try {
      const res: any = await apiClient.post('/chat/query', { message: text, history });
      const tid = thinkingMsg.id;
      setMessages(prev => prev.map(m => m.id === tid ? {
        ...m, loading: false,
        text: res.answer ?? 'Sorry, I could not process that.',
        type: res.type, cards: res.cards ?? [], actions: res.actions ?? [], suggestions: res.suggestions ?? [],
      } : m));
      if (!open) setUnread(n=>n+1);
    } catch {
      const tid = thinkingMsg.id;
      setMessages(prev => prev.map(m => m.id === tid ? {
        ...m, loading: false, text: '⚠️ Could not reach the server. Please try again.', type: 'fallback',
      } : m));
    } finally { setLoading(false); }
  }, [loading, buildHistory, open]);

  // ── Main dispatcher ───────────────────────────────────────────────────────
  const sendMessage = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    setInput('');
    const lower = trimmed.toLowerCase();
    // Always intercept guided-flow triggers
    if (
      lower.includes('guided') || lower === '🎯 guided actions' ||
      lower === 'menu' || lower === 'hi' || lower === 'hello' ||
      lower === 'start' || lower === 'help'
    ) {
      setFlowActive(true);
      setSessionId(null); // start fresh session
      sendFlowMessage('hi', undefined, trimmed);
      return;
    }
    if (flowActive) sendFlowMessage(trimmed);
    else sendQueryMessage(trimmed);
  }, [flowActive, sendFlowMessage, sendQueryMessage, setSessionId]);

  const handleOptionSelect = (optId: string, optLabel: string) => {
    setFlowActive(true);
    sendFlowMessage(optId, undefined, optLabel);
  };
  const handleAttendanceSave = (payload: { present_ids: string[]; absent_ids: string[] }) => {
    sendFlowMessage('save', payload, `💾 Saving attendance (${payload.present_ids.length}P, ${payload.absent_ids.length}A)`);
  };
  const handleConfirm = (optId: string, optLabel: string) => sendFlowMessage(optId, undefined, optLabel);
  const handleBackToMenu = () => {
    setFlowActive(false);
    setSessionId(null);
    sendFlowMessage('menu', undefined, '← Back to Menu');
  };

  // Instead of navigating away, open the corresponding guided flow in-chat
  const handleActionClick = (path: string, label: string) => {
    const flowId = PATH_TO_FLOW[path] ?? PATH_TO_FLOW[Object.keys(PATH_TO_FLOW).find(k => path.startsWith(k)) ?? ''];
    if (flowId) {
      setFlowActive(true);
      setSessionId(null); // fresh session for new flow
      sendFlowMessage(flowId, undefined, `📂 ${label}`);
    } else {
      // Fallback: send label as message so bot can still route it
      setFlowActive(true);
      sendFlowMessage(label.toLowerCase(), undefined, `📂 ${label}`);
    }
  };

  const faqCats = [...new Set(faqList.map(f=>f.category))];
  const filteredFaq = faqSearch ? faqList.filter(f=>(f.question+f.answer).toLowerCase().includes(faqSearch.toLowerCase())) : faqList;

  // Helper: is this the last bot message?
  const lastBotMsgId = messages.filter(m=>m.role==='bot'&&!m.loading).slice(-1)[0]?.id;

  return (
    <>
      {/* ── Floating button ────────────────────────────────────────────── */}
      <button
        onClick={()=>{setOpen(o=>!o);setUnread(0);}}
        className={`fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full shadow-xl px-4 py-3 text-white transition-all duration-200 ${open?'bg-slate-700':'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700'}`}
      >
        {open ? (
          <><svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12"/></svg><span className="text-sm font-medium">Close</span></>
        ) : (
          <><div className="relative">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-3 3-3-3z"/></svg>
            {unread>0&&<span className="absolute -top-1.5 -right-1.5 w-4 h-4 bg-red-500 rounded-full text-[10px] flex items-center justify-center font-bold">{unread}</span>}
          </div><span className="text-sm font-medium">AI Assistant</span></>
        )}
      </button>

      {/* ── Chat panel ─────────────────────────────────────────────────── */}
      <div
        className={`fixed bottom-20 right-6 z-50 flex flex-col rounded-2xl shadow-2xl bg-white border border-gray-200 overflow-hidden transition-all duration-300 ${open?'opacity-100 translate-y-0 pointer-events-auto':'opacity-0 translate-y-6 pointer-events-none'}`}
        style={{ width: 400, height: 640 }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-blue-600 to-indigo-700 text-white flex-shrink-0">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-full bg-white/20 flex items-center justify-center text-xl shadow-inner">🎓</div>
            <div>
              <div className="font-semibold text-sm">School AI Agent</div>
              <div className="flex items-center gap-1 mt-0.5">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-[10px] text-blue-100">
                  {flowActive ? '🎯 Guided Mode' : 'Live school data · always available'}
                </span>
              </div>
            </div>
          </div>
          <div className="flex gap-1.5">
            {flowActive && (
              <button onClick={handleBackToMenu}
                className="text-white/70 hover:text-white transition text-xs px-2 py-1 rounded hover:bg-white/10">← Menu</button>
            )}
            <button onClick={()=>setMessages([WELCOME_MSG])}
              className="text-white/60 hover:text-white transition text-xs px-2 py-1 rounded hover:bg-white/10">Clear</button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b flex-shrink-0 bg-gray-50">
          {(['chat','faq'] as const).map(t=>(
            <button key={t} onClick={()=>setTab(t)}
              className={`flex-1 py-2 text-xs font-medium transition-all ${tab===t?'border-b-2 border-blue-600 text-blue-600 bg-white':'text-gray-500 hover:text-gray-700'}`}>
              {t==='chat'?'💬 Chat':'📖 FAQ & Guides'}
            </button>
          ))}
        </div>

        {/* ── CHAT TAB ───────────────────────────────────────────────── */}
        {tab === 'chat' && (
          <>
            <div className="flex-1 overflow-y-auto px-3 py-3 space-y-3 min-h-0 bg-gray-50/60">
              {messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.role==='user'?'justify-end':'justify-start'} items-end gap-2`}>
                  {msg.role==='bot' && (
                    <div className="w-7 h-7 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-sm flex-shrink-0 mb-0.5 shadow-sm">🎓</div>
                  )}
                  <div className="max-w-[90%]">
                    {/* Bubble */}
                    <div className={`rounded-2xl px-3.5 py-2.5 text-sm shadow-sm ${msg.role==='user'?'bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-br-sm':'bg-white text-gray-800 border border-gray-100 rounded-bl-sm'}`}>
                      {msg.loading ? (
                        <div className="flex gap-1 py-0.5">
                          <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{animationDelay:'0ms'}}/>
                          <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{animationDelay:'150ms'}}/>
                          <span className="w-2 h-2 bg-gray-300 rounded-full animate-bounce" style={{animationDelay:'300ms'}}/>
                        </div>
                      ) : msg.role==='bot' ? <Md text={msg.text}/> : <span className="text-sm">{msg.text}</span>}
                    </div>

                    {/* Breadcrumb (only on last bot message) */}
                    {msg.role==='bot' && !msg.loading && msg.breadcrumb && msg.id===lastBotMsgId && (
                      <Breadcrumb text={msg.breadcrumb} onMenu={handleBackToMenu} />
                    )}

                    {/* Option Buttons — only on last bot message */}
                    {msg.role==='bot' && !msg.loading && (msg.options?.length ?? 0) > 0 && msg.id===lastBotMsgId && msg.type!=='confirm' && (
                      <OptionButtons options={msg.options!} onSelect={handleOptionSelect} />
                    )}

                    {/* Attend/Staff Table — only on last bot message */}
                    {msg.role==='bot' && !msg.loading && (msg.attendance_rows?.length ?? 0) > 0 && msg.id===lastBotMsgId && (
                      <AttendanceTable
                        rows={msg.attendance_rows!}
                        label={msg.breadcrumb || 'Attendance'}
                        onSave={handleAttendanceSave}
                      />
                    )}

                    {/* Confirm buttons */}
                    {msg.role==='bot' && !msg.loading && msg.type==='confirm' && (msg.options?.length ?? 0) > 0 && msg.id===lastBotMsgId && (
                      <div className="flex gap-2 mt-2">
                        {msg.options!.map(opt=>(
                          <button key={opt.id} onClick={()=>handleConfirm(opt.id,opt.label)}
                            className={`flex-1 rounded-lg text-[12px] font-semibold py-1.5 transition ${opt.id==='yes'||opt.id==='submit'?'bg-indigo-600 text-white hover:bg-indigo-700':'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Cards (stats / tables) */}
                    {msg.cards && msg.cards.length > 0 && <Cards cards={msg.cards as Card[]} />}

                    {/* In-chat action buttons (no redirect — opens flow inline) */}
                    {msg.actions && msg.actions.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {msg.actions.map((a,i)=>(
                          <button key={i} onClick={()=>handleActionClick(a.path, a.label)}
                            className="inline-flex items-center gap-1 text-[11px] bg-indigo-600 text-white rounded-full px-3 py-1.5 hover:bg-indigo-700 transition shadow-sm font-medium">
                            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                            {a.label}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Suggestion chips */}
                    {msg.role==='bot' && !msg.loading && (msg.suggestions?.length ?? 0) > 0 && !(msg.options?.length) && !(msg.attendance_rows?.length) && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {msg.suggestions!.map((s,i)=>(
                          <button key={i} onClick={()=>sendMessage(s)}
                            className="rounded-full bg-indigo-50 border border-indigo-100 text-indigo-700 text-[11px] px-2.5 py-1 hover:bg-indigo-100 transition">
                            {s}
                          </button>
                        ))}
                      </div>
                    )}

                    {/* Session-ended restart button */}
                    {msg.role==='bot' && !msg.loading && msg.session_ended && msg.id===lastBotMsgId && (
                      <button onClick={()=>sendMessage('menu')}
                        className="mt-2 w-full rounded-xl bg-gradient-to-r from-indigo-50 to-blue-50 border border-indigo-200 text-indigo-700 text-[11px] font-semibold py-1.5 hover:bg-indigo-100 transition">
                        🎯 Start Another Guided Action
                      </button>
                    )}
                  </div>
                </div>
              ))}

              {/* Quick start (first load) */}
              {messages.length <= 1 && suggestions && (
                <div className="px-1 py-1">
                  <p className="text-[10px] text-gray-400 mb-1.5 font-medium">Try asking:</p>
                  <div className="grid grid-cols-2 gap-1.5">
                    {[...suggestions.data_queries.slice(0,3), ...suggestions.how_to.slice(0,1)].map((s,i)=>(
                      <button key={i} onClick={()=>sendMessage(s)}
                        className="text-[11px] text-left rounded-lg bg-white border border-gray-100 text-gray-600 px-2.5 py-2 hover:border-blue-300 hover:text-blue-600 transition shadow-sm">
                        {s}
                      </button>
                    ))}
                  </div>
                  <button onClick={()=>sendMessage('🎯 Guided Actions')}
                    className="mt-2 w-full rounded-xl bg-gradient-to-r from-indigo-600 to-blue-600 text-white text-[12px] font-semibold py-2 hover:from-indigo-700 hover:to-blue-700 transition shadow-sm">
                    🎯 Guided Actions — Attendance, Leave, Fee…
                  </button>
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            {/* Input bar */}
            <div className="flex items-center gap-2 px-3 py-3 border-t bg-white flex-shrink-0">
              {flowActive && (
                <button onClick={handleBackToMenu}
                  className="w-8 h-8 rounded-full border border-gray-200 text-gray-400 hover:text-gray-600 hover:bg-gray-50 flex items-center justify-center transition flex-shrink-0 text-sm">
                  ←
                </button>
              )}
              <input ref={inputRef} value={input}
                onChange={e=>setInput(e.target.value)}
                onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage(input);}}}
                placeholder={flowActive ? "Type your answer…" : "Ask about students, fees, attendance…"}
                className="flex-1 rounded-full border border-gray-200 bg-gray-50 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 focus:bg-white transition"
                disabled={loading}
              />
              <button onClick={()=>sendMessage(input)} disabled={!input.trim()||loading}
                className="w-9 h-9 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 text-white flex items-center justify-center flex-shrink-0 disabled:opacity-40 hover:shadow-lg transition">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8"/>
                </svg>
              </button>
            </div>
          </>
        )}

        {/* ── FAQ TAB ────────────────────────────────────────────────── */}
        {tab === 'faq' && (
          <div className="flex-1 flex flex-col min-h-0">
            <div className="px-3 py-2 border-b bg-white flex-shrink-0">
              <input value={faqSearch} onChange={e=>setFaqSearch(e.target.value)}
                placeholder="Search guides…"
                className="w-full rounded-full border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-300 bg-gray-50"/>
            </div>
            <div className="flex-1 overflow-y-auto px-3 py-2 bg-gray-50/60">
              {faqList.length===0&&<p className="text-center text-gray-400 text-sm py-10">Loading guides…</p>}
              {faqSearch
                ? filteredFaq.map(f=>{const gi=faqList.indexOf(f);return <FaqCard key={gi} faq={f} open={faqOpen===gi} toggle={()=>setFaqOpen(faqOpen===gi?null:gi)} onAsk={()=>{setTab('chat');sendMessage(f.question);}}/>;})
                : faqCats.map(cat=>(
                    <div key={cat} className="mb-3">
                      <div className="flex items-center gap-2 mb-1.5">
                        <div className="h-px flex-1 bg-gray-200"/><span className="text-[10px] font-bold text-blue-600 uppercase tracking-widest">{cat}</span><div className="h-px flex-1 bg-gray-200"/>
                      </div>
                      {faqList.filter(f=>f.category===cat).map(f=>{const gi=faqList.indexOf(f);return <FaqCard key={gi} faq={f} open={faqOpen===gi} toggle={()=>setFaqOpen(faqOpen===gi?null:gi)} onAsk={()=>{setTab('chat');sendMessage(f.question);}}/>;  })}
                    </div>
                  ))
              }
            </div>
          </div>
        )}
      </div>
    </>
  );
};


// ─── FAQ Card ─────────────────────────────────────────────────────────────────

const FaqCard: React.FC<{
  faq: { question: string; answer: string; category: string };
  open: boolean; toggle: () => void; onAsk: () => void;
}> = ({ faq, open, toggle, onAsk }) => (
  <div className="rounded-xl border border-gray-100 bg-white mb-1.5 overflow-hidden shadow-sm hover:shadow-md transition-shadow">
    <button onClick={toggle} className="w-full flex items-center justify-between px-3 py-2.5 text-left hover:bg-gray-50 transition">
      <span className="text-[12px] font-medium text-gray-700 pr-2 leading-snug">{faq.question}</span>
      <svg className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-200 ${open?'rotate-180':''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7"/>
      </svg>
    </button>
    {open && (
      <div className="px-3 pb-3 pt-1 border-t bg-blue-50/40">
        <div className="text-[11px] text-gray-600 leading-relaxed"><Md text={faq.answer}/></div>
        <button onClick={onAsk} className="mt-2 text-[11px] text-blue-500 hover:text-blue-700 font-medium transition">
          💬 Ask in chat →
        </button>
      </div>
    )}
  </div>
);

export default ChatWidget;
