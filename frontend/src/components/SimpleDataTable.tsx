import React, { useCallback } from 'react';
import {
  Table,
  TableHeader,
  TableColumn,
  TableBody,
  TableRow,
  TableCell,
  Spinner,
  Card,
  Button,
  Chip
} from '@heroui/react';
import { PlusIcon } from '@heroicons/react/24/outline';

export interface SimpleTableColumn<T = Record<string, unknown>> {
  key: string;
  label: string;
  render?: (value: unknown, item: T) => React.ReactNode;
}

export interface SimpleDataTableProps<T = Record<string, unknown>> {
  data: T[];
  columns: SimpleTableColumn<T>[];
  loading?: boolean;
  title?: string;
  subtitle?: string;
  onRowClick?: (item: T) => void;
  createAction?: {
    label: string;
    onClick: () => void;
  };
  emptyContent?: string;
  className?: string;
}

export const SimpleDataTable = <T extends Record<string, unknown>>({
  data,
  columns,
  loading = false,
  title,
  subtitle,
  onRowClick,
  createAction,
  emptyContent = 'Нет данных',
  className = ''
}: SimpleDataTableProps<T>) => {
  
  // Функция для получения значения по ключу
  const getValue = useCallback((item: T, key: string) => {
    return key.split('.').reduce((obj: unknown, k: string) => 
      (obj as Record<string, unknown>)?.[k], item);
  }, []);
  
  // Рендер заголовка
  const renderHeader = () => {
    if (!title && !createAction) return null;
    
    return (
      <div className="flex justify-between items-center mb-4 px-4 pt-4">
        <div>
          {title && <h2 className="text-xl font-semibold text-gray-900">{title}</h2>}
          {subtitle && <p className="text-sm text-gray-600 mt-1">{subtitle}</p>}
        </div>
        {createAction && (
          <Button
            color="primary"
            onClick={createAction.onClick}
            startContent={<PlusIcon className="w-4 h-4" />}
          >
            {createAction.label}
          </Button>
        )}
      </div>
    );
  };
  
  // Рендер ячейки
  const renderCell = useCallback((item: T, column: SimpleTableColumn<T>) => {
    const value = getValue(item, column.key);
    
    if (column.render) {
      return column.render(value, item);
    }
    
    if (value === null || value === undefined) {
      return <span className="text-gray-400">—</span>;
    }
    
    if (typeof value === 'boolean') {
      return (
        <Chip
          color={value ? 'success' : 'danger'}
          variant="flat"
          size="sm"
        >
          {value ? 'Да' : 'Нет'}
        </Chip>
      );
    }
    
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    
    if (value instanceof Date) {
      return value.toLocaleDateString();
    }
    
    return String(value);
  }, [getValue]);
  
  // Обработчик клика по строке
  const handleRowClick = useCallback((item: T) => {
    if (onRowClick) {
      onRowClick(item);
    }
  }, [onRowClick]);
  
  return (
    <Card className={className}>
      {renderHeader()}
      
      <div className="px-4 pb-4">
        <Table 
          aria-label={title || 'Таблица данных'}
          className={onRowClick ? 'cursor-pointer' : ''}
        >
          <TableHeader>
            {columns.map((column) => (
              <TableColumn key={column.key}>
                {column.label}
              </TableColumn>
            ))}
          </TableHeader>
          
          <TableBody
            items={data}
            isLoading={loading}
            loadingContent={<Spinner label="Загрузка..." />}
            emptyContent={emptyContent}
          >
            {(item) => (
              <TableRow 
                key={(item as { id?: number | string }).id || Math.random()}
                className={onRowClick ? 'cursor-pointer hover:bg-gray-50' : ''}
                onClick={() => handleRowClick(item)}
              >
                {columns.map((column) => (
                  <TableCell key={column.key}>
                    {renderCell(item, column)}
                  </TableCell>
                ))}
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}; 