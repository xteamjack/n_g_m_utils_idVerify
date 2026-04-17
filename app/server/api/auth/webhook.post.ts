import { handleAuthWebhook } from '@libs/server/webhook';

export default defineEventHandler(async (event) => {
    return await handleAuthWebhook(event);
});
