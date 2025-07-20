import { Cuboid, FileText, Code, Mic, Database, Settings } from 'lucide-react';

// In a real app, this would be dynamic based on the current URL path.
// For this tutorial, we are setting it manually.
const navItems = [
  { name: 'SVG Studio', icon: Cuboid, href: '/', active: false },
  { name: 'Data Generator', icon: Database, href: '/data-generator', active: false },
  { name: 'Doc Inspector', icon: FileText, href: '/doc-inspector', active: false },
  { name: 'Code Analyzer', icon: Code, href: '/code-analyzer', active: false },
  { name: 'Voice Assistant', icon: Mic, href: '/voice-assistant', active: false },
];

export default function Nav() {
  return (
    <nav className="w-64 bg-gray-900 border-r border-gray-800 p-4 flex flex-col">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">CogniSuite</h2>
      </div>
      <ul className="space-y-2 flex-1">
        {navItems.map((item) => (
          <li key={item.name}>
            <a
              href={item.href}
              className={`flex items-center gap-3 px-4 py-2 rounded-lg text-sm transition-colors ${
                item.active
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-400 hover:bg-gray-800 hover:text-white'
              }`}
            >
              <item.icon size={20} />
              {item.name}
            </a>
          </li>
        ))}
      </ul>
      <div className="mt-auto">
        <a href="#" className="flex items-center gap-3 px-4 py-2 rounded-lg text-sm text-gray-400 hover:bg-gray-800 hover:text-white">
          <Settings size={20} />
          Settings
        </a>
      </div>
    </nav>
  );
}