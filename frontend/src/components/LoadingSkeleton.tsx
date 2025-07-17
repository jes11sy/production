import React from 'react';
import { Card, Skeleton } from '@heroui/react';

interface LoadingSkeletonProps {
  className?: string;
}

// Базовый компонент skeleton
export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ className = '' }) => (
  <div className={`animate-pulse ${className}`}>
    <div className="bg-gray-200 rounded h-4 w-full"></div>
  </div>
);

// Skeleton для таблицы
export const TableSkeleton: React.FC<{ rows?: number; columns?: number }> = ({ 
  rows = 5, 
  columns = 4 
}) => (
  <Card className="p-4">
    <div className="space-y-4">
      {/* Заголовок таблицы */}
      <div className="flex justify-between items-center">
        <Skeleton className="h-6 w-32 rounded" />
        <Skeleton className="h-10 w-24 rounded" />
      </div>
      
      {/* Заголовки колонок */}
      <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
        {Array.from({ length: columns }).map((_, index) => (
          <Skeleton key={index} className="h-4 w-full rounded" />
        ))}
      </div>
      
      {/* Строки таблицы */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton key={colIndex} className="h-4 w-full rounded" />
          ))}
        </div>
      ))}
    </div>
  </Card>
);

// Skeleton для карточки
export const CardSkeleton: React.FC<{ showAvatar?: boolean }> = ({ showAvatar = false }) => (
  <Card className="p-4">
    <div className="space-y-4">
      {showAvatar && (
        <div className="flex items-center space-x-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-4 w-32 rounded" />
            <Skeleton className="h-3 w-24 rounded" />
          </div>
        </div>
      )}
      <div className="space-y-2">
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-3/4 rounded" />
        <Skeleton className="h-4 w-1/2 rounded" />
      </div>
    </div>
  </Card>
);

// Skeleton для формы
export const FormSkeleton: React.FC<{ fields?: number }> = ({ fields = 4 }) => (
  <Card className="p-6">
    <div className="space-y-6">
      {/* Заголовок формы */}
      <div className="space-y-2">
        <Skeleton className="h-6 w-48 rounded" />
        <Skeleton className="h-4 w-64 rounded" />
      </div>
      
      {/* Поля формы */}
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index} className="space-y-2">
          <Skeleton className="h-4 w-24 rounded" />
          <Skeleton className="h-10 w-full rounded" />
        </div>
      ))}
      
      {/* Кнопки */}
      <div className="flex gap-2 pt-4">
        <Skeleton className="h-10 w-24 rounded" />
        <Skeleton className="h-10 w-20 rounded" />
      </div>
    </div>
  </Card>
);

// Skeleton для списка
export const ListSkeleton: React.FC<{ items?: number; showAvatar?: boolean }> = ({ 
  items = 5, 
  showAvatar = false 
}) => (
  <div className="space-y-4">
    {Array.from({ length: items }).map((_, index) => (
      <Card key={index} className="p-4">
        <div className="flex items-center space-x-4">
          {showAvatar && <Skeleton className="h-10 w-10 rounded-full" />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-3/4 rounded" />
            <Skeleton className="h-3 w-1/2 rounded" />
          </div>
          <Skeleton className="h-8 w-16 rounded" />
        </div>
      </Card>
    ))}
  </div>
);

// Skeleton для дашборда
export const DashboardSkeleton: React.FC = () => (
  <div className="space-y-6">
    {/* Заголовок */}
    <div className="space-y-2">
      <Skeleton className="h-8 w-48 rounded" />
      <Skeleton className="h-4 w-64 rounded" />
    </div>
    
    {/* Статистические карточки */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <Card key={index} className="p-4">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24 rounded" />
            <Skeleton className="h-6 w-16 rounded" />
            <Skeleton className="h-3 w-20 rounded" />
          </div>
        </Card>
      ))}
    </div>
    
    {/* Основной контент */}
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="p-4">
        <div className="space-y-4">
          <Skeleton className="h-5 w-32 rounded" />
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="flex justify-between items-center">
                <Skeleton className="h-4 w-24 rounded" />
                <Skeleton className="h-4 w-16 rounded" />
              </div>
            ))}
          </div>
        </div>
      </Card>
      
      <Card className="p-4">
        <div className="space-y-4">
          <Skeleton className="h-5 w-32 rounded" />
          <Skeleton className="h-32 w-full rounded" />
        </div>
      </Card>
    </div>
  </div>
);

// Skeleton для страницы профиля
export const ProfileSkeleton: React.FC = () => (
  <div className="space-y-6">
    <Card className="p-6">
      <div className="flex items-center space-x-6">
        <Skeleton className="h-24 w-24 rounded-full" />
        <div className="space-y-2">
          <Skeleton className="h-6 w-48 rounded" />
          <Skeleton className="h-4 w-32 rounded" />
          <Skeleton className="h-4 w-40 rounded" />
        </div>
      </div>
    </Card>
    
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card className="p-6">
        <div className="space-y-4">
          <Skeleton className="h-5 w-32 rounded" />
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <div key={index} className="space-y-1">
                <Skeleton className="h-4 w-20 rounded" />
                <Skeleton className="h-8 w-full rounded" />
              </div>
            ))}
          </div>
        </div>
      </Card>
      
      <Card className="p-6">
        <div className="space-y-4">
          <Skeleton className="h-5 w-32 rounded" />
          <div className="space-y-2">
            {Array.from({ length: 6 }).map((_, index) => (
              <div key={index} className="flex justify-between items-center">
                <Skeleton className="h-4 w-32 rounded" />
                <Skeleton className="h-4 w-24 rounded" />
              </div>
            ))}
          </div>
        </div>
      </Card>
    </div>
  </div>
);

// Skeleton для модального окна
export const ModalSkeleton: React.FC<{ title?: boolean; content?: boolean; actions?: boolean }> = ({ 
  title = true, 
  content = true, 
  actions = true 
}) => (
  <div className="space-y-4">
    {title && <Skeleton className="h-6 w-48 rounded" />}
    {content && (
      <div className="space-y-3">
        <Skeleton className="h-4 w-full rounded" />
        <Skeleton className="h-4 w-3/4 rounded" />
        <Skeleton className="h-4 w-1/2 rounded" />
      </div>
    )}
    {actions && (
      <div className="flex gap-2 pt-4">
        <Skeleton className="h-10 w-20 rounded" />
        <Skeleton className="h-10 w-24 rounded" />
      </div>
    )}
  </div>
);

// Хук для управления skeleton loading
// eslint-disable-next-line react-refresh/only-export-components
export const useSkeletonLoading = (loading: boolean, delay: number = 300) => {
  const [showSkeleton, setShowSkeleton] = React.useState(false);

  React.useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (loading) {
      timer = setTimeout(() => {
        setShowSkeleton(true);
      }, delay);
    } else {
      setShowSkeleton(false);
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [loading, delay]);

  return showSkeleton;
};

// Wrapper компонент для автоматического skeleton
export const SkeletonWrapper: React.FC<{
  loading: boolean;
  skeleton: React.ReactNode;
  children: React.ReactNode;
  delay?: number;
}> = ({ loading, skeleton, children, delay = 300 }) => {
  const showSkeleton = useSkeletonLoading(loading, delay);
  
  if (showSkeleton) {
    return <>{skeleton}</>;
  }
  
  return <>{children}</>;
}; 