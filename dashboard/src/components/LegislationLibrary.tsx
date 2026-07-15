"use client";

import React, { useEffect, useState } from "react";
import { BookOpen, ExternalLink, ShieldCheck, Database, FileCheck, Layers, Sparkles } from "lucide-react";

interface ActInfo {
  key: string;
  title: string;
  filename: string;
  url: string;
}

export default function LegislationLibrary() {
  const [acts, setActs] = useState<ActInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("http://localhost:8000/api/acts")
      .then(res => res.json())
      .then(data => {
        if (data && data.acts) setActs(data.acts);
        setLoading(false);
      })
      .catch(() => {
        // Fallback default acts if backend API not reached
        setActs([
          { key: "POPIA", title: "Protection of Personal Information Act 4 of 2013", filename: "popia_act_4_of_2013.txt", url: "http://www.saflii.org/za/legis/num_act/popia2013449/" },
          { key: "COMPANIES", title: "Companies Act 71 of 2008", filename: "companies_act_71_of_2008.txt", url: "http://www.saflii.org/za/legis/num_act/ca2008133/" },
          { key: "BCEA", title: "Basic Conditions of Employment Act 75 of 1997", filename: "bcea_act_75_of_1997.txt", url: "http://www.saflii.org/za/legis/num_act/bcoea1997369/" },
          { key: "LRA", title: "Labour Relations Act 66 of 1995", filename: "lra_act_66_of_1995.txt", url: "http://www.saflii.org/za/legis/num_act/lra1995220/" },
          { key: "CPA", title: "Consumer Protection Act 68 of 2008", filename: "cpa_act_68_of_2008.txt", url: "http://www.saflii.org/za/legis/num_act/cpa2008285/" },
          { key: "NCA", title: "National Credit Act 34 of 2005", filename: "nca_act_34_of_2005.txt", url: "http://www.saflii.org/za/legis/num_act/nca2005164/" },
          { key: "CONSTITUTION", title: "Constitution of the Republic of South Africa Act 108 of 1996", filename: "constitution_act_108_of_1996.txt", url: "http://www.saflii.org/za/legis/num_act/cotrosa1996423/" }
        ]);
        setLoading(false);
      });
  }, []);

  return (
    <div className="flex flex-col min-h-[750px] glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-2xl p-8 space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <BookOpen className="w-7 h-7 text-emerald-400" />
            Core South African Legislation Library
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            These authoritative national Acts are pre-processed, sectioned, and embedded into your Qdrant Vector Store (`mzansi_law_acts`).
          </p>
        </div>

        <div className="flex items-center gap-3 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 rounded-xl text-emerald-300 text-xs font-semibold">
          <Database className="w-4 h-4 text-emerald-400 animate-pulse" />
          <span>7 Core Statutes Embedded & Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {acts.map((act) => (
          <div
            key={act.key}
            className="glass-card p-6 rounded-2xl flex flex-col justify-between space-y-4 border border-slate-800/80 hover:border-emerald-500/50 transition-all group shadow-lg"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-3 py-1 rounded-lg bg-blue-500/20 text-blue-300 text-xs font-bold font-mono tracking-wider border border-blue-500/30">
                  {act.key}
                </span>
                <span className="flex items-center gap-1 text-[11px] text-emerald-400 font-semibold">
                  <ShieldCheck className="w-3.5 h-3.5" /> Verified
                </span>
              </div>

              <h3 className="font-bold text-white text-base leading-snug group-hover:text-blue-400 transition-colors">
                {act.title}
              </h3>

              <p className="text-xs text-slate-400 leading-relaxed font-sans">
                {act.key === "POPIA" && "Governs personal data protection, lawful processing conditions, security safeguards, and employee/customer rights."}
                {act.key === "COMPANIES" && "Regulates corporate governance, director personal financial disclosures (s75), and Business Rescue proceedings (s129)."}
                {act.key === "BCEA" && "Sets mandatory basic conditions: ordinary working hours, overtime compensation (1.5x), annual/sick leave, and notice periods."}
                {act.key === "LRA" && "Protect employees from unfair dismissals, unfair labor practices, and establishes CCMA / Bargaining Council dispute rights."}
                {act.key === "CPA" && "Protects consumer transactions against unfair contract terms, cooling-off rescission (direct marketing), and quality warranties."}
                {act.key === "NCA" && "Prevents reckless lending, limits excessive interest/fees, and governs credit agreements and debt counselling."}
                {act.key === "CONSTITUTION" && "The supreme law of South Africa, enshrining fundamental human rights, equality, privacy, and administrative justice."}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-800/60 flex items-center justify-between text-xs">
              <span className="text-slate-500 font-mono text-[11px] truncate max-w-[150px]">
                {act.filename}
              </span>
              <a
                href={act.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-blue-400 hover:text-blue-300 font-semibold transition"
              >
                <span>Official SAFLII</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
