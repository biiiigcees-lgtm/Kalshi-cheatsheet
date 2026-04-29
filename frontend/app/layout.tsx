import type { Metadata } from 'next'
import './globals.css'
import { Header } from '@/components/Header'

export const metadata: Metadata = {
  title:       'BTC-Trustee Quant V3',
  description: 'Real-time AI signal engine for Kalshi KXBTC15M prediction markets',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="bg-black">
      <body className="min-h-screen bg-black text-bb-text font-mono antialiased">
        <Header />
        {/* Nav bar */}
        <nav className="border-b border-bb-border px-4">
          <div className="flex gap-0">
            {[
              { href: '/',        label: 'DASHBOARD' },
              { href: '/history', label: 'HISTORY'   },
              { href: '/diary',   label: 'DIARY'      },
            ].map(({ href, label }) => (
              <a
                key={href}
                href={href}
                className="px-4 py-2 text-xs text-bb-muted hover:text-bb-amber
                           border-b-2 border-transparent hover:border-bb-amber
                           transition-colors duration-100"
              >
                {label}
              </a>
            ))}
          </div>
        </nav>

        <main className="p-4 space-y-4">{children}</main>

        <footer className="mt-8 px-4 py-3 border-t border-bb-border text-bb-dim text-xs flex justify-between">
          <span>BTC-TRUSTEE QUANT V3 · KXBTC15M AI ENGINE</span>
          <span>BRTI settlement: 60-second CME CF mean</span>
        </footer>
      </body>
    </html>
  )
}
