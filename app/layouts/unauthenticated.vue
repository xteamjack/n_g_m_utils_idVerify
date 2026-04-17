<template>
  <UnauthenticatedLayout>
    <slot />
  </UnauthenticatedLayout>
</template>

<script setup>
import UnauthenticatedLayout from '@libs/ui/layouts/unauthenticated.vue';
</script>
