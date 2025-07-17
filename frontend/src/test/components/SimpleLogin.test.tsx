import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'

// Simple mock component for testing
const SimpleLogin = () => {
  return (
    <div>
      <h1>Авторизация</h1>
      <form>
        <label htmlFor="login">Логин</label>
        <input type="text" id="login" name="login" />
        
        <label htmlFor="password">Пароль</label>
        <input type="password" id="password" name="password" />
        
        <button type="submit">Войти</button>
      </form>
    </div>
  )
}

const renderSimpleLogin = () => {
  return render(
    <BrowserRouter>
      <SimpleLogin />
    </BrowserRouter>
  )
}

describe('Simple Login Test', () => {
  it('renders basic login form', () => {
    renderSimpleLogin()
    
    expect(screen.getByText('Авторизация')).toBeInTheDocument()
    expect(screen.getByLabelText('Логин')).toBeInTheDocument()
    expect(screen.getByLabelText('Пароль')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Войти' })).toBeInTheDocument()
  })

  it('has proper form structure', () => {
    renderSimpleLogin()
    
    const loginInput = screen.getByLabelText('Логин')
    const passwordInput = screen.getByLabelText('Пароль')
    
    expect(loginInput).toHaveAttribute('type', 'text')
    expect(passwordInput).toHaveAttribute('type', 'password')
  })
}) 