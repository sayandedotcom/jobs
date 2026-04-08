"use client"

import * as React from "react"

const URL_RE = /https?:\/\/[^\s<>"')\]]+[^\s<>"')\].,;:!?]/
const EMAIL_RE =
  /(?<![^\s<>"'():\/\]])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})/g

function linkifyText(text: string): string {
  let result = text.replace(
    new RegExp(URL_RE.source, "g"),
    (url) =>
      `<a href="${url}" target="_blank" rel="noopener noreferrer">${url}</a>`
  )
  result = result.replace(EMAIL_RE, (_match, email) => {
    return `<a href="mailto:${email}">${email}</a>`
  })
  return result
}

function linkifyHtml(html: string): string {
  const parts = html.split(/(<[^>]+>)/)
  let inAnchor = false
  return parts
    .map((part) => {
      if (part.startsWith("<")) {
        if (/^<a[\s>]/i.test(part)) inAnchor = true
        else if (/^<\/a/i.test(part)) inAnchor = false
        return part
      }
      return inAnchor ? part : linkifyText(part)
    })
    .join("")
}

export function HtmlRenderer({ content }: { content: string }) {
  if (!content) return null

  const html = linkifyHtml(content)

  return (
    <div
      className="tiptap-renderer"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  )
}
