import { navigateTo, abortNavigation } from '#app';
import { sansCookieAuthInterceptor } from '@libs/web/interceptors';

export default defineNuxtRouteMiddleware(async (to) => {
    if (to.path.startsWith('/api')) return;
    console.log(`[AUTH-MW] customer - Navigating to: ${to.path}`);
    
    const result = await sansCookieAuthInterceptor(to);
    
    if (result === false) {
        console.warn(`[AUTH-MW] customer - Navigation aborted for: ${to.path}`);
        return abortNavigation();
    }

    if (typeof result === 'object' && result.status === 'redirect') {
        const isExternal = typeof result.redirectUrl === 'string' && result.redirectUrl.startsWith('http');
        console.log(`[AUTH-MW] customer - Redirection requested to:`, result.redirectUrl);
        return navigateTo(result.redirectUrl, { 
            external: isExternal,
            replace: result.replace || false
        });
    }
});
