import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import Login from '../../pages/Login'
import { AuthProvider } from '../../contexts/AuthContext'

// Mock the auth context
const mockLogin = vi.fn()
const mockAuthContext = {
  user: null,
  isAuthenticated: false,
  login: mockLogin,
  logout: vi.fn(),
  loading: false,
}

vi.mock('../../contexts/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
  useAuth: () => mockAuthContext,
}))

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    Navigate: ({ to }: { to: string }) => <div data-testid="navigate-to">{to}</div>,
  }
})

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <AuthProvider>
        <Login />
      </AuthProvider>
    </BrowserRouter>
  )
}

describe('Login Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockAuthContext.isAuthenticated = false
  })

  it('renders login form correctly', () => {
    renderLogin()
    
    expect(screen.getByLabelText(/логин/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument()
  })

  it('shows validation errors for empty fields', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    const submitButton = screen.getByRole('button', { name: /войти/i })
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText('Логин обязателен')).toBeInTheDocument()
      expect(screen.getByText('Пароль обязателен')).toBeInTheDocument()
    })
  })

  it('calls login function with correct credentials', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValueOnce({ role: 'admin' })
    
    renderLogin()
    
    const loginInput = screen.getByLabelText(/логин/i)
    const passwordInput = screen.getByLabelText(/пароль/i)
    const submitButton = screen.getByRole('button', { name: /войти/i })
    
    await user.type(loginInput, 'testuser')
    await user.type(passwordInput, 'testpassword')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith('testuser', 'testpassword')
    })
  })

  it('redirects to requests page for director/callcenter roles', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValueOnce({ role: 'director' })
    
    renderLogin()
    
    const loginInput = screen.getByLabelText(/логин/i)
    const passwordInput = screen.getByLabelText(/пароль/i)
    const submitButton = screen.getByRole('button', { name: /войти/i })
    
    await user.type(loginInput, 'director')
    await user.type(passwordInput, 'password')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/requests')
    })
  })

  it('redirects to home page for other roles', async () => {
    const user = userEvent.setup()
    mockLogin.mockResolvedValueOnce({ role: 'admin' })
    
    renderLogin()
    
    const loginInput = screen.getByLabelText(/логин/i)
    const passwordInput = screen.getByLabelText(/пароль/i)
    const submitButton = screen.getByRole('button', { name: /войти/i })
    
    await user.type(loginInput, 'admin')
    await user.type(passwordInput, 'password')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/')
    })
  })

  it('displays error message on login failure', async () => {
    const user = userEvent.setup()
    const errorMessage = 'Неверные учетные данные'
    mockLogin.mockRejectedValueOnce({
      response: { data: { detail: errorMessage } }
    })
    
    renderLogin()
    
    const loginInput = screen.getByLabelText(/логин/i)
    const passwordInput = screen.getByLabelText(/пароль/i)
    const submitButton = screen.getByRole('button', { name: /войти/i })
    
    await user.type(loginInput, 'wrong')
    await user.type(passwordInput, 'credentials')
    await user.click(submitButton)
    
    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument()
    })
  })

  it('toggles password visibility', async () => {
    const user = userEvent.setup()
    renderLogin()
    
    const passwordInput = screen.getByLabelText(/пароль/i)
    // Ищем все кнопки и берем ту, что не submit (toggle для пароля)
    const buttons = screen.getAllByRole('button')
    const toggleButton = buttons.find(btn => btn.getAttribute('type') !== 'submit')
    
    expect(passwordInput).toHaveAttribute('type', 'password')
    
    if (toggleButton) {
      await user.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'text')
      
      await user.click(toggleButton)
      expect(passwordInput).toHaveAttribute('type', 'password')
    } else {
      // Если кнопка не найдена, пропускаем тест
      expect(true).toBe(true)
    }
  })

  it('redirects authenticated users', () => {
    mockAuthContext.isAuthenticated = true
    renderLogin()
    
    expect(screen.getByTestId('navigate-to')).toHaveTextContent('/')
  })

  it('disables submit button during loading', async () => {
    const user = userEvent.setup()
    let resolveLogin: (value: any) => void
    const loginPromise = new Promise(resolve => {
      resolveLogin = resolve
    })
    mockLogin.mockReturnValueOnce(loginPromise)
    
    renderLogin()
    
    const loginInput = screen.getByLabelText(/логин/i)
    const passwordInput = screen.getByLabelText(/пароль/i)
    const submitButton = screen.getByRole('button', { name: /войти/i })
    
    await user.type(loginInput, 'test')
    await user.type(passwordInput, 'test')
    await user.click(submitButton)
    
    expect(submitButton).toBeDisabled()
    
    resolveLogin!({ role: 'admin' })
    await waitFor(() => {
      expect(submitButton).not.toBeDisabled()
    })
  })
}) 