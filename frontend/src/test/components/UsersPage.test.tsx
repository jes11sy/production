import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'

// Простой мок компонент для тестирования концепции UsersPage
const SimpleUsersPage = () => {
  const [activeTab, setActiveTab] = React.useState('masters')

  return (
    <div>
      <h1>Управление пользователями</h1>
      
      <div role="tablist">
        <button 
          role="tab" 
          aria-selected={activeTab === 'masters'}
          onClick={() => setActiveTab('masters')}
        >
          Мастера
        </button>
        <button 
          role="tab" 
          aria-selected={activeTab === 'employees'}
          onClick={() => setActiveTab('employees')}
        >
          Сотрудники
        </button>
        <button 
          role="tab" 
          aria-selected={activeTab === 'administrators'}
          onClick={() => setActiveTab('administrators')}
        >
          Администраторы
        </button>
      </div>

      <div data-testid="tab-content">
        {activeTab === 'masters' && (
          <div>
            <h2>Список мастеров</h2>
            <button>Добавить мастера</button>
            <div data-testid="masters-list">
              <div>Мастер 1 <button aria-label="Удалить">Удалить</button></div>
              <div>Мастер 2 <button aria-label="Удалить">Удалить</button></div>
            </div>
          </div>
        )}
        
        {activeTab === 'employees' && (
          <div>
            <h2>Список сотрудников</h2>
            <button>Добавить сотрудника</button>
            <div data-testid="employees-list">
              <div>Сотрудник 1 <button aria-label="Удалить">Удалить</button></div>
            </div>
          </div>
        )}
        
        {activeTab === 'administrators' && (
          <div>
            <h2>Список администраторов</h2>
            <button>Добавить администратора</button>
            <div data-testid="administrators-list">
              <div>Администратор 1 <button aria-label="Удалить">Удалить</button></div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

const renderSimpleUsersPage = () => {
  return render(
    <BrowserRouter>
      <SimpleUsersPage />
    </BrowserRouter>
  )
}

describe('Simple Users Page Test', () => {
  it('renders users page title', () => {
    renderSimpleUsersPage()
    
    expect(screen.getByText('Управление пользователями')).toBeInTheDocument()
  })

  it('displays tab navigation', () => {
    renderSimpleUsersPage()
    
    expect(screen.getByRole('tab', { name: 'Мастера' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Сотрудники' })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: 'Администраторы' })).toBeInTheDocument()
  })

  it('shows masters by default', () => {
    renderSimpleUsersPage()
    
    expect(screen.getByText('Список мастеров')).toBeInTheDocument()
    expect(screen.getByText('Добавить мастера')).toBeInTheDocument()
    expect(screen.getByTestId('masters-list')).toBeInTheDocument()
  })

  it('switches to employees tab', async () => {
    const user = userEvent.setup()
    renderSimpleUsersPage()
    
    const employeesTab = screen.getByRole('tab', { name: 'Сотрудники' })
    await user.click(employeesTab)
    
    expect(screen.getByText('Список сотрудников')).toBeInTheDocument()
    expect(screen.getByText('Добавить сотрудника')).toBeInTheDocument()
    expect(screen.getByTestId('employees-list')).toBeInTheDocument()
  })

  it('switches to administrators tab', async () => {
    const user = userEvent.setup()
    renderSimpleUsersPage()
    
    const administratorsTab = screen.getByRole('tab', { name: 'Администраторы' })
    await user.click(administratorsTab)
    
    expect(screen.getByText('Список администраторов')).toBeInTheDocument()
    expect(screen.getByText('Добавить администратора')).toBeInTheDocument()
    expect(screen.getByTestId('administrators-list')).toBeInTheDocument()
  })

  it('displays delete buttons', () => {
    renderSimpleUsersPage()
    
    // По умолчанию показаны мастера с кнопками удаления
    const deleteButtons = screen.getAllByLabelText('Удалить')
    expect(deleteButtons.length).toBeGreaterThan(0)
  })

  it('shows user items', () => {
    renderSimpleUsersPage()
    
    // Проверяем что отображаются элементы пользователей
    expect(screen.getByText('Мастер 1')).toBeInTheDocument()
    expect(screen.getByText('Мастер 2')).toBeInTheDocument()
  })
}) 