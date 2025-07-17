import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useNavigate, Navigate } from 'react-router-dom';
import { Button, Input, Card } from '@heroui/react';
import { UserIcon, EyeIcon, EyeSlashIcon, LockClosedIcon } from '@heroicons/react/24/outline';
import { useAuth } from '../contexts/AuthContext';
import logo from '../assets/logo.png';

const schema = z.object({
  login: z.string().min(1, 'Логин обязателен'),
  password: z.string().min(1, 'Пароль обязателен'),
});

type LoginForm = z.infer<typeof schema>;

export default function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isVisible, setIsVisible] = useState(false);

  const { register, handleSubmit, formState: { errors } } = useForm<LoginForm>({
    resolver: zodResolver(schema),
  });

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const onSubmit = async (data: LoginForm) => {
    setIsLoading(true);
    setError('');
    try {
      const user = await login(data.login, data.password);
      
      // Перенаправляем в зависимости от роли пользователя
      if (user.role === 'director' || user.role === 'callcenter') {
        navigate('/requests');
      } else {
        navigate('/');
      }
    } catch (err: unknown) {
      const errorMessage = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || 'Ошибка входа в систему';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-100 to-indigo-200 p-4">
      <Card className="w-full max-w-md rounded-3xl shadow-2xl border border-blue-100 bg-white/95 p-12 transition-shadow hover:shadow-3xl">
        <div className="flex flex-col items-center mt-2 mb-10">
          <img src={logo} alt="Логотип" className="h-44 w-44 object-contain mb-10" />
        </div>
        <form className="space-y-8" onSubmit={handleSubmit(onSubmit)}>
          <div>
            <label htmlFor="login" className="block text-lg font-bold text-gray-900 mb-3">Логин</label>
            <Input
              id="login"
              {...register('login')}
              startContent={<UserIcon className="h-5 w-5 text-gray-400" />}
              variant="bordered"
              isInvalid={!!errors.login}
              errorMessage={errors.login?.message}
              fullWidth
              size="lg"
              className="h-16 rounded-2xl text-lg transition focus:ring-2 focus:ring-blue-400"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-lg font-bold text-gray-900 mb-3">Пароль</label>
            <Input
              id="password"
              {...register('password')}
              type={isVisible ? 'text' : 'password'}
              startContent={<LockClosedIcon className="h-5 w-5 text-gray-400" />}
              endContent={
                <button type="button" tabIndex={-1} onClick={() => setIsVisible(v => !v)} className="focus:outline-none">
                  {isVisible ? (
                    <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                  ) : (
                    <EyeIcon className="h-5 w-5 text-gray-400" />
                  )}
                </button>
              }
              variant="bordered"
              isInvalid={!!errors.password}
              errorMessage={errors.password?.message}
              fullWidth
              size="lg"
              className="h-16 rounded-2xl text-lg transition focus:ring-2 focus:ring-blue-400"
            />
          </div>
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-center text-base">{error}</div>
          )}
          <Button
            type="submit"
            color="primary"
            size="lg"
            fullWidth
            isLoading={isLoading}
            className="mt-2 h-16 rounded-2xl text-lg font-bold transition hover:scale-105"
          >
            Войти
          </Button>
        </form>
      </Card>
    </div>
  );
} 