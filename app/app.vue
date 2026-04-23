<script setup>
import { computed } from 'vue';
import { useSANSAuth } from '@libs/web/auth';

const { authState } = useSANSAuth();
const route = useRoute();
const layoutName = computed(() => {
  if (route.meta.layout === false) return false;
  return authState.value?.state || 'unauthenticated';
});
</script>

<template>
  <NuxtLayout :name="layoutName">
    <NuxtPage />
  </NuxtLayout>
</template>
