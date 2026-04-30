import type { EnvVarSchema, ServiceDependencySchema } from '@libs/core/dependency';

export default (baseEnv: EnvVarSchema[], baseService: ServiceDependencySchema[]) => {
    return {
        envSchema: [...baseEnv],
        serviceSchema: [
            ...baseService,
            { appKey: 'apps.profileStore', mandatory: false },
            { appKey: 'apps.idVerifyServer', mandatory: true }
        ]
    };
};
