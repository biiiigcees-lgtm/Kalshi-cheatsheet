import type { NextConfig } from 'next'

const config: NextConfig = {
  // Allow fetching live BTC prices from Binance in server components
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [{ key: 'X-Content-Type-Options', value: 'nosniff' }],
      },
    ]
  },
}

export default config
