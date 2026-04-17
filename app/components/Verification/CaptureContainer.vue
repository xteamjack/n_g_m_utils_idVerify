<script setup lang="ts">
/**
 * CaptureContainer.vue
 * Core component for real-time webcam capture with dynamic template overlays.
 */
const props = defineProps<{
    mode: 'face' | 'card'
    title: string
    description: string
}>()

const emit = defineEmits(['capture'])

const video = ref<HTMLVideoElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
const stream = ref<MediaStream | null>(null)
const captureStatus = ref<'idle' | 'scanning' | 'ready' | 'processing'>('scanning')
const errorMsg = ref('')

onMounted(async () => {
    try {
        stream.value = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: props.mode === 'face' ? 'user' : 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        })
        if (video.value) {
            video.value.srcObject = stream.value
        }
    } catch (err: any) {
        errorMsg.value = "Webcam access denied. Please check permissions."
    }
})

onUnmounted(() => {
    if (stream.value) {
        stream.value.getTracks().forEach(track => track.stop())
    }
})

const handleCapture = () => {
    if (!video.value || !canvas.value) return
    
    captureStatus.value = 'processing'
    const context = canvas.value.getContext('2d')
    if (context) {
        canvas.value.width = video.value.videoWidth
        canvas.value.height = video.value.videoHeight
        context.drawImage(video.value, 0, 0)
        const blob = canvas.value.toBlob((blob) => {
            emit('capture', blob)
        }, 'image/jpeg', 0.95)
    }
}
</script>

<template>
  <div class="relative w-full max-w-3xl mx-auto overflow-hidden rounded-3xl bg-black shadow-2xl border border-white/10 aspect-video">
    <!-- Camera Feed -->
    <video
      ref="video"
      autoplay
      playsinline
      muted
      class="h-full w-full object-cover scale-x-[-1]"
      :class="{ 'grayscale': captureStatus === 'processing' }"
    ></video>

    <!-- Overlay Template -->
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <!-- Face Template Overlay -->
      <div v-if="mode === 'face'" 
        class="w-64 h-80 border-2 rounded-[100%] transition-colors duration-500"
        :class="captureStatus === 'ready' ? 'border-primary shadow-[0_0_40px_rgba(var(--color-primary),0.5)]' : 'border-white/30'"
      ></div>
      
      <!-- Card Template Overlay -->
      <div v-else 
        class="w-[80%] h-[60%] border-2 rounded-2xl transition-colors duration-500"
        :class="captureStatus === 'ready' ? 'border-primary shadow-[0_0_40px_rgba(var(--color-primary),0.5)]' : 'border-white/30'"
      ></div>
    </div>

    <!-- UI Controls -->
    <div class="absolute inset-x-0 bottom-0 p-8 flex flex-col items-center bg-gradient-to-t from-black/80 to-transparent">
        <h3 class="text-white text-xl font-bold tracking-tight">{{ title }}</h3>
        <p class="text-white/60 text-sm mt-1">{{ description }}</p>
        
        <button 
            @click="handleCapture"
            :disabled="captureStatus === 'processing'"
            class="mt-6 w-16 h-16 rounded-full border-4 border-white flex items-center justify-center bg-white/20 hover:bg-white/40 active:scale-95 transition-all"
        >
            <div class="w-12 h-12 rounded-full bg-white transition-all transform" :class="captureStatus === 'processing' ? 'scale-75 opacity-50' : ''"></div>
        </button>
    </div>

    <!-- Hidden Canvas for capture -->
    <canvas ref="canvas" class="hidden"></canvas>
    
    <!-- Error Overlay -->
    <div v-if="errorMsg" class="absolute inset-0 bg-black/90 flex items-center justify-center p-10 text-center">
        <p class="text-red-400 font-medium">{{ errorMsg }}</p>
    </div>
  </div>
</template>

<style scoped>
.aspect-video {
    aspect-ratio: 16 / 9;
}
</style>
