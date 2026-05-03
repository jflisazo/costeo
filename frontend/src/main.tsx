import './index.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider, theme } from 'antd'
import esES from 'antd/locale/es_ES'
import App from './App'

const qc = new QueryClient({
  defaultOptions: { queries: { staleTime: 0, retry: 1 } },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={qc}>
      <ConfigProvider locale={esES} theme={{ algorithm: theme.defaultAlgorithm }}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
)
