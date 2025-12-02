import { Outlet, NavLink } from 'react-router-dom'
import { MessageSquare, FileText, Settings, Bot, ScrollText, Search } from 'lucide-react'
import clsx from 'clsx'

const navItems = [
  { to: '/chat', icon: MessageSquare, label: '问答' },
  { to: '/chatbots', icon: Bot, label: '机器人' },
  { to: '/documents', icon: FileText, label: '文档' },
  { to: '/search-test', icon: Search, label: '检索测试' },
  { to: '/logs', icon: ScrollText, label: '日志' },
  { to: '/settings', icon: Settings, label: '设置' },
]

export default function Layout() {
  return (
    <div className="flex h-screen bg-dark-950">
      {/* 侧边栏 */}
      <aside className="w-16 bg-dark-900 border-r border-dark-800 flex flex-col items-center py-4">
        {/* Logo */}
        <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-primary-700 rounded-xl flex items-center justify-center mb-8">
          <span className="text-white font-bold text-lg">Q</span>
        </div>
        
        {/* 导航 */}
        <nav className="flex-1 flex flex-col gap-2">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                clsx(
                  'w-12 h-12 rounded-xl flex items-center justify-center transition-all duration-200',
                  'hover:bg-dark-800 group relative',
                  isActive
                    ? 'bg-primary-500/20 text-primary-400'
                    : 'text-dark-400 hover:text-dark-200'
                )
              }
            >
              <item.icon className="w-5 h-5" />
              {/* Tooltip */}
              <span className="absolute left-full ml-2 px-2 py-1 bg-dark-800 text-dark-200 text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
                {item.label}
              </span>
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}

