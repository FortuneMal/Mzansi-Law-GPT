"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Send, Bot, User, BookOpen, ShieldCheck, Sparkles, AlertCircle, ChevronDown, ChevronUp, FileText } from "lucide-react";

interface Source {
  act: string;
  section: string;
  content: string;
  source_file: string;
}

interface Message {
  id: string;
  sender: "user" | "bot";
  text: string;
  sources?: Source[];
  timestamp: string;
}

const PRESET_QUESTIONS = [
  "Can my employer force me to work 60 hours a week without overtime pay under the BCEA?",
  "What are my statutory rights under POPIA if a company sells my personal data without consent?",
  "What mandatory rules must a company follow when initiating Business Rescue under Section 129?",
  "Is a residential lease clause legal if it forfeits 100% of my deposit upon early cancellation under the CPA?"
];

const ACT_FILTERS = [
  "All Acts",
  "Basic Conditions of Employment Act",
  "Protection of Personal Information Act",
  "Companies Act",
  "Labour Relations Act",
  "Consumer Protection Act",
  "National Credit Act"
];

export default function ChatConsultant() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: "welcome",
      sender: "bot",
      text: "Sawubona! Welcome to **Mzansi Law GPT**, your state-of-the-art South African AI Legal Consultant.\n\nI am grounded strictly in official statutory legislation from **SAFLII** and your **Qdrant Cloud vector database**. Ask me any question about South African employment law, data privacy, corporate governance, or consumer rights below!",
      timestamp: "Just now"
    }
  ]);
  const [inputQuery, setInputQuery] = useState("");
  const [selectedFilter, setSelectedFilter] = useState("All Acts");
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const toggleSource = (msgId: string) => {
    setExpandedSources(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const handleSend = async (queryText?: string) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInputQuery("");
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: textToSend,
          act_filter: selectedFilter,
          collection_name: "mzansi_law_acts",
          force_local: false
        })
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.statusText}`);
      }

      const data = await response.json();
      const botMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "bot",
        text: data.answer,
        sources: data.sources,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err: any) {
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        sender: "bot",
        text: `⚠️ **Connection Error**: Could not connect to the Mzansi Law API (` + err.message + `). Make sure your backend server (` + `python api_server.py` + `) is running on port 8000.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
      };
      setMessages(prev => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[750px] glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-2xl">
      {/* Top Bar with Filters */}
      <div className="px-6 py-4 bg-slate-900/80 border-b border-slate-700/60 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-blue-500/20 rounded-lg text-blue-400">
            <Sparkles className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-100 text-lg flex items-center gap-2">
              Statutory RAG Consultant
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-normal border border-emerald-500/30">
                Grounded in Qdrant Vector Store
              </span>
            </h3>
            <p className="text-xs text-slate-400">Ask complex legal scenarios & receive authoritative citations</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400 font-medium">Filter Legislation:</span>
          <select
            value={selectedFilter}
            onChange={(e) => setSelectedFilter(e.target.value)}
            className="bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-1.5 text-sm text-slate-200 focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer shadow-sm"
          >
            {ACT_FILTERS.map(filter => (
              <option key={filter} value={filter}>{filter}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Preset Questions Bar */}
      <div className="px-6 py-2.5 bg-slate-950/40 border-b border-slate-800/80 overflow-x-auto flex items-center gap-2 scrollbar-none">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">Try Query:</span>
        {PRESET_QUESTIONS.map((q, i) => (
          <button
            key={i}
            onClick={() => handleSend(q)}
            disabled={isLoading}
            className="text-xs bg-slate-800/60 hover:bg-slate-700/80 text-slate-300 px-3 py-1 rounded-full border border-slate-700/50 transition whitespace-nowrap hover:border-blue-500/40"
          >
            {q.length > 50 ? q.substring(0, 50) + "..." : q}
          </button>
        ))}
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <motion.div
            key={msg.id}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className={`flex gap-4 ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
          >
            {msg.sender === "bot" && (
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center text-white shrink-0 shadow-lg shadow-blue-500/20">
                <Bot className="w-6 h-6" />
              </div>
            )}

            <div className={`max-w-[80%] space-y-3 ${msg.sender === "user" ? "order-1" : "order-2"}`}>
              <div className="flex items-center gap-2 px-1">
                <span className="text-xs font-medium text-slate-400">
                  {msg.sender === "user" ? "You (Citizen / Legal Officer)" : "Mzansi Law GPT Assistant"}
                </span>
                <span className="text-[10px] text-slate-500">{msg.timestamp}</span>
              </div>

              <div
                className={`p-5 rounded-2xl shadow-md leading-relaxed text-sm ${
                  msg.sender === "user"
                    ? "bg-gradient-to-r from-blue-600 to-blue-700 text-white rounded-tr-none"
                    : "bg-slate-800/90 border border-slate-700/60 text-slate-200 rounded-tl-none whitespace-pre-wrap"
                }`}
              >
                {msg.text}
              </div>

              {/* Statutory Sources Citations Drawer */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="bg-slate-900/80 border border-slate-700/60 rounded-xl overflow-hidden shadow-inner">
                  <button
                    onClick={() => toggleSource(msg.id)}
                    className="w-full px-4 py-2.5 bg-slate-800/60 hover:bg-slate-800 flex items-center justify-between text-xs font-semibold text-blue-400 transition"
                  >
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-emerald-400" />
                      <span>Retrieved Statutory Grounding ({msg.sources.length} Sections Cited)</span>
                    </div>
                    {expandedSources[msg.id] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>

                  <AnimatePresence>
                    {expandedSources[msg.id] && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="p-4 space-y-3 divide-y divide-slate-800 text-xs"
                      >
                        {msg.sources.map((src, idx) => (
                          <div key={idx} className="pt-3 first:pt-0 space-y-1">
                            <div className="flex items-center justify-between">
                              <span className="font-bold text-emerald-400 flex items-center gap-1.5">
                                <FileText className="w-3.5 h-3.5" />
                                {src.act}
                              </span>
                              <span className="px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 font-mono text-[11px] border border-blue-500/20">
                                Section {src.section}
                              </span>
                            </div>
                            <p className="text-slate-300 bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80 italic line-clamp-4 hover:line-clamp-none transition-all">
                              "{src.content}"
                            </p>
                          </div>
                        ))}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              )}
            </div>

            {msg.sender === "user" && (
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-700 flex items-center justify-center text-white shrink-0 order-2 shadow-lg shadow-emerald-500/20">
                <User className="w-6 h-6" />
              </div>
            )}
          </motion.div>
        ))}

        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4 items-center">
            <div className="w-10 h-10 rounded-xl bg-blue-600/30 flex items-center justify-center text-blue-400 animate-pulse">
              <Bot className="w-6 h-6" />
            </div>
            <div className="p-4 bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-none flex items-center gap-3 text-sm text-slate-300">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                <span className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></span>
              </div>
              Searching South African Acts & generating legal guidance...
            </div>
          </motion.div>
        )}
      </div>

      {/* Input Bar */}
      <div className="p-4 bg-slate-900/90 border-t border-slate-700/60">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex items-center gap-3 relative"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            placeholder={`Ask a legal question (e.g. "What rights do I have during business rescue under ${selectedFilter}?")`}
            disabled={isLoading}
            className="flex-1 bg-slate-950/80 border border-slate-700/80 rounded-2xl px-5 py-3.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition shadow-inner"
          />
          <button
            type="submit"
            disabled={isLoading || !inputQuery.trim()}
            className="px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 disabled:opacity-40 text-white font-semibold rounded-2xl flex items-center gap-2 shadow-lg shadow-blue-500/25 transition-all transform active:scale-95"
          >
            <span>Consult</span>
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
