import { forwardRef, InputHTMLAttributes } from 'react'
import clsx from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="space-y-1.5">
        {label && (
          <label className="block text-sm font-medium text-dark-300">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={clsx(
            'w-full px-3 py-2 bg-dark-900 border rounded-lg text-dark-100',
            'placeholder:text-dark-500 focus:outline-none focus:ring-2',
            'transition-all duration-200',
            error
              ? 'border-red-500 focus:ring-red-500/20'
              : 'border-dark-700 focus:border-primary-500 focus:ring-primary-500/20',
            className
          )}
          {...props}
        />
        {error && (
          <p className="text-sm text-red-400">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input


