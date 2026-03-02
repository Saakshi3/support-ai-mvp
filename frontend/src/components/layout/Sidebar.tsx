import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  HomeIcon,
  TicketIcon,
  PlusIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/AuthContext';
import { cn } from '@/lib/utils';

const requesterNavigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'My Tickets', href: '/tickets', icon: TicketIcon },
  { name: 'Create Ticket', href: '/tickets/new', icon: PlusIcon },
];

const supportNavigation = [
  { name: 'Dashboard', href: '/', icon: HomeIcon },
  { name: 'All Tickets', href: '/tickets', icon: TicketIcon },
  { name: 'AI Analytics', href: '/dashboard/support', icon: ChartBarIcon },
  { name: 'AI Insights', href: '/ai', icon: SparklesIcon },
];

export default function Sidebar() {
  const { user } = useAuth();
  const navigation = user?.role === 'SUPPORT' ? supportNavigation : requesterNavigation;

  return (
    <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-72 lg:flex-col">
      <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 bg-white px-6 pb-4">
        <div className="flex h-16 shrink-0 items-center">
          <div className="flex items-center">
            <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <SparklesIcon className="h-5 w-5 text-white" />
            </div>
            <span className="ml-3 text-xl font-bold text-gray-900">
              Support AI
            </span>
          </div>
        </div>
        
        <nav className="flex flex-1 flex-col">
          <ul role="list" className="flex flex-1 flex-col gap-y-7">
            <li>
              <ul role="list" className="-mx-2 space-y-1">
                {navigation.map((item) => (
                  <li key={item.name}>
                    <NavLink
                      to={item.href}
                      className={({ isActive }) =>
                        cn(
                          'group flex gap-x-3 rounded-md p-2 text-sm leading-6 font-semibold',
                          isActive
                            ? 'bg-primary-50 text-primary-600'
                            : 'text-gray-700 hover:text-primary-600 hover:bg-gray-50'
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon
                            className={cn(
                              'h-6 w-6 shrink-0',
                              isActive ? 'text-primary-600' : 'text-gray-400 group-hover:text-primary-600'
                            )}
                            aria-hidden="true"
                          />
                          {item.name}
                        </>
                      )}
                    </NavLink>
                  </li>
                ))}
              </ul>
            </li>
            
            {/* User info */}
            <li className="mt-auto">
              <div className="rounded-lg bg-gray-50 p-4">
                <div className="flex items-center">
                  <div className="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center">
                    <span className="text-sm font-medium text-white">
                      {user?.display_name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    </span>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">{user?.display_name}</p>
                    <p className="text-xs text-gray-500">{user?.role}</p>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  );
}