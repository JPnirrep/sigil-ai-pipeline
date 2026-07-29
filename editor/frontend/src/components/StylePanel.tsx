/* KLEIA-UP Book Editor — Panneau Style */

import { StyleOverrides } from '../types';

interface Props {
  style: StyleOverrides;
  onChange: (s: StyleOverrides) => void;
}

const FONT_OPTIONS = [
  { label: 'Times New Roman', value: "Georgia, 'Times New Roman', serif" },
  { label: 'Georgia', value: "Georgia, 'Times New Roman', serif" },
  { label: 'Garamond', value: 'Garamond, serif' },
  { label: 'Palatino', value: 'Palatino, serif' },
  { label: 'Arial', value: 'Arial, Helvetica, sans-serif' },
  { label: 'Helvetica', value: "'Helvetica Neue', Arial, sans-serif" },
  { label: 'System UI', value: 'system-ui, sans-serif' },
];

const SIZE_OPTIONS = ['9 pt', '10 pt', '10.5 pt', '11 pt', '11.5 pt', '12 pt', '13 pt', '14 pt'];
const LINE_HEIGHT_OPTIONS = ['1.15', '1.3', '1.4', '1.5', '1.6', '1.8', '2.0'];
const ALIGN_OPTIONS = ['Gauche', 'Centre', 'Droite', 'Justifié'];
const WEIGHT_OPTIONS = ['Normal', 'Gras', 'Light'];
const HEADING_SIZE_OPS = ['14 pt', '16 pt', '18 pt', '20 pt', '22 pt', '24 pt', '26 pt', '28 pt', '30 pt'];
const SUB_SIZE_OPS = ['12 pt', '13 pt', '14 pt', '15 pt', '16 pt', '17 pt', '18 pt', '20 pt'];

const ALIGN_MAP: Record<string, string> = { 'Gauche': 'left', 'Centre': 'center', 'Droite': 'right', 'Justifié': 'justify' };
const WEIGHT_MAP: Record<string, string> = { 'Normal': 'normal', 'Gras': 'bold', 'Light': 'lighter' };
const PT_MAP = (v: string) => v.replace(' pt', 'pt');

function Select({ label, options, value, onChange }: {
  label: string; options: { label: string; value: string }[] | string[]; value: string; onChange: (v: string) => void;
}) {
  const items = Array.isArray(options) && options[0] && typeof options[0] === 'object' ? options as { label: string; value: string }[] : null;
  return (
    <div className="style-field">
      <label>{label}</label>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {items ? items.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)
          : (options as string[]).map((o) => <option key={o} value={PT_MAP(o)}>{o}</option>)}
      </select>
    </div>
  );
}

function ColorField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div className="style-field">
      <label>{label}</label>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input type="color" value={value} onChange={(e) => onChange(e.target.value)}
          style={{ width: 36, height: 32, border: '1px solid var(--border)', borderRadius: 5, padding: 1, cursor: 'pointer' }} />
        <input type="text" value={value} onChange={(e) => onChange(e.target.value)}
          style={{ flex: 1 }} />
      </div>
    </div>
  );
}

export default function StylePanel({ style, onChange }: Props) {
  const upd = (p: Partial<StyleOverrides>) => onChange({ ...style, ...p });

  return (
    <div className="style-panel">
      <div className="style-panel-header">Style du livre</div>

      <div className="style-group">
        <div className="style-group-title">Texte courant</div>
        <Select label="Police" options={FONT_OPTIONS} value={style.body_font} onChange={(v) => upd({ body_font: v })} />
        <Select label="Taille" options={SIZE_OPTIONS} value={style.body_size} onChange={(v) => upd({ body_size: v })} />
        <Select label="Interligne" options={LINE_HEIGHT_OPTIONS} value={style.body_line_height} onChange={(v) => upd({ body_line_height: v })} />
        <Select label="Alignement" options={ALIGN_OPTIONS} value={Object.entries(ALIGN_MAP).find(([,v]) => v === style.body_alignment)?.[0] || 'Justifié'}
          onChange={(v) => upd({ body_alignment: ALIGN_MAP[v] || 'justify' })} />
        <ColorField label="Couleur texte" value={style.body_color} onChange={(v) => upd({ body_color: v })} />
        <Select label="Espace entre paragraphes" options={['0', '0.1 em', '0.2 em', '0.3 em', '0.5 em', '0.8 em', '1 em']}
          value={style.body_margin_bottom} onChange={(v) => upd({ body_margin_bottom: v })} />
      </div>

      <div className="style-group">
        <div className="style-group-title">Titres H1</div>
        <Select label="Police" options={FONT_OPTIONS} value={style.h1_font} onChange={(v) => upd({ h1_font: v })} />
        <Select label="Taille" options={HEADING_SIZE_OPS} value={style.h1_size} onChange={(v) => upd({ h1_size: v })} />
        <Select label="Poids" options={WEIGHT_OPTIONS} value={Object.entries(WEIGHT_MAP).find(([,v]) => v === style.h1_weight)?.[0] || 'Gras'}
          onChange={(v) => upd({ h1_weight: WEIGHT_MAP[v] || 'bold' })} />
        <Select label="Alignement" options={ALIGN_OPTIONS} value={Object.entries(ALIGN_MAP).find(([,v]) => v === style.h1_align)?.[0] || 'Gauche'}
          onChange={(v) => upd({ h1_align: ALIGN_MAP[v] || 'left' })} />
        <ColorField label="Couleur" value={style.h1_color} onChange={(v) => upd({ h1_color: v })} />
      </div>

      <div className="style-group">
        <div className="style-group-title">Titres H2</div>
        <Select label="Taille" options={SUB_SIZE_OPS} value={style.h2_size} onChange={(v) => upd({ h2_size: v })} />
        <Select label="Poids" options={WEIGHT_OPTIONS} value={Object.entries(WEIGHT_MAP).find(([,v]) => v === style.h2_weight)?.[0] || 'Gras'}
          onChange={(v) => upd({ h2_weight: WEIGHT_MAP[v] || 'bold' })} />
      </div>

      <div className="style-group">
        <div className="style-group-title">Titres H3</div>
        <Select label="Taille" options={SUB_SIZE_OPS} value={style.h3_size} onChange={(v) => upd({ h3_size: v })} />
        <Select label="Poids" options={WEIGHT_OPTIONS} value={Object.entries(WEIGHT_MAP).find(([,v]) => v === style.h3_weight)?.[0] || 'Gras'}
          onChange={(v) => upd({ h3_weight: WEIGHT_MAP[v] || 'bold' })} />
      </div>

      <div className="style-group">
        <div className="style-group-title">Images</div>
        <Select label="Largeur max" options={['50 %', '75 %', '100 %']}
          value={style.image_max_width} onChange={(v) => upd({ image_max_width: v })} />
        <Select label="Alignement" options={ALIGN_OPTIONS}
          value={Object.entries(ALIGN_MAP).find(([,v]) => v === style.image_align)?.[0] || 'Centre'}
          onChange={(v) => upd({ image_align: ALIGN_MAP[v] || 'center' })} />
      </div>
    </div>
  );
}
