import styles from './MarkdownText.module.css'

function escHtml(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function inlineFmt(raw: string): string {
  // extract code spans first so their content isn't affected by other rules
  const spans: string[] = []
  let s = raw.replace(/``([^`]+)``|`([^`]+)`/g, (_, a, b) => {
    spans.push(`<code>${escHtml(a ?? b)}</code>`)
    return `\x02${spans.length - 1}\x02`
  })
  // escape remaining HTML
  s = escHtml(s)
  // bold
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  // italic (avoid matching **)
  s = s.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, '<em>$1</em>')
  // links [text](url)
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, t, u) =>
    `<a href="${u}" target="_blank" rel="noopener">${t}</a>`)
  // bare URLs
  s = s.replace(/(^|[\s(])(https?:\/\/[^\s<>"&)]+)/g, (_, pre, u) =>
    `${pre}<a href="${u}" target="_blank" rel="noopener">${u}</a>`)
  // restore code spans
  spans.forEach((c, i) => { s = s.replace(`\x02${i}\x02`, c) })
  return s
}

function parse(raw: string): string {
  // normalise section headers that run into content on the same line:
  // "### Summary  some text" → "### Summary\n\nsome text"
  // "some text  ### Next" → "some text\n\n### Next"
  let text = raw
    .replace(/(?<!\n)\s{2,}(#{1,4} )/g, '\n\n$1')
    .replace(/\n(#{1,4} )/g, '\n\n$1')

  // extract fenced code blocks
  const codeBlocks: string[] = []
  text = text.replace(/```([^\n]*)\n([\s\S]*?)```/g, (_, _lang, code) => {
    codeBlocks.push(`<pre><code>${escHtml(code.trimEnd())}</code></pre>`)
    return `\x01${codeBlocks.length - 1}\x01`
  })

  const blocks = text.split(/\n{2,}/).map(b => b.trim()).filter(Boolean)
  const out: string[] = []

  for (const block of blocks) {
    // code block placeholder
    const cbm = block.match(/^\x01(\d+)\x01$/)
    if (cbm) { out.push(codeBlocks[+cbm[1]]); continue }

    // heading — treat heading word(s) as label, rest as first paragraph
    const hm = block.match(/^(#{1,4})\s+(.+)/)
    if (hm) {
      const level = hm[1].length
      // split "Summary  content that follows" into heading + content
      const rest = hm[2].replace(/\s{2,}/, '\x03')
      const [title, content] = rest.includes('\x03') ? rest.split('\x03') : [rest, '']
      const tag = level === 1 ? 'h3' : 'h4'
      out.push(`<${tag}>${inlineFmt(title)}</${tag}>`)
      if (content?.trim()) out.push(`<p>${inlineFmt(content.trim())}</p>`)
      continue
    }

    // bullet list
    const lines = block.split('\n')
    if (lines.some(l => /^[-*]\s/.test(l.trim()))) {
      const items = lines.filter(l => /^[-*]\s/.test(l.trim()))
      out.push('<ul>' + items.map(l => `<li>${inlineFmt(l.trim().slice(2))}</li>`).join('') + '</ul>')
      continue
    }

    // numbered list
    if (lines.some(l => /^\d+\.\s/.test(l.trim()))) {
      const items = lines.filter(l => /^\d+\.\s/.test(l.trim()))
      out.push('<ol>' + items.map(l => `<li>${inlineFmt(l.trim().replace(/^\d+\.\s/, ''))}</li>`).join('') + '</ol>')
      continue
    }

    // paragraph — join lines with a space
    out.push(`<p>${inlineFmt(lines.join(' '))}</p>`)
  }

  return out.join('\n')
}

export function MarkdownText({ text }: { text: string }) {
  return (
    <div
      className={styles.root}
      dangerouslySetInnerHTML={{ __html: parse(text) }}
    />
  )
}
