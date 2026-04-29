import { createClient } from '@supabase/supabase-js'

const url  = process.env.NEXT_PUBLIC_SUPABASE_URL  ?? ''
const akey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ?? ''

// Browser client (anon key, respects RLS)
export const supabase = createClient(url, akey)

// ── Typed query helpers ───────────────────────────────────────────────────────

export async function fetchRecentBets(limit = 20) {
  const { data, error } = await supabase
    .from('bets')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit)
  if (error) throw error
  return data ?? []
}

export async function fetchDiaryEntries(limit = 50) {
  const { data, error } = await supabase
    .from('diary')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(limit)
  if (error) throw error
  return data ?? []
}
