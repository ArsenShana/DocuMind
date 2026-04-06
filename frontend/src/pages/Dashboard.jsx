import { useState, useEffect, useRef } from 'react'
import { Routes, Route, NavLink, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, FileSearch, FileCheck, AlertTriangle, BarChart3,
  FileText, ChevronRight, Loader, CheckCircle2, XCircle,
  Star, Info, ArrowRight
} from 'lucide-react'
import { api } from '../api'

/* ======= UPLOAD PAGE ======= */
function UploadPage() {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [analyzing, setAnalyzing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const fileRef = useRef()
  const navigate = useNavigate()

  const processFile = async (file) => {
    setError(null)
    setResult(null)
    setUploading(true)

    try {
      const upload = await api.upload(file)
      if (upload.error) throw new Error(upload.detail || upload.error)

      setUploading(false)
      setAnalyzing(true)

      const analysis = await api.analyze(upload.document_id)
      setResult(analysis)
    } catch (e) {
      setError(e.message)
    } finally {
      setUploading(false)
      setAnalyzing(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    if (e.dataTransfer.files[0]) processFile(e.dataTransfer.files[0])
  }

  const handleFileSelect = (e) => {
    if (e.target.files[0]) processFile(e.target.files[0])
  }

  const confColor = (v) => v >= 0.8 ? 'var(--success)' : v >= 0.5 ? 'var(--warning)' : 'var(--danger)'

  return (
    <div>
      <div className="dash-header">
        <h1>Upload & Analyze</h1>
        <p>Upload a document to classify, extract data, and generate AI summary.</p>
      </div>

      <motion.div
        className={`upload-zone ${dragging ? 'dragover' : ''}`}
        onClick={() => fileRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
      >
        <input ref={fileRef} type="file" accept=".pdf,.png,.jpg,.jpeg" onChange={handleFileSelect} />
        <div className="upload-zone-icon">
          {uploading ? <Loader size={28} className="spinner" /> :
           analyzing ? <FileSearch size={28} /> :
           <Upload size={28} />}
        </div>
        <h3>{uploading ? 'Uploading...' : analyzing ? 'Analyzing with AI...' : 'Drop document here'}</h3>
        <p>{uploading || analyzing ? 'Please wait, this may take a few seconds' : 'PDF, PNG, JPG up to 20MB'}</p>
      </motion.div>

      {error && (
        <motion.div className="result-card" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} style={{ borderColor: 'var(--danger)', marginTop: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--danger)' }}>
            <XCircle size={20} /> {error}
          </div>
        </motion.div>
      )}

      <AnimatePresence>
        {result && (
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} style={{ marginTop: 24 }}>
            {/* Classification */}
            <div className="result-card">
              <div className="result-card-header">
                <h3><FileSearch size={18} color="var(--accent)" /> Classification</h3>
                <span className="tag tag-accent">{result.classification.document_type}</span>
              </div>
              <div className="confidence-bar">
                <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>Confidence</span>
                <div className="confidence-track">
                  <div className="confidence-fill" style={{
                    width: `${result.classification.confidence * 100}%`,
                    background: confColor(result.classification.confidence),
                  }} />
                </div>
                <span className="confidence-label" style={{ color: confColor(result.classification.confidence) }}>
                  {(result.classification.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 8 }}>{result.classification.reasoning}</p>
            </div>

            {/* Extraction */}
            <div className="result-card">
              <div className="result-card-header">
                <h3><FileCheck size={18} color="var(--success)" /> Extracted Data</h3>
                <div className="confidence-bar" style={{ width: 150 }}>
                  <div className="confidence-track">
                    <div className="confidence-fill" style={{
                      width: `${result.extraction.overall_confidence * 100}%`,
                      background: confColor(result.extraction.overall_confidence),
                    }} />
                  </div>
                  <span className="confidence-label" style={{ color: confColor(result.extraction.overall_confidence) }}>
                    {(result.extraction.overall_confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div className="result-grid">
                {Object.entries(result.extraction.extracted_data || {}).map(([key, val]) => {
                  if (!val || key === 'line_items' || key === 'items' || key === 'key_terms' || key === 'obligations') return null
                  let display = val
                  if (typeof val === 'object' && val.value !== undefined) display = `$${val.value.toFixed(2)} ${val.currency || ''}`
                  if (Array.isArray(val)) display = val.join(', ')
                  if (typeof display === 'object') return null
                  return (
                    <div key={key} className="result-field">
                      <div className="label">{key.replace(/_/g, ' ')}</div>
                      <div className="value">{String(display)}</div>
                    </div>
                  )
                })}
              </div>

              {/* Line items */}
              {(result.extraction.extracted_data?.line_items || result.extraction.extracted_data?.items || []).length > 0 && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: 8 }}>Line Items</div>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                      <thead>
                        <tr>
                          {Object.keys((result.extraction.extracted_data?.line_items || result.extraction.extracted_data?.items)[0] || {}).map(h => (
                            <th key={h} style={{ padding: '8px 12px', textAlign: 'left', borderBottom: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {(result.extraction.extracted_data?.line_items || result.extraction.extracted_data?.items).map((item, i) => (
                          <tr key={i}>
                            {Object.values(item).map((v, j) => (
                              <td key={j} style={{ padding: '8px 12px', borderBottom: '1px solid var(--border)' }}>
                                {typeof v === 'number' && v > 1 ? `$${v.toFixed(2)}` : String(v)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {/* Summary */}
            <div className="result-card">
              <div className="result-card-header">
                <h3><BarChart3 size={18} color="var(--accent-2)" /> AI Summary</h3>
                <span className={`tag tag-${result.summary.risk_level === 'critical' ? 'danger' : result.summary.risk_level === 'warning' ? 'warning' : 'success'}`}>
                  {result.summary.risk_level} risk
                </span>
              </div>
              <p style={{ fontSize: 15, lineHeight: 1.7, marginBottom: 16 }}>{result.summary.summary}</p>

              {result.summary.key_findings.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>KEY FINDINGS</div>
                  {result.summary.key_findings.map((f, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'start', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                      <CheckCircle2 size={14} color="var(--success)" style={{ marginTop: 2, flexShrink: 0 }} /> {f}
                    </div>
                  ))}
                </div>
              )}

              {result.summary.issues_found.length > 0 && (
                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginBottom: 6 }}>ISSUES FOUND</div>
                  {result.summary.issues_found.map((f, i) => (
                    <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'start', marginBottom: 4, fontSize: 13, color: 'var(--text-secondary)' }}>
                      <AlertTriangle size={14} color="var(--warning)" style={{ marginTop: 2, flexShrink: 0 }} /> {f}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

/* ======= VALIDATE PAGE ======= */
function ValidatePage() {
  const [docs, setDocs] = useState([])
  const [selected, setSelected] = useState([])
  const [validating, setValidating] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => { api.listDocuments().then(setDocs).catch(console.error) }, [])

  const toggle = (id) => {
    setSelected(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id])
  }

  const runValidation = async () => {
    setError(null)
    setResult(null)
    setValidating(true)
    try {
      const r = await api.validate(selected)
      setResult(r)
    } catch (e) { setError(e.message) }
    finally { setValidating(false) }
  }

  const riskColor = (score) => score >= 0.7 ? 'var(--danger)' : score >= 0.3 ? 'var(--warning)' : 'var(--success)'

  return (
    <div>
      <div className="dash-header">
        <h1>Cross-Validation</h1>
        <p>Select 2 or more analyzed documents to find discrepancies.</p>
      </div>

      {docs.filter(d => d.analyzed).length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-secondary)' }}>
          <AlertTriangle size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <p>No analyzed documents yet. Upload and analyze documents first.</p>
        </div>
      ) : (
        <>
          <div style={{ marginBottom: 20 }}>
            {docs.filter(d => d.analyzed).map(d => (
              <motion.div
                key={d.document_id}
                className="doc-item"
                onClick={() => toggle(d.document_id)}
                style={{ borderColor: selected.includes(d.document_id) ? 'var(--accent)' : undefined }}
                whileTap={{ scale: 0.98 }}
              >
                <div className={`doc-icon ${selected.includes(d.document_id) ? 'invoice' : 'unknown'}`}>
                  {selected.includes(d.document_id) ? <CheckCircle2 size={20} /> : <FileText size={20} />}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600 }}>{d.filename}</div>
                  <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ID: {d.document_id}</div>
                </div>
              </motion.div>
            ))}
          </div>

          <motion.button
            className="btn btn-primary"
            onClick={runValidation}
            disabled={selected.length < 2 || validating}
            whileTap={{ scale: 0.97 }}
          >
            {validating ? <><Loader size={16} className="spinner" /> Validating...</> : <>
              <AlertTriangle size={16} /> Validate {selected.length} Documents
            </>}
          </motion.button>

          {error && <div style={{ color: 'var(--danger)', marginTop: 12 }}>{error}</div>}

          <AnimatePresence>
            {result && (
              <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} style={{ marginTop: 24 }}>
                {/* Summary */}
                <div className="result-card">
                  <div className="result-card-header">
                    <h3>
                      {result.is_valid ?
                        <><CheckCircle2 size={18} color="var(--success)" /> Valid</> :
                        <><XCircle size={18} color="var(--danger)" /> Issues Found</>
                      }
                    </h3>
                    <div className="risk-meter">
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Risk</span>
                      <div className="risk-bar">
                        <div className="risk-fill" style={{ width: `${result.risk_score * 100}%`, background: riskColor(result.risk_score) }} />
                      </div>
                      <span style={{ fontSize: 14, fontWeight: 700, color: riskColor(result.risk_score) }}>
                        {(result.risk_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  <p style={{ fontSize: 14, color: 'var(--text-secondary)', lineHeight: 1.7 }}>{result.summary}</p>
                  <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-muted)' }}>
                    {result.documents_analyzed} documents analyzed &mdash; {result.discrepancies.length} discrepancies found
                  </div>
                </div>

                {/* Discrepancies */}
                {result.discrepancies.map((d, i) => (
                  <motion.div
                    key={i}
                    className={`discrepancy-card ${d.severity}`}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.08 }}
                  >
                    <div className="discrepancy-header">
                      <h4>{d.type.replace(/_/g, ' ')}</h4>
                      <span className={`tag tag-${d.severity === 'critical' ? 'danger' : d.severity === 'warning' ? 'warning' : 'accent'}`}>
                        {d.severity}
                      </span>
                    </div>
                    <div className="discrepancy-body">{d.description}</div>
                    <div className="discrepancy-values">
                      <div className="discrepancy-val">
                        <div className="label">Doc: {d.document_a.slice(0,8)}</div>
                        <div>{d.value_a}</div>
                      </div>
                      <div className="discrepancy-val">
                        <div className="label">Doc: {d.document_b.slice(0,8)}</div>
                        <div>{d.value_b}</div>
                      </div>
                    </div>
                    {d.suggestion && (
                      <div style={{ marginTop: 8, fontSize: 12, color: 'var(--accent)', display: 'flex', gap: 4, alignItems: 'center' }}>
                        <Info size={12} /> {d.suggestion}
                      </div>
                    )}
                  </motion.div>
                ))}
              </motion.div>
            )}
          </AnimatePresence>
        </>
      )}
    </div>
  )
}

/* ======= DOCUMENTS PAGE ======= */
function DocumentsPage() {
  const [docs, setDocs] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.listDocuments().then(setDocs).catch(console.error).finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-page"><div className="spinner spinner-lg" /></div>

  return (
    <div>
      <div className="dash-header">
        <h1>Documents</h1>
        <p>{docs.length} documents uploaded</p>
      </div>

      {docs.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: 'var(--text-secondary)' }}>
          <FileText size={40} style={{ margin: '0 auto 12px', opacity: 0.3 }} />
          <p>No documents yet. Upload one from the Analyze page.</p>
        </div>
      ) : (
        docs.map((d, i) => (
          <motion.div
            key={d.document_id}
            className="doc-item"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <div className={`doc-icon ${d.analyzed ? 'invoice' : 'unknown'}`}>
              <FileText size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 600 }}>{d.filename}</div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>ID: {d.document_id}</div>
            </div>
            <span className={`tag ${d.analyzed ? 'tag-success' : 'tag-warning'}`}>
              {d.analyzed ? 'Analyzed' : 'Pending'}
            </span>
          </motion.div>
        ))
      )}
    </div>
  )
}

/* ======= DASHBOARD LAYOUT ======= */
export default function Dashboard() {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
      <div className="dash-layout">
        <div className="dash-sidebar">
          <div className="dash-sidebar-title">Dashboard</div>
          <NavLink to="/dashboard" end><Upload size={18} /> Upload & Analyze</NavLink>
          <NavLink to="/dashboard/validate"><AlertTriangle size={18} /> Cross-Validate</NavLink>
          <NavLink to="/dashboard/documents"><FileText size={18} /> Documents</NavLink>
          <a href="/api/docs" target="_blank" rel="noreferrer"><FileSearch size={18} /> API Docs</a>
        </div>
        <div className="dash-content">
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/validate" element={<ValidatePage />} />
            <Route path="/documents" element={<DocumentsPage />} />
          </Routes>
        </div>
      </div>
    </motion.div>
  )
}
