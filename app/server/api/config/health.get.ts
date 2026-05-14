import { getConfigByKey } from '@libs/core/config';

/**
 * App Health Proxy
 * Pings all microservices in parallel to check if they are UP/DOWN.
 * Securely handles the system's apiToken for the authorization header.
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event);
  const configServer = config.public?.configServer || config.configServer;
  const svcApiKey = (config as any).svcApiKey;

  if (!configServer) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Config Server URL is not configured in the system.'
    });
  }

  // 1. Fetch the app registry
  const apps = await getConfigByKey('apps', 'generic', configServer as string);
  if (!apps) return {};

  const results: Record<string, string> = {};

  // 2. Perform parallel pings
  const pings = Object.entries(apps).map(async ([code, app]: [string, any]) => {
    // Skip if no URL defined (e.g., config sections)
    if (!app.webServer?.url) {
      results[code] = 'N/A';
      return;
    }

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 3000); // 3s timeout

      const targetUrl = `${app.webServer.url.replace(/\/$/, '')}/api/health`;
      
      const headers: Record<string, string> = { 'Accept': 'application/json' };
      if (svcApiKey) headers['Authorization'] = `Bearer ${svcApiKey}`;
      const res = await fetch(targetUrl, {
        headers,
        signal: controller.signal
      });

      clearTimeout(timeout);

      if (res.status === 200) {
        results[code] = 'UP';
      } else {
        // Specifically capture status codes like 404 as requested
        results[code] = `ERR_${res.status}`;
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        results[code] = 'TIMEOUT';
      } else {
        results[code] = 'DOWN';
      }
    }
  });

  // Wait for all pings to finish or timeout
  await Promise.allSettled(pings);

  return results;
});
