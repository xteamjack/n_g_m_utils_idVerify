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
    // Scan the WHOLE shared UI layer (not just components/layouts) so
    // `@layer components` classes used in ui/pages (ApplicationPage) +
    // ui/decorators — e.g. .sans-page-header-icon — are not purged by
    // Tailwind v3. Mirrors n_dh_ms_fn_recruiter.
    path.join(libsRoot, 'ui/**/*.{vue,js,ts}').replace(/\\/g, '/')
  ]
}
