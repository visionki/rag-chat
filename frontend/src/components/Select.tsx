import { forwardRef, SelectHTMLAttributes } from 'react'
import clsx from 'clsx'

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  label?: string
  error?: string
  options: { value: string | number; label: string }[]
}

const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, label, error, options, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label className="block text-sm font-medium text-dark-300">
            {label}
          </label>
        )}
        <select
          ref={ref}
          className={clsx(
            'w-full px-3 py-2 bg-dark-900 border rounded-lg text-dark-100',
            'focus:outline-none focus:ring-2 transition-all duration-200',
            'appearance-none cursor-pointer',
            error
              ? 'border-red-500 focus:ring-red-500/20'
              : 'border-dark-700 focus:border-primary-500 focus:ring-primary-500/20',
            className
          )}
          style={{
            backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%236b7280'%3E%3Cpath stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M19 9l-7 7-7-7'%3E%3C/path%3E%3C/svg%3E")`,
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right 0.5rem center',
            backgroundSize: '1.5em 1.5em',
            paddingRight: '2.5rem',
          }}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    )
  }
)

Select.displayName = 'Select'

export default Select


