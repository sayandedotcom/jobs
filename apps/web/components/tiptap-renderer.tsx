"use client"

import * as React from "react"
import { EditorContent, useEditor } from "@tiptap/react"
import StarterKit from "@tiptap/starter-kit"
import Link from "@tiptap/extension-link"

export function TiptapRenderer({ content }: { content: string }) {
  const editor = useEditor({
    extensions: [
      StarterKit,
      Link.configure({
        HTMLAttributes: {
          target: "_blank",
          rel: "noopener noreferrer",
        },
      }),
    ],
    content,
    editable: false,
    immediatelyRender: true,
  })

  if (!editor) return null

  return <EditorContent editor={editor} className="tiptap-renderer" />
}
