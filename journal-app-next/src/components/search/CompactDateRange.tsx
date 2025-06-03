'use client';

import { useState } from 'react';
import { Calendar, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

interface CompactDateRangeProps {
  startDate: string;
  endDate: string;
  onStartDateChange: (date: string) => void;
  onEndDateChange: (date: string) => void;
  className?: string;
}

export function CompactDateRange({
  startDate,
  endDate,
  onStartDateChange,
  onEndDateChange,
  className,
}: CompactDateRangeProps) {
  const [dateMode, setDateMode] = useState<'preset' | 'custom'>('preset');

  const hasDateFilter = startDate || endDate;

  const clearDates = () => {
    onStartDateChange('');
    onEndDateChange('');
  };

  const setPresetRange = (days: number) => {
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - days);

    onStartDateChange(start.toISOString().split('T')[0]);
    onEndDateChange(end.toISOString().split('T')[0]);
  };

  const presetOptions = [
    { label: 'Last 7 days', days: 7 },
    { label: 'Last 30 days', days: 30 },
    { label: 'Last 90 days', days: 90 },
    { label: 'This year', days: new Date().getDayOfYear() },
  ];

  return (
    <div className={cn('space-y-3', className)}>
      {/* Date filter summary */}
      {hasDateFilter && (
        <div className="flex items-center justify-between p-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md">
          <div className="flex items-center gap-2">
            <Calendar className="h-4 w-4 text-blue-600 dark:text-blue-400" />
            <span className="text-sm text-blue-700 dark:text-blue-300">
              {startDate && endDate ? (
                `${new Date(startDate).toLocaleDateString()} - ${new Date(endDate).toLocaleDateString()}`
              ) : startDate ? (
                `From ${new Date(startDate).toLocaleDateString()}`
              ) : (
                `Until ${new Date(endDate).toLocaleDateString()}`
              )}
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={clearDates}
            className="h-6 w-6 p-0 text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      )}

      {/* Mode toggle */}
      <div className="flex bg-gray-100 dark:bg-gray-800 rounded-md p-1">
        <button
          type="button"
          onClick={() => setDateMode('preset')}
          className={cn(
            'flex-1 px-3 py-1.5 text-xs rounded transition-colors',
            dateMode === 'preset'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
          )}
        >
          Quick Select
        </button>
        <button
          type="button"
          onClick={() => setDateMode('custom')}
          className={cn(
            'flex-1 px-3 py-1.5 text-xs rounded transition-colors',
            dateMode === 'custom'
              ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
          )}
        >
          Custom Range
        </button>
      </div>

      {/* Content based on mode */}
      {dateMode === 'preset' ? (
        <div className="grid grid-cols-2 gap-2">
          {presetOptions.map((option) => (
            <button
              key={option.label}
              type="button"
              onClick={() => setPresetRange(option.days)}
              className="px-3 py-2 text-xs text-left bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 border border-gray-200 dark:border-gray-700 rounded-md transition-colors"
            >
              {option.label}
            </button>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              From
            </label>
            <Input
              type="date"
              value={startDate}
              onChange={(e) => onStartDateChange(e.target.value)}
              className="h-8 text-sm"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
              To
            </label>
            <Input
              type="date"
              value={endDate}
              onChange={(e) => onEndDateChange(e.target.value)}
              className="h-8 text-sm"
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Utility function to calculate day of year
declare global {
  interface Date {
    getDayOfYear(): number;
  }
}

Date.prototype.getDayOfYear = function() {
  const start = new Date(this.getFullYear(), 0, 0);
  const diff = this.getTime() - start.getTime();
  const oneDay = 1000 * 60 * 60 * 24;
  return Math.floor(diff / oneDay);
};
