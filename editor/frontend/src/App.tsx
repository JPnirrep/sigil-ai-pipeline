/* KLEIA-UP Book Editor — Application */

import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from './api';
import { Book, StyleOverrides, BookMetadata } from './types';
import RichEditor from './components/RichEditor';
import StylePanel from './components/StylePanel';
import ProjectSetupDialog from './components/ProjectSetupDialog';

interface ImportResult { book: Book; metadata: BookMetadata; session: string; }
interface TemplateItem { name: string; filename: string; size_str: string; }

const DEFAULT_STYLE: StyleOverrides = {
  body_font: "Georgia, 'Times New Roman', serif",
  body_size: '11pt',
  body_line_height: '1.5',
  body_alignment: 'justify',
  body_margin_bottom: '0.3em',
  body_color: '#333333',
  h1_font: "Georgia, 'Times New Roman', serif",
  h1_size: '24pt',
  h1_weight: 'bold',
  h1_align: 'left',
  h1_color: '#1f2937',
  h1_margin_top: '2em',
  h1_margin_bottom: '0.5em',
  h2_font: "Georgia, 'Times New Roman', serif",
  h2_size: '18pt',
  h2_weight: 'bold',
  h2_align: 'left',
  h2_color: '#374151',
  h2_margin_top: '1.5em',
  h2_margin_bottom: '0.3em',
  h3_font: "Georgia, 'Times New Roman', serif",
  h3_size: '14pt',
  h3_weight: 'bold',
  h3_align: 'left',
  h3_color: '#555555',
  image_max_width: '100%',
  image_align: 'center',
};

type Toast = { id: number; msg: string; type: 'info' | 'error' | 'success' };
let tid = 0;

function fmtTime(iso: string) {
  if (!iso) return '';
  const d = new Date(iso);
  const min = Math.floor((Date.now() - d.getTime()) / 60000);
  if (min < 1) return 'à l\'instant';
  if (min < 60) return `il y a ${min} min`;
  const h = Math.floor(min / 60);
  if (h < 24) return `il y a ${h}h`;
  return d.toLocaleDateString('fr-FR');
}

export default function App() {
  const [book, setBook] = useState<Book | null>(null);
  const [style, setStyle] = useState<StyleOverrides>(DEFAULT_STYLE);
  const [meta, setMeta] = useState<BookMetadata | null>(null);
  const [activeChId, setActiveChId] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [saving, setSaving] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showSetup, setShowSetup] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [bookTitle, setBookTitle] = useState('');
  const [bookAuthor, setBookAuthor] = useState('');
  const previewIframe = useRef<HTMLIFrameElement>(null);
  const st = useRef<number | null>(null);

  const toast = useCallback((msg: string, type: Toast['type'] = 'info') => {
    const id = ++tid;
    setToasts((p) => [...p.slice(-4), { id, msg, type }]);
    setTimeout(() => setToasts((p) => p.filter((t) => t.id !== id)), 4000);
  }, []);

  const activeCh = book?.chapters.find((c) => c.id === activeChId) ?? book?.chapters[0] ?? null;

  // Init
  useEffect(() => {
    api.templates().then((d) => setTemplates(d.templates)).catch(() => {});
    api.health().then((h: { status: string; has_book: boolean }) => {
      if (h.has_book) {
        api.getBook().then((d: any) => {
          setBook(d.book);
          setStyle(d.style);
          setMeta(d.metadata);
          setBookTitle(d.book.title || '');
          setBookAuthor(d.book.author || '');
          setActiveChId(d.book.chapters[0]?.id ?? null);
          toast('Session restaurée', 'success');
        }).catch(() => {});
      }
    }).catch(() => {});
  }, []);

  const debouncedSave = useCallback((fn: () => void, ms = 500) => {
    if (st.current) clearTimeout(st.current);
    st.current = window.setTimeout(fn, ms);
  }, []);

  const chCount = activeCh ? activeCh.content_html.replace(/<[^>]+>/g, '').split(/\s+/).filter(Boolean).length : 0;

  const updateBookMeta = (t: string, a: string) => {
    setBookTitle(t);
    setBookAuthor(a);
    setBook((prev) => prev ? { ...prev, title: t, author: a } : prev);
  };

  // ── Handlers ──

  const handleImport = () => {
    const inp = document.createElement('input');
    inp.type = 'file';
    inp.accept = '.docx';
    inp.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      try {
        setSaving(true);
        const data = await api.importDocx(file) as ImportResult;
        setBook(data.book);
        setStyle(DEFAULT_STYLE);
        setMeta(data.metadata);
        setSessionId(data.session);
        setBookTitle(data.book.title || '');
        setBookAuthor(data.book.author || '');
        setActiveChId(data.book.chapters[0]?.id ?? null);
        toast(`« ${file.name} » importé (${data.book.chapters.length} chapitres)`, 'success');
      } catch (err) {
        toast(`Import échoué: ${err}`, 'error');
      }
      setSaving(false);
    };
    inp.click();
  };

  const handleNewBook = () => {
    setBook({
      id: Date.now().toString(16),
      title: '',
      subtitle: '',
      author: '',
      front_matter_html: '',
      chapters: [
        { id: '1', title: 'Chapitre 1', content_html: '<p>Commencez à écrire…</p>' },
        { id: '2', title: 'Chapitre 2', content_html: '<p></p>' },
        { id: '3', title: 'Chapitre 3', content_html: '<p></p>' },
      ],
      trim_width: 6, trim_height: 9,
      margin_top: 0.6, margin_bottom: 0.7, margin_inner: 0.8, margin_outer: 0.5, bleed: 0,
    });
    setStyle(DEFAULT_STYLE);
    setMeta({ word_count: 0, chapter_count: 3, parsed_at: new Date().toISOString(), source_file: '', genre_detected: 'default' });
    setActiveChId('1');
    setBookTitle('');
    setBookAuthor('');
    setShowSetup(true);
  };

  const handleSetupSave = async (title: string, author: string, coverFile?: File) => {
    setBookTitle(title);
    setBookAuthor(author);
    setBook((prev) => prev ? { ...prev, title, author } : prev);
    setShowSetup(false);

    // Save to backend
    try {
      await fetch('/api/book/meta', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, subtitle: '', author }),
      });
      if (coverFile) {
        const form = new FormData();
        form.append('file', coverFile);
        await fetch('/api/book/cover', { method: 'POST', body: form });
      }
      toast('Projet enregistré', 'success');
    } catch (err) {
      toast(`Erreur: ${err}`, 'error');
    }
  };

  const handleChUpdate = (chId: string, title: string, html: string) => {
    if (!book) return;
    setSaving(true);
    setBook((prev) => prev ? {
      ...prev,
      chapters: prev.chapters.map((c) => c.id === chId ? { ...c, title, content_html: html } : c),
    } : prev);
    api.updateChapter(chId, title, html)
      .then(() => setSaving(false))
      .catch(() => { setSaving(false); toast('Erreur de sauvegarde', 'error'); });
  };

  const handleAddCh = async () => {
    if (!book) return;
    const title = prompt('Titre du chapitre :') || 'Nouveau chapitre';
    try {
      const data = await api.addChapter(title, activeChId);
      setBook((prev) => {
        if (!prev) return prev;
        const i = prev.chapters.findIndex((c) => c.id === activeChId);
        const chs = [...prev.chapters];
        chs.splice(i + 1, 0, data.chapter);
        return { ...prev, chapters: chs };
      });
      setActiveChId(data.chapter.id);
    } catch (err) { toast(`Erreur: ${err}`, 'error'); }
  };

  const handleDelCh = async () => {
    if (!book || !activeCh || book.chapters.length <= 1) return;
    if (!confirm(`Supprimer « ${activeCh.title} » ?`)) return;
    try {
      await api.deleteChapter(activeChId!);
      setBook((prev) => prev ? { ...prev, chapters: prev.chapters.filter((c) => c.id !== activeChId) } : prev);
      setActiveChId(book.chapters.find((c) => c.id !== activeChId)?.id ?? null);
    } catch (err) { toast(`Erreur: ${err}`, 'error'); }
  };

  const handleStyleChange = (s: StyleOverrides) => {
    setStyle(s);
    debouncedSave(() => api.updateStyle(s).catch(() => toast('Erreur style', 'error')), 400);
  };

  const handleExport = (fmt: 'epub' | 'pdf') => {
    fetch(`/api/export/${fmt}`, { method: 'POST' })
      .then((r) => { if (!r.ok) throw new Error(r.statusText); return r.blob(); })
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${bookTitle || 'livre'}.${fmt}`;
        a.click();
        URL.revokeObjectURL(url);
        toast(`Exporté en ${fmt.toUpperCase()}`, 'success');
      })
      .catch((err) => toast(`Export échoué: ${err}`, 'error'));
  };

  const openPreview = () => {
    setShowPreview(true);
    setTimeout(() => {
      if (previewIframe.current)
        previewIframe.current.src = `/api/preview?t=${Date.now()}`;
    }, 100);
  };

  // ── Render ──

  return (
    <div className="app-shell">
      {/* Toast container */}
      <div className="toast-container">
        {toasts.map((t) => <div key={t.id} className={`toast ${t.type}`}>{t.msg}</div>)}
      </div>

      {/* Header */}
      <header className="app-header">
        <span className="brand">KLEIA-UP</span>
        {book ? (
          <>
            <input className="book-title-input" type="text"
              placeholder="Titre du livre"
              value={bookTitle}
              onChange={(e) => updateBookMeta(e.target.value, bookAuthor)}
              onBlur={() => { if (book) setBook({ ...book, title: bookTitle, author: bookAuthor }); }} />
            <span className="spacer" />
            <button className="header-btn" onClick={openPreview}>👁 Aperçu</button>
            <button className="header-btn icon" onClick={() => handleExport('epub')} title="Exporter en EPUB">📖</button>
            <button className="header-btn icon" onClick={() => handleExport('pdf')} title="Exporter en PDF">📄</button>
          </>
        ) : (
          <>
            <span className="spacer" />
            <button className="header-btn primary" onClick={handleImport}>📂 Importer un DOCX</button>
          </>
        )}
      </header>

      {/* Main */}
      {!book ? (
        <div className="landing">
          <div className="landing-icon">📖</div>
          <h1>KLEIA-UP Book Editor</h1>
          <p>Créez et mettez en page votre livre prêt pour l'impression et le format numérique.</p>

          <div className="landing-actions">
            <div className="landing-btn" onClick={handleNewBook}>
              <span className="icon">📄</span>
              <span className="label">Nouveau livre</span>
              <span className="desc">Partez d'une page blanche</span>
            </div>
            <div className="landing-btn" onClick={handleImport}>
              <span className="icon">📂</span>
              <span className="label">Importer un DOCX</span>
              <span className="desc">Fichier KDP ou manuscrit</span>
            </div>
          </div>

          {templates.length > 0 && (
            <>
              <div className="landing-section-title">Modèles KDP</div>
              <div className="template-grid">
                {templates.map((t) => (
                  <a key={t.filename} className="template-card" href={`/api/templates/${t.filename}`}>
                    <span className="name">{t.name.replace(/[A-Z]/g, (c) => ' ' + c).trim()}</span>
                    <span className="desc">Format papier Amazon</span>
                    <span className="size">{t.size_str}</span>
                  </a>
                ))}
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="workspace">
          {/* Sidebar */}
          <aside className="sidebar">
            <div className="sidebar-header">
              <span>Chapitres</span>
              <div style={{ display: 'flex', gap: 4 }}>
                <button className="btn-icon" onClick={handleAddCh} title="Ajouter un chapitre">+</button>
                <button className="btn-icon" onClick={handleDelCh} title="Supprimer"
                  disabled={book.chapters.length <= 1}>−</button>
              </div>
            </div>
            <div className="chapter-list">
              {book.chapters.map((ch, i) => (
                <div key={ch.id}
                  className={`chapter-item${ch.id === activeChId ? ' active' : ''}`}
                  onClick={() => setActiveChId(ch.id)}>
                  <span className="num">{i + 1}.</span>
                  <span>{ch.title || '(sans titre)'}</span>
                </div>
              ))}
            </div>
          </aside>

          {/* Editor */}
          <main className="main-area">
            {activeCh ? (
              <RichEditor
                key={activeCh.id}
                content={activeCh.content_html}
                chapterTitle={activeCh.title}
                style={style}
                onUpdate={(html) => handleChUpdate(activeCh.id, activeCh.title, html)}
                onTitleUpdate={(title) => {
                  setBook((prev) => prev ? {
                    ...prev,
                    chapters: prev.chapters.map((c) => c.id === activeCh.id ? { ...c, title } : c),
                  } : prev);
                  debouncedSave(() => handleChUpdate(activeCh.id, title, activeCh.content_html), 800);
                }}
              />
            ) : (
              <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--text-muted)' }}>
                Sélectionnez un chapitre
              </div>
            )}
          </main>

          {/* Style panel */}
          <StylePanel style={style} onChange={handleStyleChange} />
        </div>
      )}

      {/* Status bar */}
      <footer className="status-bar">
        {book ? (
          <>
            <span className={`status-dot ${saving ? 'saving' : 'saved'}`} />
            <span>{saving ? 'Sauvegarde…' : 'Sauvegardé'}</span>
            {activeCh && <><span>·</span><span>{chCount} mots</span></>}
            {meta?.source_file && <><span>·</span><span style={{ overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 200 }}>{meta.source_file}</span></>}
          </>
        ) : (
          <span>Prêt</span>
        )}
      </footer>

      {/* Preview */}
      {showPreview && (
        <div className="preview-overlay" onClick={() => setShowPreview(false)}>
          <div className="preview-modal" onClick={(e) => e.stopPropagation()}>
            <div className="preview-modal-header">
              <span>Aperçu — {bookTitle || 'livre'}</span>
              <div style={{ display: 'flex', gap: 6 }}>
                <button className="header-btn" onClick={() => {
                  if (previewIframe.current) previewIframe.current.src = `/api/preview?t=${Date.now()}`;
                }}>🔄</button>
                <button className="header-btn" onClick={() => setShowPreview(false)}>Fermer</button>
              </div>
            </div>
            <div className="preview-modal-body">
              <iframe ref={previewIframe} title="Aperçu" />
            </div>
          </div>
        </div>
      )}
      <ProjectSetupDialog
        open={showSetup}
        initialTitle={bookTitle}
        initialAuthor={bookAuthor}
        onSave={handleSetupSave}
        onClose={() => setShowSetup(false)}
      />
    </div>
  );
}
