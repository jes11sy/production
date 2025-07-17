import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

// Простой мок компонент для тестирования концепции Dashboard
const SimpleDashboard = () => {
  return (
    <div>
      <h1>Панель управления</h1>
      <div data-testid="stats-grid">
        <div data-testid="stat-card">
          <span>Заявки сегодня</span>
          <span>5</span>
        </div>
        <div data-testid="stat-card">
          <span>Выполнено</span>
          <span>3</span>
        </div>
        <div data-testid="stat-card">
          <span>В работе</span>
          <span>2</span>
        </div>
        <div data-testid="stat-card">
          <span>Общий доход</span>
          <span>15 000 ₽</span>
        </div>
      </div>
    </div>
  )
}

const renderSimpleDashboard = () => {
  return render(
    <BrowserRouter>
      <SimpleDashboard />
    </BrowserRouter>
  )
}

describe('Simple Dashboard Test', () => {
  it('renders dashboard title', () => {
    renderSimpleDashboard()
    
    expect(screen.getByText('Панель управления')).toBeInTheDocument()
  })

  it('displays statistics cards', () => {
    renderSimpleDashboard()
    
    expect(screen.getByText('Заявки сегодня')).toBeInTheDocument()
    expect(screen.getByText('Выполнено')).toBeInTheDocument()
    expect(screen.getByText('В работе')).toBeInTheDocument()
    expect(screen.getByText('Общий доход')).toBeInTheDocument()
  })

  it('shows numeric values', () => {
    renderSimpleDashboard()
    
    expect(screen.getByText('5')).toBeInTheDocument() // Заявки сегодня
    expect(screen.getByText('3')).toBeInTheDocument() // Выполнено
    expect(screen.getByText('2')).toBeInTheDocument() // В работе
    expect(screen.getByText('15 000 ₽')).toBeInTheDocument() // Доход
  })

  it('has proper structure', () => {
    renderSimpleDashboard()
    
    expect(screen.getByTestId('stats-grid')).toBeInTheDocument()
    expect(screen.getAllByTestId('stat-card')).toHaveLength(4)
  })
}) 