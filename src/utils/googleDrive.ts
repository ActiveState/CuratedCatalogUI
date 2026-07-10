// Minimal GSI type declarations — only the subset we actually use
declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient(config: {
            client_id: string
            scope: string
            callback: (r: { access_token?: string; error?: string; expires_in?: number }) => void
          }): { requestAccessToken(): void }
        }
      }
    }
  }
}

const CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID as string | undefined

let gsiLoaded = false
let cachedToken: { value: string; expiresAt: number } | null = null

export function isGoogleConfigured(): boolean {
  return Boolean(CLIENT_ID)
}

export async function preloadGSI(): Promise<void> {
  if (gsiLoaded || window.google?.accounts) { gsiLoaded = true; return }
  await new Promise<void>((resolve, reject) => {
    const s = document.createElement('script')
    s.src = 'https://accounts.google.com/gsi/client'
    s.onload = () => { gsiLoaded = true; resolve() }
    s.onerror = () => reject(new Error('Failed to load Google Sign-In'))
    document.head.appendChild(s)
  })
}

async function getAccessToken(): Promise<string> {
  if (cachedToken && Date.now() < cachedToken.expiresAt - 60_000) {
    return cachedToken.value
  }
  await preloadGSI()
  return new Promise<string>((resolve, reject) => {
    const client = window.google!.accounts.oauth2.initTokenClient({
      client_id: CLIENT_ID!,
      scope: 'https://www.googleapis.com/auth/drive.file',
      callback: r => {
        if (!r.access_token) { reject(new Error(r.error ?? 'Auth failed')); return }
        cachedToken = { value: r.access_token, expiresAt: Date.now() + (r.expires_in ?? 3600) * 1000 }
        resolve(r.access_token)
      },
    })
    // Must be called synchronously from a user gesture context — caller is responsible
    client.requestAccessToken()
  })
}

async function uploadToDrive(token: string, filename: string, buf: ArrayBuffer): Promise<string> {
  const meta = JSON.stringify({ name: filename, mimeType: 'application/vnd.google-apps.spreadsheet' })
  const form = new FormData()
  form.append('metadata', new Blob([meta], { type: 'application/json' }))
  form.append('file', new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' }))

  const res = await fetch(
    'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id',
    { method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: form },
  )
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`Drive upload failed (${res.status}): ${text}`)
  }
  const { id } = await res.json() as { id: string }
  return `https://docs.google.com/spreadsheets/d/${id}/edit`
}

export async function openInSheets(buf: ArrayBuffer, filename: string): Promise<void> {
  if (!CLIENT_ID) throw new Error('VITE_GOOGLE_CLIENT_ID is not configured')
  const token = await getAccessToken()
  const url = await uploadToDrive(token, filename, buf)
  window.open(url, '_blank', 'noopener')
}
