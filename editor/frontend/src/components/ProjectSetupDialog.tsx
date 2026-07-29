/* KLEIA-UP Book Editor — Project Setup Dialog */

import { useState, useEffect, useRef } from 'react';

interface Props {
  open: boolean;
  initialTitle?: string;
  initialAuthor?: string;
  onSave: (title: string, author: string, coverFile?: File) => void;
  onClose: () => void;
}

export default function ProjectSetupDialog({ open, initialTitle, initialAuthor, onSave, onClose }: Props) {
  const [title, setTitle] = useState(initialTitle || '');
  const [author, setAuthor] = useState(initialAuthor || '');
  const [aliases, setAliases] = useState<string[]>([]);
  const [showAliasInput, setShowAliasInput] = useState(false);
  const [newAlias, setNewAlias] = useState('');
  const [coverPreview, setCoverPreview] = useState<string | null>(null);
  const [coverFile, setCoverFile] = useState<File | null>(null);
  const [coverFilename, setCoverFilename] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!open) return;
    fetch('/api/aliases')
      .then((r) => r.json())
      .then((d) => setAliases(d.aliases || []))
      .catch(() => {});
  }, [open]);

  if (!open) return null;

  const handleSubmit = () => {
    if (!title.trim()) return;
    onSave(title.trim(), author.trim(), coverFile || undefined);
  };

  const handleCover = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setCoverFile(f);
    setCoverFilename(f.name);
    const reader = new FileReader();
    reader.onload = () => setCoverPreview(reader.result as string);
    reader.readAsDataURL(f);
  };

  const handleAddAlias = async () => {
    const name = newAlias.trim();
    if (!name) return;
    try {
      const res = await fetch('/api/aliases', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name }),
      });
      const data = await res.json();
      setAliases(data.aliases || []);
      setAuthor(name);
      setShowAliasInput(false);
      setNewAlias('');
    } catch {}
  };

  return (
    <div style={{
      position: 'fixed', inset: 0,
      background: 'rgba(0,0,0,0.4)',
      zIndex: 1000,
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{
        background: 'white', borderRadius: 14,
        padding: 32, width: 420, maxWidth: '92vw',
        boxShadow: '0 8px 32px rgba(0,0,0,0.15)',
      }}>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 4 }}>
          Nouveau projet
        </h2>
        <p style={{ fontSize: 13, color: '#6b7280', marginBottom: 24 }}>
          Informations du livre
        </p>

        {/* Title */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 4 }}>
            Titre du livre *
          </label>
          <input
            autoFocus
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Ex: Hypersensible — lâcher prise pour être soi"
            style={{
              width: '100%', padding: '10px 14px',
              border: '1px solid #d1d5db', borderRadius: 8,
              fontSize: 14, outline: 'none',
            }}
            onKeyDown={(e) => e.key === 'Enter' && title.trim() && handleSubmit()}
          />
        </div>

        {/* Author / Alias */}
        <div style={{ marginBottom: 16 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 4 }}>
            Auteur / Alias
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <input
              type="text"
              value={author}
              onChange={(e) => setAuthor(e.target.value)}
              placeholder="Votre nom ou alias"
              style={{
                flex: 1, padding: '10px 14px',
                border: '1px solid #d1d5db', borderRadius: 8,
                fontSize: 14, outline: 'none',
              }}
            />
          </div>

          {/* Alias selector */}
          {aliases.length > 0 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginTop: 6 }}>
              {aliases.map((a) => (
                <button
                  key={a}
                  onClick={() => setAuthor(a)}
                  style={{
                    padding: '3px 10px', border: '1px solid #e5e7eb',
                    borderRadius: 12, fontSize: 12, cursor: 'pointer',
                    background: author === a ? '#eef2ff' : 'white',
                    color: author === a ? '#4f46e5' : '#374151',
                    fontWeight: author === a ? 600 : 400,
                  }}
                >{a}</button>
              ))}
            </div>
          )}

          {/* Add new alias */}
          {!showAliasInput ? (
            <button
              onClick={() => setShowAliasInput(true)}
              style={{
                marginTop: 6, padding: 0, border: 'none',
                background: 'none', cursor: 'pointer',
                fontSize: 12, color: '#4f46e5', fontWeight: 500,
              }}
            >+ Ajouter un alias</button>
          ) : (
            <div style={{ display: 'flex', gap: 6, marginTop: 6 }}>
              <input
                type="text"
                value={newAlias}
                onChange={(e) => setNewAlias(e.target.value)}
                placeholder="Nouvel alias"
                style={{
                  flex: 1, padding: '5px 10px',
                  border: '1px solid #d1d5db', borderRadius: 6,
                  fontSize: 13, outline: 'none',
                }}
                onKeyDown={(e) => e.key === 'Enter' && handleAddAlias()}
              />
              <button onClick={handleAddAlias}
                style={{
                  padding: '5px 12px', border: '1px solid #4f46e5',
                  borderRadius: 6, fontSize: 13, cursor: 'pointer',
                  background: '#4f46e5', color: 'white', fontWeight: 500,
                }}
              >Ajouter</button>
            </div>
          )}
        </div>

        {/* Cover */}
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 4 }}>
            Couverture
          </label>
          <div
            onClick={() => fileRef.current?.click()}
            style={{
              border: '2px dashed #d1d5db', borderRadius: 8,
              padding: coverPreview ? 8 : 20,
              textAlign: 'center', cursor: 'pointer',
              background: '#f9fafb',
              transition: 'border-color 0.15s',
              minHeight: coverPreview ? 120 : 'auto',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
            onMouseEnter={(e) => e.currentTarget.style.borderColor = '#4f46e5'}
            onMouseLeave={(e) => e.currentTarget.style.borderColor = '#d1d5db'}
          >
            {coverPreview ? (
              <img src={coverPreview} alt="Cover preview"
                style={{ maxHeight: 200, maxWidth: '100%', borderRadius: 6, objectFit: 'contain' }} />
            ) : (
              <span style={{ fontSize: 13, color: '#9ca3af' }}>
                Cliquez pour ajouter une couverture
              </span>
            )}
          </div>
          <input ref={fileRef} type="file" accept="image/*"
            onChange={handleCover}
            style={{ display: 'none' }} />
          {coverFilename && (
            <span style={{ fontSize: 12, color: '#6b7280', marginTop: 4, display: 'block' }}>
              {coverFilename}
            </span>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
          <button onClick={onClose}
            style={{
              padding: '8px 18px', border: '1px solid #d1d5db',
              borderRadius: 8, fontSize: 14, cursor: 'pointer',
              background: 'white',
            }}
          >Plus tard</button>
          <button onClick={handleSubmit}
            disabled={!title.trim()}
            style={{
              padding: '8px 18px', border: 'none',
              borderRadius: 8, fontSize: 14, cursor: 'pointer',
              background: title.trim() ? '#4f46e5' : '#d1d5db',
              color: title.trim() ? 'white' : '#9ca3af',
              fontWeight: 600,
            }}
          >Enregistrer</button>
        </div>
      </div>
    </div>
  );
}
