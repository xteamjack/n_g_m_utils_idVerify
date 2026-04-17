<template>
  <AuthenticatedLayout>
    <slot />
  </AuthenticatedLayout>
</template>

<script setup>
import AuthenticatedLayout from '@libs/ui/layouts/authenticated.vue';
</script>
