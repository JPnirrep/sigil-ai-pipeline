/* KLEIA-UP Book Editor — TipTap Rich Text Editor Component */

import { useCallback } from 'react';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Heading from '@tiptap/extension-heading';
import Image from '@tiptap/extension-image';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';
import Placeholder from '@tiptap/extension-placeholder';
import Blockquote from '@tiptap/extension-blockquote';
import { StyleOverrides } from '../types';

interface RichEditorProps {
  content: string;
  chapterTitle: string;
  style: StyleOverrides;
  onUpdate: (html: string) => void;
  onTitleUpdate?: (title: string) => void;
}

export default function RichEditor({ content, chapterTitle, style, onUpdate, onTitleUpdate }: RichEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: false,
        blockquote: false,
      }),
      Heading.configure({
        levels: [1, 2, 3],
      }),
      Image.configure({
        inline: false,
        allowBase64: true,
      }),
      TextAlign.configure({
        types: ['heading', 'paragraph'],
      }),
      Underline,
      Placeholder.configure({
        placeholder: 'Commencez à écrire…',
      }),
      Blockquote,
    ],
    content,
    onUpdate: ({ editor }) => {
      onUpdate(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'prose-editor',
      },
    },
  });

  const handleImageUpload = useCallback(() => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file || !editor) return;

      try {
        const form = new FormData();
        form.append('file', file);
        const res = await fetch('/api/image/upload', { method: 'POST', body: form });
        const data = await res.json();
        editor.chain().focus().setImage({ src: data.url }).run();
      } catch {
        const reader = new FileReader();
        reader.onload = () => {
          editor.chain().focus().setImage({ src: reader.result as string }).run();
        };
        reader.readAsDataURL(file);
      }
    };
    input.click();
  }, [editor]);

  if (!editor) return null;

  const ToolBtn = ({ cmd, label, isActive, title }: {
    cmd: () => void; label: string; isActive?: boolean; title?: string;
  }) => (
    <button onClick={cmd} className={isActive ? 'active' : ''} title={title} type="button">
      {label}
    </button>
  );

  const HeadingSelect = ({ level }: { level: 1 | 2 | 3 }) => {
    const label = { 1: 'H1', 2: 'H2', 3: 'H3' }[level];
    return (
      <ToolBtn
        cmd={() => editor.chain().focus().toggleHeading({ level }).run()}
        label={label}
        isActive={editor.isActive('heading', { level })}
        title={`Titre ${level}`}
      />
    );
  };

  return (
    <div>
      <div className="editor-toolbar">
        <input
          type="text"
          value={chapterTitle}
          onChange={(e) => onTitleUpdate?.(e.target.value)}
          style={{
            border: 'none', background: 'transparent', fontSize: 14,
            fontWeight: 600, flex: 1, padding: '4px 8px',
            outline: 'none', fontFamily: 'inherit',
          }}
          placeholder="Titre du chapitre"
        />
        <div className="separator" />
        <ToolBtn cmd={() => editor.chain().focus().undo().run()} label="↶" title="Annuler" />
        <ToolBtn cmd={() => editor.chain().focus().redo().run()} label="↷" title="Rétablir" />
        <div className="separator" />
        <HeadingSelect level={1} />
        <HeadingSelect level={2} />
        <HeadingSelect level={3} />
        <div className="separator" />
        <ToolBtn cmd={() => editor.chain().focus().toggleBold().run()} label="B" isActive={editor.isActive('bold')} title="Gras" />
        <ToolBtn cmd={() => editor.chain().focus().toggleItalic().run()} label="I" isActive={editor.isActive('italic')} title="Italique" />
        <ToolBtn cmd={() => editor.chain().focus().toggleUnderline().run()} label="U" isActive={editor.isActive('underline')} title="Souligné" />
        <div className="separator" />
        <ToolBtn cmd={() => editor.chain().focus().setTextAlign('left').run()} label="≡" isActive={editor.isActive({ textAlign: 'left' })} title="Aligné à gauche" />
        <ToolBtn cmd={() => editor.chain().focus().setTextAlign('center').run()} label="≡" isActive={editor.isActive({ textAlign: 'center' })} title="Centré" />
        <ToolBtn cmd={() => editor.chain().focus().setTextAlign('justify').run()} label="≡" isActive={editor.isActive({ textAlign: 'justify' })} title="Justifié" />
        <div className="separator" />
        <ToolBtn cmd={() => editor.chain().focus().toggleBlockquote().run()} label="❝" isActive={editor.isActive('blockquote')} title="Citation" />
        <ToolBtn cmd={handleImageUpload} label="🖼" title="Insérer image" />
      </div>

      {/* Editor content — CSS vars driven by style panel for WYSIWYG */}
      <div className="editor-content"
        style={{
          '--wysiwyg-font': style.body_font,
          '--wysiwyg-size': style.body_size,
          '--wysiwyg-lineheight': style.body_line_height,
          '--wysiwyg-align': style.body_alignment,
          '--wysiwyg-color': style.body_color,
          '--wysiwyg-h1-size': style.h1_size,
          '--wysiwyg-h1-weight': style.h1_weight,
          '--wysiwyg-h1-align': style.h1_align,
          '--wysiwyg-h1-color': style.h1_color,
          '--wysiwyg-h1-mt': style.h1_margin_top,
          '--wysiwyg-h1-mb': style.h1_margin_bottom,
          '--wysiwyg-h2-size': style.h2_size,
          '--wysiwyg-h2-weight': style.h2_weight,
          '--wysiwyg-h2-color': style.h2_color,
          '--wysiwyg-h2-mt': style.h2_margin_top,
          '--wysiwyg-h2-mb': style.h2_margin_bottom,
          '--wysiwyg-h3-size': style.h3_size,
          '--wysiwyg-h3-weight': style.h3_weight,
          '--wysiwyg-h3-color': style.h3_color,
        } as React.CSSProperties}
      >
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}
