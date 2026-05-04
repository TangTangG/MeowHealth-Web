import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import PreventiveCare from '../PreventiveCare'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useOutletContext: () => ({ selectedCatId: 'test-cat-id' }),
  }
})

describe('PreventiveCare', () => {
  it('renders preventive care page with tabs', () => {
    render(<PreventiveCare />)
    expect(screen.getByText(/疫苗接种/i)).toBeInTheDocument()
    expect(screen.getByText(/驱虫记录/i)).toBeInTheDocument()
  })

  it('renders page title', () => {
    render(<PreventiveCare />)
    expect(screen.getByText('疫苗与驱虫')).toBeInTheDocument()
  })
})
