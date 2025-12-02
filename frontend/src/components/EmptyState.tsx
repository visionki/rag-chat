import { ReactNode } from 'react'
import { LucideIcon } from 'lucide-react'

interface EmptyStateProps {
  icon: LucideIcon
  title: string
  description?: string
  action?: ReactNode
}

export default function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 px-4 text-center">
      <div className="w-16 h-16 rounded-2xl bg-dark-800 flex items-center justify-center mb-4">
        <Icon className="w-8 h-8 text-dark-500" />
      </div>
      <h3 className="text-lg font-medium text-dark-200 mb-1">{title}</h3>
      {description && (
        <p className="text-sm text-dark-500 mb-4 max-w-sm">{description}</p>
      )}
      {action}
    </div>
  )
}


