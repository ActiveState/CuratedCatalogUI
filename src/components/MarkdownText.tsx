import styles from './MarkdownText.module.css'

function esc(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function inlineFmt(raw: string): string {
  const spans: string[] = []
  // extract code spans first so their content is never touched by other rules
  let s = raw.replace(/``([^`]+)``|`([^`]+)`/g, (_, a, b) => {
    spans.push(`<code>${esc(a ?? b)}</code>`)
    return `\x02${spans.length - 1}\x02`
  })
  s = esc(s)
  // bold before italic so ** is handled first
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>')
  // links [text](url)
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, t, u) =>
    `<a href="${u}" target="_blank" rel="noopener">${t}</a>`)
  // bare URLs
  s = s.replace(/(^|[\s(])(https?:\/\/[^\s<>"&)]+)/g, (_, pre, u) =>
    `${pre}<a href="${u}" target="_blank" rel="noopener">${u}</a>`)
  // restore code spans
  spans.forEach((c, i) => { s = s.replaceAll(`\x02${i}\x02`, c) })
  return s
}

function isTableBlock(lines: string[]): boolean {
  return lines.length >= 2 &&
    lines[0].includes('|') &&
    /^\s*\|?[\s\-:|]+\|/.test(lines[1])
}

function renderTable(lines: string[]): string {
  const parseRow = (l: string) =>
    l.replace(/^\s*\|/, '').replace(/\|\s*$/, '').split('|').map(c => c.trim())

  const headers = parseRow(lines[0])
  const rows = lines.slice(2).filter(l => l.includes('|')).map(parseRow)

  const th = headers.map(h => `<th>${inlineFmt(h)}</th>`).join('')
  const tbody = rows.map(r =>
    '<tr>' + r.map(c => `<td>${inlineFmt(c)}</td>`).join('') + '</tr>'
  ).join('')

  return `<table><thead><tr>${th}</tr></thead><tbody>${tbody}</tbody></table>`
}

export function parseMarkdown(raw: string): string {
  // normalise section headers that run together: "text  ## Heading" → "text\n\n## Heading"
  let text = raw
    .replace(/(?<!\n)\s{2,}(#{1,4} )/g, '\n\n$1')
    .replace(/\n(#{1,4} )/g, '\n\n$1')

  // extract fenced code blocks — wrap placeholder in \n\n so it becomes its own block
  const codeBlocks: string[] = []
  text = text.replace(/```([^\n]*)\n?([\s\S]*?)```/g, (_, _lang, code) => {
    codeBlocks.push(`<pre><code>${esc(code.trimEnd())}</code></pre>`)
    return `\n\n\x01${codeBlocks.length - 1}\x01\n\n`
  })

  const blocks = text.split(/\n{2,}/).map(b => b.trim()).filter(Boolean)
  const out: string[] = []

  for (const block of blocks) {
    // code block placeholder
    const cbm = block.match(/^\x01(\d+)\x01$/)
    if (cbm) { out.push(codeBlocks[+cbm[1]]); continue }

    // heading — may have content on the same line after the title word
    const hm = block.match(/^(#{1,4})\s+(.+)/)
    if (hm) {
      const tag = hm[1].length === 1 ? 'h3' : 'h4'
      // split "### Title  body text here" on 2+ spaces or a newline
      const [title, ...rest] = hm[2].split(/\s{2,}|\n/)
      out.push(`<${tag}>${inlineFmt(title)}</${tag}>`)
      if (rest.length) {
        const body = rest.join(' ').trim()
        if (body) out.push(`<p>${inlineFmt(body)}</p>`)
      }
      continue
    }

    const lines = block.split('\n')

    // table
    if (isTableBlock(lines)) {
      out.push(renderTable(lines))
      continue
    }

    // bullet list
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

  // safety net: replace any code block placeholders that slipped into paragraphs
  let html = out.join('\n')
  codeBlocks.forEach((cb, i) => { html = html.replaceAll(`\x01${i}\x01`, cb) })
  return html
}

export function MarkdownText({ text }: { text: string }) {
  return (
    <div
      className={styles.root}
      dangerouslySetInnerHTML={{ __html: parseMarkdown(text) }}
    />
  )
}
