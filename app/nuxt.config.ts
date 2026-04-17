import path from 'node:path'
import { APP_KEY } from './constants';

export default async () => {
    const projectRoot = process.env.SANS_PROJECT_ROOT || path.resolve(__dirname, '../../');
    const libsRoot = path.resolve(projectRoot, 'n_g_m_nuxt_libs/libs');

    try {
        const helperPath = path.join(libsRoot, 'utils/nuxt-config.ts').replace(/\\/g, '/');
        const defsLibPath = path.join(libsRoot, 'config/defs.ts').replace(/\\/g, '/');

        const { baseEnvSchema, baseServiceSchema } = await import(`file://${defsLibPath}`);
        const { default: getSchemas } = await import('./config/defs');

        const { envSchema, serviceSchema } = getSchemas(baseEnvSchema, baseServiceSchema);
        const { defineAppConfig } = await import(`file://${helperPath}`);

        return await defineAppConfig({
            appKey: APP_KEY,
            libsRoot,
            extends: [ 
                libsRoot.replace(/\\/g, '/'),
                path.resolve(projectRoot, 'n_dh_ms_fn_profileStore/app').replace(/\\/g, '/')
            ],
            envSchema,
            serviceSchema,
            overrides: {
                modules: ["@nuxtjs/tailwindcss", "@nuxtjs/color-mode"],
                tailwindcss: { configPath: 'tailwind.config.ts' },
                runtimeConfig: {
                    public: {
                        configServer: process.env.SANS_SERVER_CONFIG
                    }
                },
                components: [
                    { path: '~/components' },
                    { path: path.resolve(projectRoot, 'n_dh_ms_fn_profileStore/app/components').replace(/\\/g, '/'), pathPrefix: false }
                ],
                vite: {
                    build: {
                        target: 'esnext',
                        minify: false,
                        cssCodeSplit: false
                    }
                }
            }
        });
    } catch (error: any) {
        console.error(`[CRITICAL] Configuration load failed: ${error.message}`);
        if (error.stack) console.error(`Stack Trace: \n${error.stack}`);
        process.exit(1);
    }
};
