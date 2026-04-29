'use client'
import { useEffect, useState } from 'react'
import type { DiaryEntry } from '@/types'
import { fetchDiaryEntries } from '@/lib/supabase'

function utcShort(iso: string) {
  return new Date(iso).toUTCString().split(' ').slice(1, 5).join(' ').replace(':00 UTC', ' UTC')
}

const DEMO_DIARY: DiaryEntry[] = [
  { id:'1', user_id:'demo', ticker:'KXBTC15M-SIM-001', decision:'HOLD', shadow_prediction:'YES', confidence:0.45, reason_text:'neutral_38.3', created_at:'2025-04-01T00:00:00Z' },
  { id:'2', user_id:'demo', ticker:'KXBTC15M-SIM-002', decision:'HOLD', shadow_prediction:'NO',  confidence:0.40, reason_text:'neutral_43.5', created_at:'2025-04-01T00:15:00Z' },
  { id:'3', user_id:'demo', ticker:'KXBTC15M-SIM-005', decision:'HOLD', shadow_prediction:'YES', confidence:0.42, reason_text:'bullish_no_momentum_72.8', created_at:'2025-04-01T01:00:00Z' },
  { id:'4', user_id:'demo', ticker:'KXBTC15M-SIM-010', decision:'HOLD', shadow_prediction:'YES', confidence:0.50, reason_text:'low_conf_0.50', created_at:'2025-04-01T02:15:00Z' },
  { id:'5', user_id:'demo', ticker:'KXBTC15M-SIM-016', decision:'HOLD', shadow_prediction:'YES', confidence:0.54, reason_text:'low_conf_0.54', created_at:'2025-04-01T03:45:00Z' },
]

export function DiaryTable() {
  const [entries, setEntries] = useState<DiaryEntry[]>([])
  const [demo, setDemo] = useState(false)

  useEffect(() => {
    fetchDiaryEntries(50)
      .then(rows => {
        if (rows.length > 0) setEntries(rows)
        else { setEntries(DEMO_DIARY); setDemo(true) }
      })
      .catch(() => { setEntries(DEMO_DIARY); setDemo(true) })
  }, [])

  return (
    <div>
      {demo && (
        <div className="text-xs text-bb-dim mb-2">
          ⚠ Showing demo data — connect Supabase to see live diary
        </div>
      )}
      <table className="w-full text-xs">
        <thead>
          <tr className="bb-label border-b border-bb-border">
            <th className="text-left py-2 pr-4">TIME (UTC)</th>
            <th className="text-left pr-4">TICKER</th>
            <th className="text-left pr-4">SHADOW PRED</th>
            <th className="text-right pr-4">CONFIDENCE</th>
            <th className="text-left">REASON (AI)</th>
          </tr>
        </thead>
        <tbody>
          {entries.map(e => (
            <tr key={e.id} className="border-b border-bb-border hover:bg-bb-panel transition-colors">
              <td className="py-1.5 pr-4 text-bb-dim">{utcShort(e.created_at)}</td>
              <td className="pr-4 text-bb-text truncate max-w-[10rem]">{e.ticker}</td>
              <td className={`pr-4 font-semibold ${e.shadow_prediction === 'YES' ? 'text-bb-green/60' : 'text-bb-red/60'}`}>
                {e.shadow_prediction}
                <span className="text-bb-dim font-normal ml-1">(held)</span>
              </td>
              <td className="pr-4 text-right tabular-nums text-bb-yellow">
                {(e.confidence * 100).toFixed(1)}%
              </td>
              <td className="text-bb-dim truncate max-w-xs" title={e.reason_text}>
                {e.reason_text}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
