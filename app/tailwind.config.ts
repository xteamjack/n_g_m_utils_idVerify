import type { Config } from 'tailwindcss'
import path from 'node:path'
import { tailwindTheme } from '../../n_g_m_nuxt_libs/libs/ui/themes/tailwind'

const projectRoot = process.env.SANS_PROJECT_ROOT || path.resolve(__dirname, '../../');
const libsRoot = path.resolve(projectRoot, 'n_g_m_nuxt_libs/libs');

export default <Partial<Config>>{
  darkMode: 'class',
  theme: tailwindTheme as any, 
  content: [
    './components/**/*.{vue,js,ts}',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './app.vue',
    path.join(libsRoot, 'ui/components/**/*.{vue,js,ts}').replace(/\\/g, '/'),
    path.join(libsRoot, 'ui/layouts/**/*.vue').replace(/\\/g, '/')
  ]
}
