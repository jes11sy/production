import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { Card, CardBody, Button } from '@heroui/react';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
  errorInfo?: ErrorInfo;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Здесь можно отправить ошибку в систему мониторинга
    // например, Sentry, LogRocket и т.д.
    this.logErrorToService(error, errorInfo);
    
    this.setState({
      error,
      errorInfo,
    });
  }

  private logErrorToService = (error: Error, errorInfo: ErrorInfo) => {
    // Логирование ошибки в внешний сервис
    const errorData = {
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent,
    };
    
    // Отправка в сервис мониторинга
    console.error('Error logged:', errorData);
  };

  private handleReload = () => {
    window.location.reload();
  };

  private handleReset = () => {
    this.setState({ hasError: false, error: undefined, errorInfo: undefined });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
          <Card className="max-w-md w-full">
            <CardBody className="text-center space-y-4">
              <ExclamationTriangleIcon className="h-16 w-16 text-red-500 mx-auto" />
              
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Произошла ошибка
                </h2>
                <p className="text-gray-600 text-sm">
                  К сожалению, что-то пошло не так. Попробуйте перезагрузить страницу или обратитесь к администратору.
                </p>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="text-left bg-gray-100 p-3 rounded text-xs">
                  <summary className="cursor-pointer font-medium text-red-600 mb-2">
                    Детали ошибки (только для разработки)
                  </summary>
                  <div className="space-y-2">
                    <div>
                      <strong>Сообщение:</strong>
                      <pre className="mt-1 text-red-600">{this.state.error.message}</pre>
                    </div>
                    {this.state.error.stack && (
                      <div>
                        <strong>Stack trace:</strong>
                        <pre className="mt-1 text-gray-600 overflow-auto max-h-32">
                          {this.state.error.stack}
                        </pre>
                      </div>
                    )}
                    {this.state.errorInfo?.componentStack && (
                      <div>
                        <strong>Component stack:</strong>
                        <pre className="mt-1 text-gray-600 overflow-auto max-h-32">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </div>
                    )}
                  </div>
                </details>
              )}

              <div className="flex gap-2 justify-center">
                <Button
                  color="primary"
                  startContent={<ArrowPathIcon className="h-4 w-4" />}
                  onClick={this.handleReset}
                >
                  Попробовать снова
                </Button>
                <Button
                  variant="bordered"
                  onClick={this.handleReload}
                >
                  Перезагрузить страницу
                </Button>
              </div>
            </CardBody>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}

// Хук для использования в функциональных компонентах
// eslint-disable-next-line react-refresh/only-export-components
export const useErrorHandler = () => {
  const handleError = (error: Error, errorInfo?: string) => {
    console.error('Error handled:', error, errorInfo);
    
    // Можно интегрировать с системой уведомлений
    // или отправить в сервис мониторинга
  };

  return { handleError };
};

// Компонент для обработки ошибок в конкретных секциях
interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
  title?: string;
  description?: string;
}

export const ErrorFallback: React.FC<ErrorFallbackProps> = ({
  error,
  resetError,
  title = 'Произошла ошибка',
  description = 'Не удалось загрузить данные. Попробуйте еще раз.',
}) => {
  return (
    <Card className="border-red-200 bg-red-50">
      <CardBody className="text-center space-y-3">
        <ExclamationTriangleIcon className="h-8 w-8 text-red-500 mx-auto" />
        <div>
          <h3 className="font-medium text-red-900">{title}</h3>
          <p className="text-sm text-red-700 mt-1">{description}</p>
        </div>
        
        {process.env.NODE_ENV === 'development' && (
          <details className="text-left bg-white p-2 rounded text-xs">
            <summary className="cursor-pointer text-red-600">
              Детали ошибки
            </summary>
            <pre className="mt-1 text-red-600 overflow-auto">
              {error.message}
            </pre>
          </details>
        )}
        
        <Button
          size="sm"
          color="danger"
          variant="bordered"
          onClick={resetError}
          startContent={<ArrowPathIcon className="h-4 w-4" />}
        >
          Попробовать снова
        </Button>
      </CardBody>
    </Card>
  );
}; 