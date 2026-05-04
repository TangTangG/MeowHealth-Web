import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import Analytics from '../Analytics'

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useOutletContext: () => ({ selectedCatId: 'test-cat-id' }),
  }
})

// Mock API calls
vi.mock('@/lib/api', () => ({
  getIndicatorNames: vi.fn().mockResolvedValue([
    { name: 'WBC', display_name: '白细胞' },
    { name: 'RBC', display_name: '红细胞' },
  ]),
  getWeightLogs: vi.fn().mockResolvedValue([]),
  getHealthScoreHistory: vi.fn().mockResolvedValue({ data: [] }),
  getIndicatorHistory: vi.fn().mockResolvedValue([]),
}))

// Mock chart components to avoid recharts rendering issues in jsdom
vi.mock('@/components/WeightChart', () => ({
  default: () => <div data-testid="weight-chart">体重图表</div>,
}))

vi.mock('@/components/HealthScoreChart', () => ({
  default: () => <div data-testid="health-score-chart">健康评分图表</div>,
}))

vi.mock('@/components/IndicatorChart', () => ({
  default: () => <div data-testid="indicator-chart">指标图表</div>,
}))

describe('Analytics', () => {
  it('renders analytics page with title and sections', async () => {
    render(<Analytics />)

    // Page title
    expect(await screen.findByText('数据洞察')).toBeInTheDocument()

    // Section headers
    expect(screen.getByText('体重趋势 (90天)')).toBeInTheDocument()
    expect(screen.getByText('健康评分趋势 (180天)')).toBeInTheDocument()
    expect(screen.getByText('化验指标历史对比')).toBeInTheDocument()

    // Indicator dropdown
    expect(screen.getByText('白细胞')).toBeInTheDocument()
  })
})
