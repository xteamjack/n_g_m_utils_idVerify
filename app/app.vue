<script setup>
import { computed } from 'vue';
import { useSANSAuth } from '@libs/web/auth';

const { authState } = useSANSAuth();
const layoutName = computed(() => authState.value?.state || 'unauthenticated');
</script>

<template>
  <NuxtLayout :name="layoutName">
    <NuxtPage />
  </NuxtLayout>
</template>
