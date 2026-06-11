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
  // split row on |, trim, ignore empty first/last
  const splitRow = (l: string) =>
    l.split('|').slice(1).map(c => c.trim()).filter((c, i, a) =>
      !(i === a.length - 1 && c === '')
    )

  const headers = splitRow(lines[0])
  const rows = lines.slice(2)
    .filter(l => l.includes('|') && !/^[\s\-:|]+$/.test(l))
    .map(splitRow)

  const th = headers.map(h => `<th>${inlineFmt(h)}</th>`).join('')
  const tbody = rows.map(r => {
    const cells = headers.map((_, i) => `<td>${inlineFmt(r[i] ?? '')}</td>`).join('')
    return `<tr>${cells}</tr>`
  }).join('')
  return `<table><thead><tr>${th}</tr></thead><tbody>${tbody}</tbody></table>`
}

function normalizeInlineTable(text: string): string[] | null {
  if (!text.includes('|')) return null
  const lines = text.replace(/\| \|/g, '|\n|').split('\n').map(l => l.trim()).filter(Boolean)
  return isTableBlock(lines) ? lines : null
}

// Split an inline " - item1 - item2" format into ["item1", "item2"]
function splitInlineList(text: string): string[] | null {
  // Normalize leading "- " then split on " - "
  const norm = text.replace(/^[-*]\s+/, '')
  const parts = norm.split(/ - (?=\S)/).map(p => p.trimEnd())
  return parts.length >= 2 ? parts : null
}

function processBody(bodyRaw: string, codeBlocks: string[], out: string[]) {
  if (!bodyRaw.trim()) return

  // Code block placeholder
  const pcb = bodyRaw.trim().match(/^\x01(\d+)\x01$/)
  if (pcb) { out.push(codeBlocks[+pcb[1]]); return }

  // Inline table
  const tableLines = normalizeInlineTable(bodyRaw)
  if (tableLines) { out.push(renderTable(tableLines)); return }

  // Multi-line content: split and recurse through blocks
  const subBlocks = bodyRaw.split(/\n{2,}/).map(b => b.trim()).filter(Boolean)
  if (subBlocks.length > 1) {
    for (const sub of subBlocks) {
      processBody(sub, codeBlocks, out)
    }
    return
  }

  const lines = bodyRaw.split('\n')

  // Multi-line bullet list
  if (lines.some(l => /^[-*]\s/.test(l.trim()))) {
    const pre   = lines.filter(l => !/^[-*\s]/.test(l.trim()) && l.trim())
    const items = lines.filter(l => /^[-*]\s/.test(l.trim()))
    if (pre.length) out.push(`<p>${inlineFmt(pre.join(' '))}</p>`)
    out.push('<ul>' + items.map(l => `<li>${inlineFmt(l.trim().slice(2))}</li>`).join('') + '</ul>')
    return
  }

  // Inline " - item" list (e.g. "- **A**: desc - **B**: desc")
  if (/^[-*]\s/.test(bodyRaw.trim()) || (bodyRaw.match(/ - /g) || []).length >= 2) {
    const parts = splitInlineList(bodyRaw)
    if (parts) {
      out.push('<ul>' + parts.map(p => `<li>${inlineFmt(p)}</li>`).join('') + '</ul>')
      return
    }
  }

  // Numbered list
  if (lines.some(l => /^\d+\.\s/.test(l.trim()))) {
    const items = lines.filter(l => /^\d+\.\s/.test(l.trim()))
    out.push('<ol>' + items.map(l => `<li>${inlineFmt(l.trim().replace(/^\d+\.\s/, ''))}</li>`).join('') + '</ol>')
    return
  }

  // Paragraph
  out.push(`<p>${inlineFmt(lines.join(' '))}</p>`)
}

export function parseMarkdown(raw: string): string {
  // Normalise run-together section headers
  let text = raw
    .replace(/(?<!\n)\s{2,}(#{1,4} )/g, '\n\n$1')
    .replace(/\n(#{1,4} )/g, '\n\n$1')

  // Extract fenced code blocks first — wrap placeholder in \n\n
  const codeBlocks: string[] = []
  text = text.replace(/```(\w*)[^\S\n]*\n?([\s\S]*?)```/g, (_, _lang, code) => {
    codeBlocks.push(`<pre><code>${esc(code.trimEnd())}</code></pre>`)
    return `\n\n\x01${codeBlocks.length - 1}\x01\n\n`
  })

  // Detect implicit OSV section headings: "Summary  text" or "Impact  text"
  // (used when OSV strips the ## markers)
  const implicitSections = 'Summary|Details|Impact|PoC|Patches|References|Acknowledgement|Remediation|Workarounds|Mitigation|Reproduction|Script|Notes|Background|Fix'
  text = text.replace(
    new RegExp(`(^|\\s{2,})(${implicitSections})(\\s{2,})`, 'g'),
    (_match, _pre, word) => `\n\n## ${word}\n\n`
  )
  // Re-run header normalisation after implicit heading injection
  text = text
    .replace(/(?<!\n)\s{2,}(#{1,4} )/g, '\n\n$1')
    .replace(/\n(#{1,4} )/g, '\n\n$1')

  // Normalise inline tables: "| |" row boundaries → actual newlines
  text = text.replace(/\| \|/g, '|\n|')

  const blocks = text.split(/\n{2,}/).map(b => b.trim()).filter(Boolean)
  const out: string[] = []

  for (const block of blocks) {
    // Code block placeholder
    const cbm = block.match(/^\x01(\d+)\x01$/)
    if (cbm) { out.push(codeBlocks[+cbm[1]]); continue }

    // Heading — title is everything up to the first 2+ spaces (OSV inline body pattern)
    // or the end of the first line, whichever comes first. Subsequent lines are body.
    const hm = block.match(/^(#{1,4})\s+/)
    if (hm) {
      const tag = hm[1].length === 1 ? 'h3' : 'h4'
      const afterHash = block.slice(hm[0].length)
      const lines = afterHash.split('\n')
      const firstLine = lines[0]
      const split = firstLine.match(/^(\S.*?)\s{2,}(.+)$/)
      const title = split ? split[1] : firstLine.trimEnd()
      const inlineBody = split ? split[2] : ''
      const laterLines = lines.slice(1).join('\n').trimStart()
      const bodyRaw = [inlineBody, laterLines].filter(Boolean).join('\n')

      out.push(`<${tag}>${inlineFmt(title)}</${tag}>`)
      processBody(bodyRaw, codeBlocks, out)
      continue
    }

    // Table
    const lines = block.split('\n')
    if (isTableBlock(lines)) { out.push(renderTable(lines)); continue }

    // Delegate remaining to processBody (handles lists, inline lists, paragraphs)
    processBody(block, codeBlocks, out)
  }

  // Safety net: replace any code block placeholder that slipped through
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
