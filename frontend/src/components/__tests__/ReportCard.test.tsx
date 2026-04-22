import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ReportCard } from '../ReportCard'

describe('ReportCard', () => {
  const mockIndicators = [
    {
      id: '1',
      name: 'WBC',
      display_name: '白细胞',
      value: 12.5,
      unit: '10^9/L',
      reference_min: 5.5,
      reference_max: 19.5,
      is_abnormal: false,
      explanation: '正常'
    },
    {
      id: '2',
      name: 'CREA',
      display_name: '肌酐',
      value: 2.5,
      unit: 'mg/dL',
      reference_min: 0.8,
      reference_max: 2.4,
      is_abnormal: true,
      explanation: '偏高'
    }
  ]

  it('renders report title and date', () => {
    render(
      <ReportCard
        title="血常规检查"
        date="2024-01-15"
        summary="整体正常"
        indicators={mockIndicators}
        recommendations={["多饮水"]}
      />
    )

    expect(screen.getByText('血常规检查')).toBeInTheDocument()
    expect(screen.getByText('整体正常')).toBeInTheDocument()
  })

  it('highlights abnormal indicators', () => {
    render(
      <ReportCard
        title="血常规检查"
        date="2024-01-15"
        summary="整体正常"
        indicators={mockIndicators}
        recommendations={["多饮水"]}
      />
    )

    const abnormalIndicator = screen.getByText('肌酐')
    expect(abnormalIndicator).toBeInTheDocument()
  })

  it('displays recommendations', () => {
    render(
      <ReportCard
        title="血常规检查"
        date="2024-01-15"
        summary="整体正常"
        indicators={mockIndicators}
        recommendations={["多饮水", "定期复查"]}
      />
    )

    expect(screen.getByText('多饮水')).toBeInTheDocument()
    expect(screen.getByText('定期复查')).toBeInTheDocument()
  })
})
