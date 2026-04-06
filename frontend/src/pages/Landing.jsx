import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight, Zap, Shield, FileSearch, Brain, FileCheck,
  BarChart3, AlertTriangle, Layers, Upload, ScanSearch, CheckCircle2
} from 'lucide-react'

const fadeUp = (delay = 0) => ({
  initial: { opacity: 0, y: 40 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay, ease: [0.25, 0.46, 0.45, 0.94] },
})

const fadeIn = (delay = 0) => ({
  initial: { opacity: 0 },
  whileInView: { opacity: 1 },
  viewport: { once: true },
  transition: { duration: 0.6, delay },
})

export default function Landing() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      {/* Hero */}
      <section className="hero">
        <div className="hero-bg">
          <div className="hero-orb hero-orb-1" />
          <div className="hero-orb hero-orb-2" />
          <div className="hero-orb hero-orb-3" />
        </div>
        <motion.div className="hero-content" {...fadeUp()}>
          <div className="hero-badge"><Zap size={14} /> AI-Powered Document Intelligence</div>
          <h1>
            Analyze Documents<br />
            with <span className="gradient-text">AI Precision</span>
          </h1>
          <p>
            Upload invoices, receipts, and contracts. DocuMind classifies, extracts structured data,
            validates across documents, and generates actionable insights — all powered by GPT.
          </p>
          <div className="hero-actions">
            <Link to="/dashboard" className="btn btn-primary btn-lg">
              Get Started <ArrowRight size={18} />
            </Link>
            <a href="#features" className="btn btn-outline btn-lg">
              Learn More
            </a>
          </div>
        </motion.div>
      </section>

      {/* Features */}
      <section className="section" id="features">
        <div className="container">
          <motion.div className="section-header" {...fadeIn()}>
            <div className="section-label">Features</div>
            <h2>Everything You Need for<br />Document Intelligence</h2>
            <p>From classification to cross-document validation — a complete AI-powered pipeline.</p>
          </motion.div>

          <div className="features-grid">
            {[
              { icon: <FileSearch size={24} />, title: 'Smart Classification', desc: 'Automatically detects document type — invoice, receipt, or contract — with confidence scoring.' },
              { icon: <Brain size={24} />, title: 'Data Extraction', desc: 'Pulls structured data: dates, amounts, parties, line items. Every field has a confidence score.' },
              { icon: <AlertTriangle size={24} />, title: 'Cross-Validation', desc: 'Hybrid engine (rules + LLM) detects amount mismatches, date inconsistencies, missing fields.' },
              { icon: <BarChart3 size={24} />, title: 'AI Summaries', desc: 'Concise overview of each document with key findings, issues found, and risk assessment.' },
              { icon: <Shield size={24} />, title: 'Confidence Scoring', desc: 'Every extracted value includes a 0-1 confidence score so you know what to trust.' },
              { icon: <Layers size={24} />, title: 'Structured JSON', desc: 'All outputs are strictly typed with Pydantic schemas — ready for integration.' },
            ].map((f, i) => (
              <motion.div
                key={i}
                className="feature-card"
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1, duration: 0.5 }}
              >
                <div className="feature-icon">{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="section" style={{ background: 'var(--bg-card)' }}>
        <div className="container">
          <motion.div className="section-header" {...fadeIn()}>
            <div className="section-label">How It Works</div>
            <h2>Four Steps to Insight</h2>
            <p>Upload a document and let the AI pipeline do the rest.</p>
          </motion.div>

          <div className="steps-grid">
            {[
              { num: '1', icon: <Upload size={20} />, title: 'Upload', desc: 'PDF, PNG, or JPG document' },
              { num: '2', icon: <ScanSearch size={20} />, title: 'Classify & Extract', desc: 'AI identifies type and pulls data' },
              { num: '3', icon: <AlertTriangle size={20} />, title: 'Validate', desc: 'Cross-check against other documents' },
              { num: '4', icon: <CheckCircle2 size={20} />, title: 'Results', desc: 'Structured data + risk assessment' },
            ].map((s, i) => (
              <motion.div
                key={i}
                className="step-card"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.15 }}
              >
                <div className="step-number">{s.num}</div>
                <h3>{s.title}</h3>
                <p>{s.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Pipeline Demo */}
      <section className="section">
        <div className="container">
          <motion.div className="section-header" {...fadeIn()}>
            <div className="section-label">Pipeline</div>
            <h2>Under the Hood</h2>
            <p>A hybrid approach combining LLM intelligence with deterministic rule-based validation.</p>
          </motion.div>

          <motion.div className="pipeline-demo" {...fadeIn(0.2)}>
            {[
              { color: 'var(--accent)', label: 'Document Parser', desc: 'PyMuPDF extracts raw text from PDF/images' },
              { color: 'var(--accent-2)', label: 'LLM Classifier', desc: 'GPT identifies: invoice / receipt / contract' },
              { color: 'var(--success)', label: 'Data Extractor', desc: 'Structured JSON with confidence scores' },
              { color: 'var(--warning)', label: 'Rule Engine', desc: 'Deterministic checks: math, dates, entities' },
              { color: '#ec4899', label: 'LLM Validator', desc: 'Semantic analysis for complex discrepancies' },
              { color: 'var(--accent)', label: 'Report Generator', desc: 'Summary, findings, risk level' },
            ].map((step, i) => (
              <div key={i}>
                <div className="pipeline-step">
                  <div className="pipeline-dot" style={{ background: step.color }} />
                  <div>
                    <div className="pipeline-step-label">{step.label}</div>
                    <div className="pipeline-step-desc">{step.desc}</div>
                  </div>
                </div>
                {i < 5 && <div className="pipeline-line" />}
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="section">
        <div className="container">
          <motion.div
            style={{
              textAlign: 'center',
              padding: '80px 40px',
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius)',
              border: '1px solid var(--border)',
              position: 'relative',
              overflow: 'hidden',
            }}
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <div style={{ position: 'absolute', width: 400, height: 400, background: 'radial-gradient(circle, var(--accent-glow), transparent 70%)', top: '-50%', right: '-10%', pointerEvents: 'none' }} />
            <div style={{ position: 'absolute', width: 300, height: 300, background: 'radial-gradient(circle, var(--accent-2-glow), transparent 70%)', bottom: '-30%', left: '-5%', pointerEvents: 'none' }} />
            <h2 style={{ fontSize: 36, fontWeight: 800, marginBottom: 16, position: 'relative', letterSpacing: -1 }}>
              Ready to Analyze?
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: 32, fontSize: 18, position: 'relative' }}>
              Upload your first document and see the AI pipeline in action.
            </p>
            <Link to="/dashboard" className="btn btn-primary btn-lg" style={{ position: 'relative' }}>
              Open Dashboard <ArrowRight size={18} />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="footer">
        <div className="container">
          DocuMind AI &copy; {new Date().getFullYear()} &mdash; Intelligent Document Analysis
        </div>
      </footer>
    </motion.div>
  )
}
