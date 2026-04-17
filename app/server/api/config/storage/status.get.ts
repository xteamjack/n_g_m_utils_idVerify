import { getConfigByKey } from '@libs/core/config';
import { getDbHandle } from '@libs/utils/db';

/**
 * Storage Health & Metrics Proxy
 * Inspects all configured database modules, checks if collections exist,
 * and retrieves document counts.
 */
export default defineEventHandler(async (event) => {
  const config = useRuntimeConfig(event);
  const configServer = config.public?.configServer || config.configServer;

  if (!configServer) {
    throw createError({
      statusCode: 500,
      statusMessage: 'Config Server URL is not defined.'
    });
  }

  // 1. Fetch the full storage registry
  const mods = await getConfigByKey('storage.db.mods', 'generic', configServer as string);
  if (!mods) return {};

  const results: Record<string, any> = {};

  // 2. Process each module
  const processing = Object.keys(mods).map(async (modName) => {
    const modConfig = mods[modName];
    
    try {
      // Initialize DB Handle using the full path key
      const handle = await getDbHandle(`storage.db.mods.${modName}`, 'generic');
      
      // A. Strict Existence Check
      const rawDb = await handle.getRawDb();
      const collections = await rawDb.listCollections({ name: modConfig.collection }).toArray();
      
      if (collections.length === 0) {
        results[modName] = { 
          status: 'MISSING_COLLECTION', 
          count: 0, 
          error: `Collection '${modConfig.collection}' does not exist in database '${modConfig.database}'` 
        };
        return;
      }

      // B. Retrieve Record Count
      const countRes = await handle.query({ query: { limit: 0 } });
      
      results[modName] = { 
        status: 'OK', 
        count: countRes.meta?.totalRecords || 0 
      };

    } catch (err: any) {
      results[modName] = { 
        status: 'ERROR', 
        count: 0, 
        error: err.message 
      };
    }
  });

  // Execute inspection in parallel
  await Promise.allSettled(processing);

  return results;
});
