<template>
  <div class="h-full flex flex-col items-center justify-center p-10 text-center animate-in fade-in duration-700">
    <h1 class="text-5xl font-black text-primary italic underline underline-offset-8 decoration-primary/20 tracking-tight">ID Verifty</h1>
    <p class="mt-6 text-xl opacity-70 font-medium max-w-2xl px-4">User Onboarding and ID Verification App</p>
    <div class="mt-10 text-left bg-slate-50 p-6 rounded-xl border border-slate-200">
      <h2 class="font-bold mb-4">Development Progress:</h2>
      <ul class="text-sm space-y-1 font-mono">
        <li>- [x] Environment Setup</li>
        <li>- [x] Update Frontend `package.json` with `@mediapipe/tasks-vision`</li>
        <li>- [x] Update Backend `vision.py` with rigorous validation logic</li>
        <li>- [x] Frontend Real-time Logic</li>
        <li>- [x] Initialize MediaPipe Face Landmarker in `CaptureContainer.vue`</li>
        <li>- [x] Implement detection loop (requestAnimationFrame)</li>
        <li>- [x] Add centering and orientation (yaw/pitch) logic</li>
        <li>- [x] Implement Red/Green visual feedback</li>
        <li>- [x] Backend Verification Logic</li>
        <li>- [x] Implement Laplacian-based blur detection</li>
        <li>- [x] Implement Face mesh verification for single-face and alignment</li>
        <li>- [x] Integration & Testing</li>
        <li>- [x] Verify capture is blocked during Red state</li>
        <li>- [x] Verify server rejection on poor quality images</li>
      </ul>
    </div>
    <div class="mt-10 flex gap-4">
      <NuxtLink to="/verify/demo-session-123" class="sans-button-primary">Start Verification PoC</NuxtLink>
      <NuxtLink to="/apps" class="sans-button-secondary">Explore Apps</NuxtLink>
    </div>
  </div>
</template>

<script setup>
/**
 * Initial landing page for the Customer microservice.
 */
</script>
