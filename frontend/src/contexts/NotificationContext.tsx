import React, { createContext, useContext, useState } from 'react';
import type { ReactNode } from 'react';
import { Notification } from '../components/Notification';
import type { NotificationProps } from '../components/Notification';

interface NotificationContextType {
  showSuccess: (message: string, duration?: number) => void;
  showError: (message: string, duration?: number) => void;
  showWarning: (message: string, duration?: number) => void;
  showInfo: (message: string, duration?: number) => void;
}

const NotificationContext = createContext<NotificationContextType | undefined>(undefined);

// eslint-disable-next-line react-refresh/only-export-components
export const useNotification = () => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  return context;
};

interface NotificationProviderProps {
  children: ReactNode;
}

export const NotificationProvider: React.FC<NotificationProviderProps> = ({ children }) => {
  const [notifications, setNotifications] = useState<Array<NotificationProps & { id: string }>>([]);

  const addNotification = (notification: Omit<NotificationProps, 'onClose'>) => {
    const id = Date.now().toString();
    setNotifications(prev => [...prev, { 
      ...notification, 
      id, 
      onClose: () => removeNotification(id) 
    }]);
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

  return (
    <NotificationContext.Provider value={{
      showSuccess,
      showError,
      showWarning,
      showInfo
    }}>
      {children}
      
      {/* Контейнер для уведомлений */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map((notification) => (
          <Notification
            key={notification.id}
            {...notification}
            onClose={() => removeNotification(notification.id)}
          />
        ))}
      </div>
    </NotificationContext.Provider>
  );
}; 