"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { UploadCloud, FileCheck, AlertTriangle, CheckCircle2, XCircle, ShieldAlert, Download, FileText, ArrowRight, RefreshCw, Layers } from "lucide-react";
import confetti from "canvas-confetti";

interface FindingAnalysis {
  status?: string;
  statutory_authority?: string;
  contract_clause?: string;
  legal_analysis?: string;
  citizen_explanation?: string;
  recommended_redline?: string;
  error?: string;
  raw?: string;
}

interface Finding {
  domain: string;
  status: "COMPLIANT" | "NON-COMPLIANT" | "RISK";
  analysis: FindingAnalysis | string;
  statutory_context_used: string;
}

interface AuditResult {
  document_name: string;
  contract_type: string;
  overall_status: "PASSED" | "FAILED";
  violation_count: number;
  findings: Finding[];
  report_url?: string;
  timestamp: string;
}

export default function ContractAuditor() {
  const [file, setFile] = useState<File | null>(null);
  const [contractType, setContractType] = useState("auto");
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditProgress, setAuditProgress] = useState(0);
  const [currentDomainText, setCurrentDomainText] = useState("Initializing statutory vector engine...");
  const [result, setResult] = useState<AuditResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const startAudit = async () => {
    if (!file || isAuditing) return;

    setIsAuditing(true);
    setAuditProgress(15);
    setCurrentDomainText("Parsing document clauses & extracting section titles...");
    setResult(null);
    setError(null);

    // Simulate domain checking progress while API runs
    const interval = setInterval(() => {
      setAuditProgress(prev => {
        if (prev >= 85) return 85;
        const next = prev + 15;
        if (next === 30) setCurrentDomainText("Auditing against BCEA Working Hours & Leave requirements...");
        if (next === 45) setCurrentDomainText("Cross-referencing POPIA Data Privacy & consent clauses...");
        if (next === 60) setCurrentDomainText("Checking CPA Consumer Rights & unfair penalty waivers...");
        if (next === 75) setCurrentDomainText("Auditing LRA Termination & CCMA dispute resolution clauses...");
        return next;
      });
    }, 1800);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("contract_type", contractType);
    formData.append("force_local", "false");

    try {
      const response = await fetch("http://localhost:8000/api/audit", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `Audit failed: ${response.statusText}`);
      }

      const data: AuditResult = await response.json();
      clearInterval(interval);
      setAuditProgress(100);
      setCurrentDomainText("Compliance audit completed!");
      setResult(data);

      if (data.overall_status === "PASSED") {
        confetti({
          particleCount: 100,
          spread: 70,
          origin: { y: 0.6 }
        });
      }
    } catch (err: any) {
      clearInterval(interval);
      setError(`⚠️ **Audit Failure**: ${err.message}. Make sure your backend API server (python api_server.py) is running on port 8000.`);
    } finally {
      setIsAuditing(false);
    }
  };

  return (
    <div className="flex flex-col min-h-[750px] glass-panel rounded-2xl overflow-hidden border border-slate-700/60 shadow-2xl p-8 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <h2 className="text-2xl font-bold text-white flex items-center gap-3">
            <ShieldAlert className="w-7 h-7 text-blue-400" />
            Automated Contract & Compliance Auditor
          </h2>
          <p className="text-slate-400 text-sm mt-1">
            Upload any Employment Contract, Residential Lease, or Consumer Terms (`.pdf`, `.docx`, `.txt`) for instant statutory violation auditing.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-slate-400">Target Law:</span>
          <select
            value={contractType}
            onChange={(e) => setContractType(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-xl px-4 py-2 text-sm text-slate-200 font-medium focus:ring-2 focus:ring-blue-500 cursor-pointer"
          >
            <option value="auto">⚡ Auto-Detect Contract Type</option>
            <option value="employment">🧑‍💼 Employment Contract (BCEA, POPIA, LRA)</option>
            <option value="lease">🏠 Residential Lease Agreement (CPA, POPIA)</option>
            <option value="consumer_terms">🛒 Consumer Terms & Conditions (CPA, POPIA)</option>
          </select>
        </div>
      </div>

      {/* Upload Dropzone */}
      {!result && !isAuditing && (
        <div className="flex flex-col items-center justify-center p-12 border-2 border-dashed border-slate-700 hover:border-blue-500/60 rounded-3xl bg-slate-900/40 transition-all cursor-pointer group relative">
          <input
            type="file"
            accept=".pdf,.docx,.txt"
            onChange={handleFileChange}
            className="absolute inset-0 opacity-0 cursor-pointer z-10"
          />
          <div className="w-20 h-20 rounded-2xl bg-blue-500/10 flex items-center justify-center text-blue-400 group-hover:scale-110 group-hover:bg-blue-500/20 transition-transform mb-4 shadow-lg shadow-blue-500/10">
            <UploadCloud className="w-10 h-10" />
          </div>
          <h3 className="text-lg font-semibold text-slate-200">
            {file ? `Selected File: ${file.name}` : "Drag and drop your contract file here, or browse"}
          </h3>
          <p className="text-sm text-slate-500 mt-2 text-center max-w-md">
            Supports Microsoft Word (.docx), Adobe PDF (.pdf), or plain text (.txt). We extract every clause and check it against mandatory statutory rights.
          </p>

          {file && (
            <motion.button
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              onClick={(e) => {
                e.stopPropagation();
                startAudit();
              }}
              className="mt-6 px-8 py-3.5 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold rounded-2xl flex items-center gap-2 shadow-lg shadow-emerald-500/30 z-20 transition-transform active:scale-95"
            >
              <span>Run Statutory Compliance Audit</span>
              <ArrowRight className="w-5 h-5" />
            </motion.button>
          )}
        </div>
      )}

      {/* Auditing Progress State */}
      {isAuditing && (
        <div className="flex flex-col items-center justify-center p-16 bg-slate-900/60 rounded-3xl border border-slate-800 space-y-6">
          <div className="relative w-24 h-24 flex items-center justify-center">
            <div className="absolute inset-0 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin"></div>
            <FileText className="w-10 h-10 text-blue-400 animate-pulse" />
          </div>

          <div className="text-center space-y-2 max-w-lg">
            <h3 className="text-xl font-bold text-white">Auditing Contract Clauses Against South African Legislation...</h3>
            <p className="text-sm text-blue-300/80 font-mono animate-pulse">{currentDomainText}</p>
          </div>

          <div className="w-full max-w-md bg-slate-800 rounded-full h-3 overflow-hidden shadow-inner border border-slate-700">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${auditProgress}%` }}
              className="bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 h-full transition-all duration-500"
            />
          </div>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-6 bg-red-500/10 border border-red-500/40 rounded-2xl text-red-300 text-sm flex items-center gap-4">
          <AlertTriangle className="w-6 h-6 shrink-0 text-red-400" />
          <div className="flex-1 whitespace-pre-wrap">{error}</div>
          <button
            onClick={() => setError(null)}
            className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 rounded-xl font-semibold transition"
          >
            Try Again
          </button>
        </div>
      )}

      {/* Results View */}
      {result && (
        <AnimatePresence>
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
            {/* Executive Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="p-6 bg-slate-900/80 rounded-2xl border border-slate-800 shadow-md flex flex-col justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase">Document Name</span>
                <span className="text-lg font-bold text-white truncate mt-2">{result.document_name}</span>
              </div>

              <div className="p-6 bg-slate-900/80 rounded-2xl border border-slate-800 shadow-md flex flex-col justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase">Detected Type</span>
                <span className="text-lg font-bold text-blue-400 mt-2">{result.contract_type}</span>
              </div>

              <div className="p-6 bg-slate-900/80 rounded-2xl border border-slate-800 shadow-md flex flex-col justify-between">
                <span className="text-xs font-semibold text-slate-400 uppercase">Statutory Violations</span>
                <span className={`text-2xl font-black mt-1 ${result.violation_count > 0 ? "text-red-400" : "text-emerald-400"}`}>
                  {result.violation_count} {result.violation_count === 1 ? "Violation" : "Violations"} Flagged
                </span>
              </div>

              <div className={`p-6 rounded-2xl border shadow-lg flex flex-col justify-between ${
                result.overall_status === "PASSED"
                  ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                  : "bg-red-500/10 border-red-500/40 text-red-300"
              }`}>
                <span className="text-xs font-bold uppercase">Overall Audit Status</span>
                <div className="flex items-center gap-2 mt-2">
                  {result.overall_status === "PASSED" ? (
                    <CheckCircle2 className="w-8 h-8 text-emerald-400" />
                  ) : (
                    <XCircle className="w-8 h-8 text-red-400" />
                  )}
                  <span className="text-2xl font-black">{result.overall_status}</span>
                </div>
              </div>
            </div>

            {/* Findings List */}
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Layers className="w-5 h-5 text-blue-400" />
                  Detailed Statutory Compliance Findings ({result.findings.length} Domains Audited)
                </h3>
                <button
                  onClick={() => setResult(null)}
                  className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-xl border border-slate-700 flex items-center gap-2 transition"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  Audit Another Contract
                </button>
              </div>

              <div className="space-y-6">
                {result.findings.map((fnd, idx) => (
                  <div
                    key={idx}
                    className={`p-6 rounded-2xl border shadow-xl space-y-4 ${
                      fnd.status === "COMPLIANT"
                        ? "bg-slate-900/90 border-slate-800/80"
                        : fnd.status === "NON-COMPLIANT"
                        ? "bg-slate-900/95 border-red-500/40 shadow-red-500/5"
                        : "bg-slate-900/95 border-amber-500/40 shadow-amber-500/5"
                    }`}
                  >
                    <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-800/80 pb-3">
                      <span className="font-bold text-slate-100 text-base flex items-center gap-2">
                        {fnd.status === "COMPLIANT" && <CheckCircle2 className="w-5 h-5 text-emerald-400" />}
                        {fnd.status === "NON-COMPLIANT" && <XCircle className="w-5 h-5 text-red-400" />}
                        {fnd.status === "RISK" && <AlertTriangle className="w-5 h-5 text-amber-400" />}
                        Domain: {fnd.domain}
                      </span>

                      <span
                        className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${
                          fnd.status === "COMPLIANT"
                            ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30"
                            : fnd.status === "NON-COMPLIANT"
                            ? "bg-red-500/20 text-red-300 border-red-500/30"
                            : "bg-amber-500/20 text-amber-300 border-amber-500/30"
                        }`}
                      >
                        {fnd.status === "NON-COMPLIANT" ? "STATUTORY VIOLATION DETECTED" : fnd.status}
                      </span>
                    </div>

                    {typeof fnd.analysis === "object" && !("error" in fnd.analysis) ? (
                      <div className="flex flex-col gap-4 mt-4">
                        <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/60">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">The Contract Says:</h4>
                          <p className="text-sm text-slate-300 font-serif italic border-l-2 border-slate-600 pl-3">"{fnd.analysis.contract_clause}"</p>
                        </div>
                        
                        <div className="p-4 rounded-xl bg-blue-500/5 border border-blue-500/20">
                          <h4 className="text-xs font-bold uppercase tracking-wider text-blue-400 mb-2 flex items-center gap-2">
                            <ShieldAlert className="w-4 h-4" /> Plain English Explanation
                          </h4>
                          <p className="text-sm text-blue-100 leading-relaxed">{fnd.analysis.citizen_explanation}</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div className="p-4 rounded-xl bg-slate-950/50 border border-slate-800/60">
                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-2">Legal Analysis</h4>
                            <p className="text-xs text-slate-300 leading-relaxed">{fnd.analysis.legal_analysis}</p>
                            <p className="mt-3 text-[11px] font-mono text-slate-500 flex items-center gap-1">
                              <FileCheck className="w-3.5 h-3.5" /> {fnd.analysis.statutory_authority}
                            </p>
                          </div>
                          
                          {fnd.status !== "COMPLIANT" && fnd.analysis.recommended_redline && (
                            <div className="p-4 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                              <h4 className="text-xs font-bold uppercase tracking-wider text-emerald-400 mb-2">Recommended Redline</h4>
                              <p className="text-xs text-emerald-100/90 leading-relaxed whitespace-pre-wrap">{fnd.analysis.recommended_redline}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap bg-slate-950/60 p-4 rounded-xl border border-slate-800/60 font-sans mt-4">
                        {typeof fnd.analysis === "object" ? fnd.analysis.raw || fnd.analysis.error : fnd.analysis}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
