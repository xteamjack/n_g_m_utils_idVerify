import type { EnvVarSchema, ServiceDependencySchema } from '@libs/core/dependency';

export default (baseEnv: EnvVarSchema[], baseService: ServiceDependencySchema[]) => {
    return {
        envSchema: [...baseEnv],
        serviceSchema: [
            ...baseService,
            { key: 'apps.profileStore', type: 'service' }
        ]
    };
};
