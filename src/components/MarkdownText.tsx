import styles from './MarkdownText.module.css'

function esc(s: string) {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')
}

function inlineFmt(raw: string): string {
  const spans: string[] = []
  let s = raw.replace(/``([^`]+)``|`([^`]+)`/g, (_, a, b) => {
    spans.push(`<code>${esc(a ?? b)}</code>`)
    return `\x02${spans.length - 1}\x02`
  })
  s = esc(s)
  s = s.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
  s = s.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em>$1</em>')
  s = s.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, t, u) =>
    `<a href="${u}" target="_blank" rel="noopener">${t}</a>`)
  s = s.replace(/(^|[\s(])(https?:\/\/[^\s<>"&)]+)/g, (_, pre, u) =>
    `${pre}<a href="${u}" target="_blank" rel="noopener">${u}</a>`)
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

// Convert inline table format "| col | col | |---| | val | val |" to line-per-row
function normalizeInlineTable(text: string): string[] | null {
  if (!text.includes('|')) return null
  const lines = text.replace(/\| \|/g, '|\n|').split('\n').map(l => l.trim()).filter(Boolean)
  return isTableBlock(lines) ? lines : null
}

export function parseMarkdown(raw: string): string {
  // Normalise run-together section headers: "text  ## Heading" → "text\n\n## Heading"
  let text = raw
    .replace(/(?<!\n)\s{2,}(#{1,4} )/g, '\n\n$1')
    .replace(/\n(#{1,4} )/g, '\n\n$1')

  // Extract fenced code blocks first — wrap placeholder in \n\n
  // (\w*) = lang id only; [^\S\n]* skips horizontal space; \n? optional newline
  // Handles both "```python\ncode```" and OSV's no-newline "```python code```"
  const codeBlocks: string[] = []
  text = text.replace(/```(\w*)[^\S\n]*\n?([\s\S]*?)```/g, (_, _lang, code) => {
    codeBlocks.push(`<pre><code>${esc(code.trimEnd())}</code></pre>`)
    return `\n\n\x01${codeBlocks.length - 1}\x01\n\n`
  })

  // Normalise inline tables: "| |" row boundaries → actual newlines
  // No leading-space requirement: separator rows end with "|" (not " |")
  text = text.replace(/\| \|/g, '|\n|')

  // Normalise inline " - item - item" list separators → line-per-item
  // Only when 3+ occurrences (to avoid matching simple "A - B" constructs)
  text = text.replace(/^(.+?)( - .+){3,}$/gm, (match) => {
    return match.replace(/ - /g, '\n- ')
  })

  const blocks = text.split(/\n{2,}/).map(b => b.trim()).filter(Boolean)
  const out: string[] = []

  for (let block of blocks) {
    // Code block placeholder
    const cbm = block.match(/^\x01(\d+)\x01$/)
    if (cbm) { out.push(codeBlocks[+cbm[1]]); continue }

    // Heading — title is the FIRST word; everything after is the body
    // (OSV uses both "### Title  body" with 2+ spaces AND "### Title body" with 1 space)
    const hm = block.match(/^(#{1,4})\s+(.+)/)
    if (hm) {
      const tag = hm[1].length === 1 ? 'h3' : 'h4'
      const spaceIdx = hm[2].search(/\s/)
      const title   = spaceIdx > 0 ? hm[2].slice(0, spaceIdx) : hm[2]
      const bodyRaw = spaceIdx > 0 ? hm[2].slice(spaceIdx).trimStart() : ''
      out.push(`<${tag}>${inlineFmt(title)}</${tag}>`)
      if (bodyRaw) {
        // Body might itself be a code block placeholder
        const pcb = bodyRaw.match(/^\x01(\d+)\x01$/)
        if (pcb) {
          out.push(codeBlocks[+pcb[1]])
        } else {
          const tableLines = normalizeInlineTable(bodyRaw)
          if (tableLines) {
            out.push(renderTable(tableLines))
          } else {
            out.push(`<p>${inlineFmt(bodyRaw)}</p>`)
          }
        }
      }
      continue
    }

    const lines = block.split('\n')

    // Table
    if (isTableBlock(lines)) { out.push(renderTable(lines)); continue }

    // Bullet list
    if (lines.some(l => /^[-*]\s/.test(l.trim()))) {
      const items = lines.filter(l => /^[-*]\s/.test(l.trim()))
      const pre   = lines.filter(l => !/^[-*\s]/.test(l.trim()) && l.trim())
      if (pre.length) out.push(`<p>${inlineFmt(pre.join(' '))}</p>`)
      out.push('<ul>' + items.map(l => `<li>${inlineFmt(l.trim().slice(2))}</li>`).join('') + '</ul>')
      continue
    }

    // Numbered list
    if (lines.some(l => /^\d+\.\s/.test(l.trim()))) {
      const items = lines.filter(l => /^\d+\.\s/.test(l.trim()))
      out.push('<ol>' + items.map(l => `<li>${inlineFmt(l.trim().replace(/^\d+\.\s/, ''))}</li>`).join('') + '</ol>')
      continue
    }

    // Paragraph
    out.push(`<p>${inlineFmt(lines.join(' '))}</p>`)
  }

  // Safety net: replace any code block placeholder that slipped into a paragraph
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
