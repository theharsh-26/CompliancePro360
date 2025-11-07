'use client'

import { useEffect, useState } from 'react'
import { 
  TrendingUp, 
  TrendingDown, 
  Building2, 
  CheckCircle2, 
  AlertTriangle,
  Clock
} from 'lucide-react'

interface DashboardStats {
  totalCompanies: number
  pendingTasks: number
  completedTasks: number
  overdueTask: number
  averageComplianceScore: number
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats>({
    totalCompanies: 0,
    pendingTasks: 0,
    completedTasks: 0,
    overdueTask: 0,
    averageComplianceScore: 0
  })

  useEffect(() => {
    // Fetch dashboard stats from API
    // For now, using mock data
    setStats({
      totalCompanies: 45,
      pendingTasks: 23,
      completedTasks: 156,
      overdueTask: 5,
      averageComplianceScore: 87
    })
  }, [])

  const statCards = [
    {
      title: 'Total Companies',
      value: stats.totalCompanies,
      icon: Building2,
      change: '+12%',
      changeType: 'positive' as const,
      color: 'bg-blue-500'
    },
    {
      title: 'Pending Tasks',
      value: stats.pendingTasks,
      icon: Clock,
      change: '-8%',
      changeType: 'positive' as const,
      color: 'bg-orange-500'
    },
    {
      title: 'Completed Tasks',
      value: stats.completedTasks,
      icon: CheckCircle2,
      change: '+23%',
      changeType: 'positive' as const,
      color: 'bg-green-500'
    },
    {
      title: 'Overdue Tasks',
      value: stats.overdueTask,
      icon: AlertTriangle,
      change: '+2',
      changeType: 'negative' as const,
      color: 'bg-red-500'
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="text-gray-600 mt-1">Welcome back! Here's your compliance overview.</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => (
          <div key={stat.title} className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">{stat.title}</p>
                <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                <div className="flex items-center gap-1 mt-2">
                  {stat.changeType === 'positive' ? (
                    <TrendingUp className="w-4 h-4 text-green-600" />
                  ) : (
                    <TrendingDown className="w-4 h-4 text-red-600" />
                  )}
                  <span className={`text-sm font-medium ${
                    stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {stat.change}
                  </span>
                  <span className="text-sm text-gray-500">vs last month</span>
                </div>
              </div>
              <div className={`w-12 h-12 ${stat.color} rounded-lg flex items-center justify-center`}>
                <stat.icon className="w-6 h-6 text-white" />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Compliance Score */}
      <div className="card">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Average Compliance Score</h2>
        <div className="flex items-center gap-6">
          <div className="relative w-32 h-32">
            <svg className="w-full h-full transform -rotate-90">
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="#e5e7eb"
                strokeWidth="12"
                fill="none"
              />
              <circle
                cx="64"
                cy="64"
                r="56"
                stroke="#3b82f6"
                strokeWidth="12"
                fill="none"
                strokeDasharray={`${2 * Math.PI * 56}`}
                strokeDashoffset={`${2 * Math.PI * 56 * (1 - stats.averageComplianceScore / 100)}`}
                strokeLinecap="round"
              />
            </svg>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-3xl font-bold text-gray-900">{stats.averageComplianceScore}%</span>
            </div>
          </div>
          <div className="flex-1">
            <p className="text-gray-600">
              Your companies are maintaining a good compliance score. Keep up the excellent work!
            </p>
            <div className="mt-4 space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Excellent (90-100)</span>
                <span className="font-medium text-green-600">15 companies</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Good (70-89)</span>
                <span className="font-medium text-blue-600">20 companies</span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">Needs Attention (&lt;70)</span>
                <span className="font-medium text-orange-600">10 companies</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Tasks & Upcoming Deadlines */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tasks */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Recent Tasks</h2>
          <div className="space-y-3">
            {[
              { company: 'Tech Innovations Pvt Ltd', task: 'GSTR-3B Filing', dueDate: '2025-11-20', status: 'pending' },
              { company: 'Global Solutions Inc', task: 'TDS Return Q2', dueDate: '2025-11-15', status: 'completed' },
              { company: 'Smart Systems Ltd', task: 'Form 24Q', dueDate: '2025-11-25', status: 'pending' },
            ].map((task, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{task.task}</p>
                  <p className="text-sm text-gray-600">{task.company}</p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600">{task.dueDate}</p>
                  <span className={`badge ${task.status === 'completed' ? 'badge-success' : 'badge-warning'}`}>
                    {task.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Deadlines */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Upcoming Deadlines</h2>
          <div className="space-y-3">
            {[
              { task: 'GSTR-1 Filing', companies: 12, dueDate: 'Nov 11, 2025', daysLeft: 8 },
              { task: 'Income Tax Return', companies: 5, dueDate: 'Nov 15, 2025', daysLeft: 12 },
              { task: 'PF Return', companies: 8, dueDate: 'Nov 20, 2025', daysLeft: 17 },
            ].map((deadline, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="font-medium text-gray-900">{deadline.task}</p>
                  <p className="text-sm text-gray-600">{deadline.companies} companies</p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{deadline.daysLeft} days left</p>
                  <p className="text-xs text-gray-600">{deadline.dueDate}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
