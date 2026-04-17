<template>
  <TempAuthenticatedLayout>
    <slot />
  </TempAuthenticatedLayout>
</template>

<script setup>
import TempAuthenticatedLayout from '@libs/ui/layouts/tempAuthenticated.vue';
</script>
