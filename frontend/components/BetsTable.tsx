'use client'
import { useEffect, useState } from 'react'
import type { Bet } from '@/types'
import { fetchRecentBets } from '@/lib/supabase'

function utcShort(iso: string) {
  return new Date(iso).toUTCString().split(' ').slice(1, 5).join(' ').replace(':00 UTC', ' UTC')
}

interface Props { limit?: number }

// Demo rows shown when Supabase is not configured
const DEMO_BETS: Bet[] = [
  { id:'1', user_id:'demo', ticker:'KXBTC15M-SIM-014', bet_type:'YES', amount:50, outcome:'WIN',  payout:94,  floor_strike:94478, settlement_price:94590, created_at:'2025-04-01T03:15:00Z' },
  { id:'2', user_id:'demo', ticker:'KXBTC15M-SIM-022', bet_type:'NO',  amount:50, outcome:'WIN',  payout:91,  floor_strike:93135, settlement_price:92988, created_at:'2025-04-01T05:15:00Z' },
  { id:'3', user_id:'demo', ticker:'KXBTC15M-SIM-037', bet_type:'YES', amount:50, outcome:'WIN',  payout:89,  floor_strike:91267, settlement_price:91340, created_at:'2025-04-01T09:00:00Z' },
  { id:'4', user_id:'demo', ticker:'KXBTC15M-SIM-038', bet_type:'YES', amount:50, outcome:'WIN',  payout:92,  floor_strike:91254, settlement_price:91360, created_at:'2025-04-01T09:15:00Z' },
  { id:'5', user_id:'demo', ticker:'KXBTC15M-SIM-045', bet_type:'YES', amount:50, outcome:'WIN',  payout:98,  floor_strike:91485, settlement_price:91620, created_at:'2025-04-01T11:00:00Z' },
]

export function BetsTable({ limit = 20 }: Props) {
  const [bets, setBets] = useState<Bet[]>([])
  const [demo, setDemo] = useState(false)

  useEffect(() => {
    fetchRecentBets(limit)
      .then(rows => {
        if (rows.length > 0) setBets(rows)
        else { setBets(DEMO_BETS); setDemo(true) }
      })
      .catch(() => { setBets(DEMO_BETS); setDemo(true) })
  }, [limit])

  return (
    <div>
      {demo && (
        <div className="text-xs text-bb-dim mb-2 px-1">
          ⚠ Showing demo data — connect Supabase to see live bets
        </div>
      )}
      <table className="w-full text-xs">
        <thead>
          <tr className="bb-label border-b border-bb-border">
            <th className="text-left py-2 pr-4">TIME (UTC)</th>
            <th className="text-left pr-4">TICKER</th>
            <th className="text-left pr-4">SIGNAL</th>
            <th className="text-right pr-4">STRIKE</th>
            <th className="text-right pr-4">SETTLE</th>
            <th className="text-right">OUTCOME</th>
          </tr>
        </thead>
        <tbody>
          {bets.map(b => {
            const win = b.outcome === 'WIN'
            const pend = b.outcome === 'PENDING'
            return (
              <tr key={b.id} className="border-b border-bb-border hover:bg-bb-panel transition-colors">
                <td className="py-1.5 pr-4 text-bb-dim">{utcShort(b.created_at)}</td>
                <td className="pr-4 text-bb-text truncate max-w-[10rem]">{b.ticker}</td>
                <td className={`pr-4 font-semibold ${b.bet_type === 'YES' ? 'text-bb-green' : 'text-bb-red'}`}>
                  BET_{b.bet_type}
                </td>
                <td className="pr-4 text-right tabular-nums text-bb-text">
                  ${b.floor_strike.toLocaleString()}
                </td>
                <td className="pr-4 text-right tabular-nums text-bb-muted">
                  {b.settlement_price ? `$${b.settlement_price.toLocaleString()}` : '—'}
                </td>
                <td className={`text-right font-semibold ${pend ? 'text-bb-dim' : win ? 'text-bb-green' : 'text-bb-red'}`}>
                  {pend ? 'PENDING' : win ? `WIN +$${(b.payout ?? 0) - b.amount}` : `LOSS -$${b.amount}`}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
