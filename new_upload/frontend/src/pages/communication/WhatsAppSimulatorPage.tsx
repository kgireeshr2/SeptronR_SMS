/**
 * WhatsApp Chat Simulator
 * ─────────────────────────
 * Lets you test the WhatsApp / FlowEngine bot from the browser.
 * Calls POST /chat/whatsapp/test (no Meta credentials needed).
 *
 * Shows:
 *  - Config status panel (whether Meta credentials are set)
 *  - Send real test message to any phone (requires Meta credentials)
 *  - WhatsApp-style chat bubbles
 *  - Option buttons (mirrors WA interactive list/buttons)
 *  - Interactive attendance marking with present/absent toggles
 *  - Expandable "WA Payloads" panel so you see exactly what Meta would receive
 */
import React, { useState, useRef, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import apiClient from '@/api/axios';

const unwrap = (r: any) => r?.data ?? r;

// ─── Types ────────────────────────────────────────────────────────────────────

interface Option { id: string; label: string; description?: string }
interface AttRow { student_id: string; name: string; roll_number: string; default_status: string }
interface StatItem { label: string; value: string; color?: string }
interface Card { type: string; title?: string; headers?: string[]; rows?: string[][]; stats?: StatItem[] }
interface NavAction { label: string; path: string }

interface BotMsg {
  text: string;
  options: Option[];
  attendance_rows: AttRow[];
  cards: Card[];
  actions: NavAction[];
  suggestions: string[];
  breadcrumb: string;
  session_ended: boolean;
  wa_payloads: object[];
}

interface ChatBubble {
  id: number;
  from: 'user' | 'bot';
  text: string;
  botData?: BotMsg;
  ts: Date;
}

// ─── Attendance Widget ────────────────────────────────────────────────────────

interface AttendanceWidgetProps {
  rows: AttRow[];
  onSave: (presentIds: string[], absentIds: string[]) => void;
  disabled: boolean;
}

const AttendanceWidget: React.FC<AttendanceWidgetProps> = ({ rows, onSave, disabled }) => {
  const [absentSet, setAbsentSet] = useState<Set<string>>(new Set());

  const toggle = (studentId: string) => {
    setAbsentSet(prev => {
      const next = new Set(prev);
      next.has(studentId) ? next.delete(studentId) : next.add(studentId);
      return next;
    });
  };

  const handleSave = () => {
    const absentIds = rows.filter(r => absentSet.has(r.student_id)).map(r => r.student_id);
    const presentIds = rows.filter(r => !absentSet.has(r.student_id)).map(r => r.student_id);
    onSave(presentIds, absentIds);
  };

  const presentCount = rows.length - absentSet.size;

  return (
    <div className="mt-2 bg-gray-50 rounded p-2 text-xs space-y-1">
      <p className="font-semibold text-gray-600 mb-1">
        Tap a student to toggle absent — <span className="text-green-600">{presentCount} present</span> / <span className="text-red-500">{absentSet.size} absent</span>
      </p>
      <div className="max-h-56 overflow-y-auto space-y-0.5">
        {rows.map((r, i) => {
          const isAbsent = absentSet.has(r.student_id);
          return (
            <button
              key={r.student_id}
              onClick={() => toggle(r.student_id)}
              disabled={disabled}
              className={`flex items-center gap-2 w-full text-left rounded px-2 py-1 transition ${
                isAbsent
                  ? 'bg-red-100 text-red-700 line-through'
                  : 'bg-green-50 text-gray-700 hover:bg-green-100'
              }`}
            >
              <span className="w-5 text-right text-gray-400">{i + 1}.</span>
              <span className={`flex-1 ${isAbsent ? 'line-through' : ''}`}>{r.name}</span>
              {r.roll_number && <span className="text-gray-400">#{r.roll_number}</span>}
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                isAbsent ? 'bg-red-200 text-red-700' : 'bg-green-200 text-green-700'
              }`}>
                {isAbsent ? 'A' : 'P'}
              </span>
            </button>
          );
        })}
      </div>
      <button
        onClick={handleSave}
        disabled={disabled}
        className="mt-2 w-full bg-[#075E54] hover:bg-[#064e46] text-white text-xs font-semibold py-1.5 rounded-lg transition disabled:opacity-50"
      >
        ✔ Save Attendance ({presentCount}P / {absentSet.size}A)
      </button>
    </div>
  );
};

// ─── Config Panel ────────────────────────────────────────────────────────────

interface ConfigStatus {
  token_configured: boolean;
  phone_id_configured: boolean;
  verify_token: string;
  webhook_url: string;
  api_version: string;
  ready_for_real_wa: boolean;
}

const ConfigPanel: React.FC = () => {
  const [open, setOpen] = useState(false);
  const [phone, setPhone] = useState('');
  const [testMsg, setTestMsg] = useState('Hello from SeptroSchool! This is a test message. 👋');
  const [sendResult, setSendResult] = useState<string | null>(null);
  const [verifyResult, setVerifyResult] = useState<any>(null);

  const configQ = useQuery<ConfigStatus>({
    queryKey: ['wa-config-status'],
    queryFn: async () => unwrap(await apiClient.get('/chat/whatsapp/config-status')),
    staleTime: 60_000,
  });
  const cfg = configQ.data;

  const sendMutation = useMutation({
    mutationFn: () => apiClient.post('/chat/whatsapp/send-test-message', { phone: phone.replace(/\D/g, ''), message: testMsg }),
    onSuccess: (r: any) => setSendResult(`✅ Sent! Message ID: ${unwrap(r)?.meta_response?.messages?.[0]?.id ?? 'ok'}`),
    onError: (e: any) => setSendResult(`❌ ${e?.response?.data?.detail ?? e?.message}`),
  });

  const verifyMutation = useMutation({
    mutationFn: () => apiClient.get('/chat/whatsapp/verify-test'),
    onSuccess: (r: any) => setVerifyResult(unwrap(r)),
    onError: (e: any) => setVerifyResult({ status: `❌ ${e?.response?.data?.detail ?? e?.message}` }),
  });

  const dot = (ok: boolean) => ok
    ? <span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-1.5" />
    : <span className="inline-block w-2 h-2 rounded-full bg-red-400 mr-1.5" />;

  return (
    <div className="bg-white border-b border-gray-200 dark:bg-gray-900 dark:border-gray-700">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between px-4 py-2 text-xs text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
      >
        <span className="flex items-center gap-2">
          {cfg ? (cfg.ready_for_real_wa
            ? <span className="flex items-center text-green-600 font-semibold">{dot(true)} Meta API Connected</span>
            : <span className="flex items-center text-amber-600 font-semibold">{dot(false)} Meta API Not Configured (Simulator only)</span>)
            : '⚙️ WhatsApp Configuration'}
        </span>
        <span>{open ? '▲' : '▼'} Config</span>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 space-y-4 text-sm">
          {/* Status */}
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="rounded-lg border border-gray-100 dark:border-gray-700 p-3 space-y-1.5">
              <p className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Credential Status</p>
              <p>{dot(!!cfg?.token_configured)} <span className="text-gray-600 dark:text-gray-400">META_WHATSAPP_TOKEN</span> — {cfg?.token_configured ? '✔ Set' : 'Not set in .env'}</p>
              <p>{dot(!!cfg?.phone_id_configured)} <span className="text-gray-600 dark:text-gray-400">META_PHONE_NUMBER_ID</span> — {cfg?.phone_id_configured ? '✔ Set' : 'Not set in .env'}</p>
            </div>
            <div className="rounded-lg border border-gray-100 dark:border-gray-700 p-3 space-y-1.5">
              <p className="font-semibold text-gray-700 dark:text-gray-300 mb-2">Webhook Setup (paste into Meta)</p>
              <p className="text-gray-500 dark:text-gray-400">Callback URL:</p>
              <code className="block bg-gray-900 text-green-400 text-[10px] rounded px-2 py-1 break-all select-all">{cfg?.webhook_url ?? '...'}</code>
              <p className="text-gray-500 dark:text-gray-400 mt-1.5">Verify Token (copy this exact value):</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 bg-gray-900 text-yellow-300 text-[11px] font-bold rounded px-2 py-1 select-all">{cfg?.verify_token ?? '...'}</code>
                <button
                  onClick={() => navigator.clipboard.writeText(cfg?.verify_token ?? '')}
                  className="text-[10px] bg-gray-700 text-white px-2 py-1 rounded hover:bg-gray-600"
                >Copy</button>
              </div>
            </div>
          </div>

          {/* Verify test button */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-2">
            <p className="font-semibold text-gray-700 dark:text-gray-300 text-xs">Test Webhook Verification</p>
            <p className="text-xs text-gray-500">Click to simulate exactly what Meta sends when you click "Verify & Save" in Meta Business Suite.</p>
            <div className="flex items-center gap-3 flex-wrap">
              <button
                onClick={() => { setVerifyResult(null); verifyMutation.mutate(); }}
                disabled={verifyMutation.isPending}
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs px-4 py-1.5 rounded-lg transition disabled:opacity-50"
              >
                {verifyMutation.isPending ? 'Testing…' : '🔗 Test Verification Now'}
              </button>
              {verifyResult && (
                <span className={`text-xs font-medium ${verifyResult.status?.startsWith('✅') ? 'text-green-600' : 'text-red-500'}`}>
                  {verifyResult.status}
                </span>
              )}
            </div>
            {verifyResult && !verifyResult.status?.startsWith('✅') && (
              <pre className="bg-gray-900 text-red-300 text-[10px] rounded p-2 overflow-auto max-h-24">{JSON.stringify(verifyResult, null, 2)}</pre>
            )}
          </div>

          {/* Setup instructions (if not ready) */}
          {cfg && !cfg.ready_for_real_wa && (
            <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 text-xs text-blue-800 dark:text-blue-300 space-y-1">
              <p className="font-semibold">To enable real WhatsApp messaging:</p>
              <ol className="list-decimal list-inside space-y-0.5 ml-1">
                <li>Go to <strong>developers.facebook.com → Your App → WhatsApp → API Setup</strong></li>
                <li>Copy the <strong>Temporary / Permanent Access Token</strong> and <strong>Phone Number ID</strong></li>
                <li>Add to <code className="bg-blue-100 dark:bg-blue-800 px-1 rounded">backend/.env</code>:</li>
              </ol>
              <pre className="bg-gray-900 text-green-300 text-[10px] rounded p-2 mt-1 select-all">{`META_WHATSAPP_TOKEN=your_token_here\nMETA_PHONE_NUMBER_ID=your_phone_number_id\nMETA_WHATSAPP_VERIFY_TOKEN=sms_whatsapp_verify`}</pre>
              <li className="list-none mt-1">4. In Meta Developer Console → WhatsApp → Configuration → Webhook, paste the <strong>Callback URL</strong> and <strong>Verify Token</strong> above, then click <strong>"Verify and Save"</strong></li>
              <li className="list-none">5. Subscribe to the <strong>messages</strong> webhook field</li>
              <li className="list-none">6. Restart the backend — the btn above will confirm it works</li>
            </div>
          )}

          {/* Send real test message */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-3 space-y-2">
            <p className="font-semibold text-gray-700 dark:text-gray-300 text-xs">Send Real WhatsApp Message</p>
            {!cfg?.ready_for_real_wa && (
              <p className="text-xs text-amber-600 dark:text-amber-400">⚠️ Requires Meta credentials configured above</p>
            )}
            <div className="flex gap-2">
              <input
                className="flex-1 rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 px-3 py-1.5 text-xs focus:outline-none focus:border-green-500"
                placeholder="Phone: 919876543210 (no +, full international)"
                value={phone}
                onChange={e => setPhone(e.target.value)}
              />
            </div>
            <textarea
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 dark:bg-gray-800 px-3 py-1.5 text-xs focus:outline-none focus:border-green-500 resize-none"
              rows={2}
              value={testMsg}
              onChange={e => setTestMsg(e.target.value)}
            />
            <div className="flex items-center gap-3">
              <button
                onClick={() => { setSendResult(null); sendMutation.mutate(); }}
                disabled={sendMutation.isPending || !phone.trim() || !cfg?.ready_for_real_wa}
                className="bg-[#075E54] hover:bg-[#064e46] text-white text-xs px-4 py-1.5 rounded-lg transition disabled:opacity-50"
              >
                {sendMutation.isPending ? 'Sending…' : '📤 Send to WhatsApp'}
              </button>
              {sendResult && <span className="text-xs">{sendResult}</span>}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// ─── Component ────────────────────────────────────────────────────────────────

const WhatsAppSimulatorPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatBubble[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPayloads, setShowPayloads] = useState<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  // Track which attendance bubble has been saved (to disable re-submission)
  const [savedAttendanceBubbles, setSavedAttendanceBubbles] = useState<Set<number>>(new Set());

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (
    messageId: string,         // value sent to API
    reset = false,
    displayText?: string,      // text shown in user bubble (defaults to messageId)
    payload?: Record<string, any>,
  ) => {
    if (!messageId.trim() || loading) return;
    const bubbleText = displayText ?? messageId;
    const userBubble: ChatBubble = { id: Date.now(), from: 'user', text: bubbleText, ts: new Date() };
    setMessages(prev => [...prev, userBubble]);
    setInput('');
    setLoading(true);

    try {
      const resp: any = await apiClient.post('/chat/whatsapp/test', {
        message: messageId,
        reset_session: reset,
        ...(payload ? { payload } : {}),
      });
      const data: BotMsg = resp?.data ?? resp;
      const botBubble: ChatBubble = {
        id: Date.now() + 1,
        from: 'bot',
        text: data.text,
        botData: data,
        ts: new Date(),
      };
      setMessages(prev => [...prev, botBubble]);
    } catch (err: any) {
      const errMsg = err?.response?.data?.detail || err?.message || 'Error';
      setMessages(prev => [
        ...prev,
        { id: Date.now() + 1, from: 'bot', text: `⚠️ ${errMsg}`, ts: new Date() },
      ]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  };

  const handleReset = () => {
    setMessages([]);
    setSavedAttendanceBubbles(new Set());
    sendMessage('hi', true);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(input); }
  };

  const handleSaveAttendance = (bubbleId: number, presentIds: string[], absentIds: string[]) => {
    setSavedAttendanceBubbles(prev => new Set(prev).add(bubbleId));
    sendMessage(
      'save',
      false,
      `✔ Saved: ${presentIds.length}P / ${absentIds.length}A`,
      { present_ids: presentIds, absent_ids: absentIds },
    );
  };

  const fmt = (d: Date) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="flex flex-col h-full bg-[#ECE5DD] min-h-screen">
      {/* Header */}
      <div className="bg-[#075E54] text-white flex items-center gap-3 px-4 py-3 shadow-md">
        <div className="w-10 h-10 rounded-full bg-[#25D366] flex items-center justify-center text-xl font-bold">
          📱
        </div>
        <div className="flex-1">
          <div className="font-semibold text-sm">School Assistant</div>
          <div className="text-xs text-green-200">WhatsApp Bot Simulator</div>
        </div>
        <button
          onClick={handleReset}
          className="text-xs bg-[#128C7E] hover:bg-[#0e7068] px-3 py-1.5 rounded-full transition"
          title="Start new conversation"
        >
          🔄 New Chat
        </button>
      </div>

      {/* Config Panel */}
      <ConfigPanel />

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-2">
        {messages.length === 0 && (
          <div className="flex justify-center">
            <div className="bg-[#FFF3CD] text-yellow-800 text-xs px-4 py-2 rounded-lg shadow text-center max-w-xs">
              Type <strong>hi</strong> or click <strong>New Chat</strong> to start the bot flow.
              <br />Uses the same logic as real WhatsApp — no credentials needed.
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.from === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-xl shadow px-3 py-2 ${
              msg.from === 'user'
                ? 'bg-[#DCF8C6] text-gray-800 rounded-br-none'
                : 'bg-white text-gray-800 rounded-bl-none'
            }`}>
              {/* Main text */}
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>

              {/* Breadcrumb */}
              {msg.botData?.breadcrumb && (
                <p className="text-[10px] text-gray-400 mt-0.5 italic">{msg.botData.breadcrumb}</p>
              )}

              {/* Attendance list — interactive widget */}
              {msg.botData && msg.botData.attendance_rows.length > 0 && (
                <AttendanceWidget
                  rows={msg.botData.attendance_rows}
                  onSave={(pIds, aIds) => handleSaveAttendance(msg.id, pIds, aIds)}
                  disabled={loading || savedAttendanceBubbles.has(msg.id)}
                />
              )}

              {/* Data cards */}
              {msg.botData && msg.botData.cards.map((card, ci) => (
                <div key={ci} className="mt-2 bg-gray-50 rounded p-2 text-xs">
                  {card.type === 'stats' && card.stats && (
                    <div className="flex flex-wrap gap-2">
                      {card.stats.map((s, si) => (
                        <div key={si} className="bg-white rounded px-2 py-1 shadow-sm text-center min-w-[60px]">
                          <div className="font-bold text-sm">{s.value}</div>
                          <div className="text-gray-500">{s.label}</div>
                        </div>
                      ))}
                    </div>
                  )}
                  {card.type === 'table' && card.headers && (
                    <div className="overflow-x-auto">
                      <p className="font-semibold mb-1">{card.title}</p>
                      <table className="w-full text-left border-collapse">
                        <thead>
                          <tr>{card.headers.map(h => <th key={h} className="pr-2 text-gray-500 pb-1">{h}</th>)}</tr>
                        </thead>
                        <tbody>
                          {(card.rows || []).slice(0, 10).map((row, ri) => (
                            <tr key={ri} className="border-t border-gray-100">
                              {row.map((cell, ci2) => <td key={ci2} className="pr-2 py-0.5">{cell}</td>)}
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              ))}

              {/* Options (mirrors WA interactive list/buttons) */}
              {msg.botData && msg.botData.options.length > 0 && (
                <div className="mt-2 space-y-1">
                  {msg.botData.options.map(opt => (
                    <button
                      key={opt.id}
                      onClick={() => sendMessage(opt.id, false, opt.label)}
                      disabled={loading}
                      className="block w-full text-left text-sm bg-[#E7F3FF] hover:bg-[#cce5ff] text-[#075E54] font-medium px-3 py-1.5 rounded-lg border border-[#b8daff] transition disabled:opacity-50"
                    >
                      {opt.label}
                      {opt.description && <span className="block text-xs text-gray-500 font-normal">{opt.description}</span>}
                    </button>
                  ))}
                </div>
              )}

              {/* Session ended suggestions */}
              {msg.botData?.session_ended && msg.botData.suggestions.length > 0 && (
                <div className="mt-2 space-y-1">
                  <p className="text-xs text-gray-500">Quick start:</p>
                  {msg.botData.suggestions.map((s, si) => (
                    <button
                      key={si}
                      onClick={() => sendMessage(s)}
                      className="block w-full text-left text-xs bg-gray-100 hover:bg-gray-200 px-2 py-1 rounded transition"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}

              {/* Timestamp + WA payload toggle */}
              <div className="flex items-center justify-between mt-1">
                <span className="text-[10px] text-gray-400">{fmt(msg.ts)}</span>
                {msg.botData && msg.botData.wa_payloads.length > 0 && (
                  <button
                    onClick={() => setShowPayloads(prev => prev === msg.id ? null : msg.id)}
                    className="text-[10px] text-blue-400 hover:text-blue-600 ml-2"
                  >
                    {showPayloads === msg.id ? '▲ hide WA payload' : '▼ WA payload'}
                  </button>
                )}
              </div>

              {/* WA API Payloads panel */}
              {showPayloads === msg.id && msg.botData && (
                <div className="mt-1 bg-gray-900 text-green-300 text-[10px] rounded p-2 overflow-auto max-h-60 font-mono">
                  {msg.botData.wa_payloads.map((p, pi) => (
                    <div key={pi} className="mb-1 border-b border-gray-700 pb-1">
                      <span className="text-yellow-400 text-[9px]">Message {pi + 1}</span>
                      <pre className="whitespace-pre-wrap break-all">{JSON.stringify(p, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-xl rounded-bl-none shadow px-4 py-2 text-gray-400 text-sm italic">
              typing…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="bg-[#F0F0F0] border-t border-gray-300 px-3 py-2 flex items-center gap-2">
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message…"
          disabled={loading}
          className="flex-1 bg-white rounded-full px-4 py-2 text-sm outline-none border border-gray-200 focus:border-[#25D366] disabled:opacity-50"
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={loading || !input.trim()}
          className="w-10 h-10 bg-[#075E54] hover:bg-[#064e46] disabled:opacity-40 text-white rounded-full flex items-center justify-center transition"
        >
          ➤
        </button>
      </div>
    </div>
  );
};

export default WhatsAppSimulatorPage;
