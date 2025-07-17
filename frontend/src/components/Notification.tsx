import React, { useState, useEffect } from 'react';

export interface NotificationProps {
  type: 'success' | 'error' | 'warning' | 'info';
  message: string;
  duration?: number;
  onClose?: () => void;
}

export const Notification: React.FC<NotificationProps> = ({
  type,
  message,
  duration = 5000,
  onClose
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!isVisible) return null;

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✅';
      case 'error':
        return '❌';
      case 'warning':
        return '⚠️';
      case 'info':
        return 'ℹ️';
      default:
        return '';
    }
  };

  const getStyles = () => {
    const baseStyles = "fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 max-w-md min-w-72 flex items-center gap-3 animate-slide-in";
    
    switch (type) {
      case 'success':
        return `${baseStyles} bg-green-50 border border-green-200 text-green-800`;
      case 'error':
        return `${baseStyles} bg-red-50 border border-red-200 text-red-800`;
      case 'warning':
        return `${baseStyles} bg-yellow-50 border border-yellow-200 text-yellow-800`;
      case 'info':
        return `${baseStyles} bg-blue-50 border border-blue-200 text-blue-800`;
      default:
        return baseStyles;
    }
  };

  return (
    <div className={getStyles()}>
      <span className="text-lg">{getIcon()}</span>
      <span className="flex-1">{message}</span>
      <button
        onClick={() => {
          setIsVisible(false);
          onClose?.();
        }}
        className="text-gray-500 hover:text-gray-700 text-xl leading-none"
      >
        ×
      </button>
    </div>
  );
};

// Хук для управления уведомлениями
// eslint-disable-next-line react-refresh/only-export-components
export const useNotification = () => {
  const [notifications, setNotifications] = useState<Array<NotificationProps & { id: string }>>([]);

  const addNotification = (notification: Omit<NotificationProps, 'onClose'>) => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { ...notification, id, onClose: () => removeNotification(id) }]);
  };

  const removeNotification = (id: string) => {
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const showSuccess = (message: string, duration?: number) => {
    addNotification({ type: 'success', message, duration });
  };

  const showError = (message: string, duration?: number) => {
    addNotification({ type: 'error', message, duration });
  };

  const showWarning = (message: string, duration?: number) => {
    addNotification({ type: 'warning', message, duration });
  };

  const showInfo = (message: string, duration?: number) => {
    addNotification({ type: 'info', message, duration });
  };

  return {
    notifications,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    removeNotification
  };
};

// Компонент для отображения всех уведомлений
export const NotificationContainer: React.FC = () => {
  const { notifications, removeNotification } = useNotification();

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      {notifications.map((notification) => (
        <Notification
          key={notification.id}
          {...notification}
          onClose={() => removeNotification(notification.id)}
        />
      ))}
    </div>
  );
};

// CSS для анимации (добавить в index.css)
const styles = `
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
`;

// Экспорт стилей для добавления в CSS
// eslint-disable-next-line react-refresh/only-export-components
export const notificationStyles = styles; 