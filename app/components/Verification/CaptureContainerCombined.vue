<script setup lang="ts">
import { 
  FaceLandmarker, 
  FilesetResolver,
} from "@mediapipe/tasks-vision";

/**
 * CaptureContainerCombined.vue
 * Specialized capture container for side-by-side Face and ID Card Front capture.
 */
const props = defineProps<{
    title: string
    description: string
}>()

const emit = defineEmits(['capture'])

const video = ref<HTMLVideoElement | null>(null)
const canvas = ref<HTMLCanvasElement | null>(null)
const stream = ref<MediaStream | null>(null)
const captureStatus = ref<'idle' | 'scanning' | 'ready' | 'processing'>('scanning')
const guidanceMsg = ref('Initializing AI...')
const errorMsg = ref('')

// MediaPipe State
let faceLandmarker: FaceLandmarker | null = null;
let lastVideoTime = -1;

onMounted(async () => {
    console.log("[CaptureContainerCombined] Mounting...");
    // 1. Initialize Webcam
    try {
        stream.value = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'user', // Usually front camera for this side-by-side
                width: { ideal: 1920 }, // High-res critical for combined
                height: { ideal: 1080 }
            } 
        })
        if (video.value) {
            video.value.srcObject = stream.value
        }
    } catch (err: any) {
        console.error("[CaptureContainerCombined] MediaDevices Error:", err);
        errorMsg.value = "Webcam access denied."
        return
    }

    // 2. Initialize MediaPipe
    guidanceMsg.value = "Loading AI Core...";
    try {
        const vision = await FilesetResolver.forVisionTasks(
            "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm"
        );
        faceLandmarker = await FaceLandmarker.createFromOptions(vision, {
            baseOptions: {
                modelAssetPath: `https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task`,
                delegate: "GPU"
            },
            outputFaceBlendshapes: true,
            runningMode: "VIDEO",
            numFaces: 1
        });
        
        guidanceMsg.value = "Align Face (Left) and Card (Right)";
        
        if (video.value) {
            if (video.value.readyState >= 2) {
                predictWebcam();
            } else {
                video.value.addEventListener("loadeddata", predictWebcam);
            }
        }
    } catch (err) {
        console.error("[Combined] AI Error:", err);
        errorMsg.value = "AI failed to load.";
        captureStatus.value = 'ready';
    }
})

const predictWebcam = async () => {
    if (!video.value || !faceLandmarker) return;

    if (video.value.currentTime !== lastVideoTime) {
        lastVideoTime = video.value.currentTime;
        const startTimeMs = performance.now();
        const results = faceLandmarker.detectForVideo(video.value, startTimeMs);

        if (results.faceLandmarks && results.faceLandmarks.length > 0) {
            const landmarks = results.faceLandmarks[0];
            const nose = landmarks[1];
            
            // --- LOOSENED COMBINED HEURISTICS ---
            // Much wider bounds for the left-side face slot
            const isCenteredX = nose.x > 0.02 && nose.x < 0.55; 
            const isCenteredY = nose.y > 0.1 && nose.y < 0.9;

            if (!isCenteredX || !isCenteredY) {
                guidanceMsg.value = "Keep face on the left side";
                captureStatus.value = 'scanning';
            } else {
                guidanceMsg.value = "Ready! Alignment focused.";
                captureStatus.value = 'ready';
            }
        } else {
            guidanceMsg.value = "Align face on the left side";
            captureStatus.value = 'scanning';
        }
    }
    
    if (captureStatus.value !== 'processing') {
        window.requestAnimationFrame(predictWebcam);
    }
};

onUnmounted(() => {
    if (stream.value) stream.value.getTracks().forEach(track => track.stop())
    if (faceLandmarker) faceLandmarker.close();
})

const handleCapture = () => {
    if (captureStatus.value !== 'ready') return;
    if (!video.value || !canvas.value) return
    
    captureStatus.value = 'processing'
    const context = canvas.value.getContext('2d')
    if (context) {
        canvas.value.width = video.value.videoWidth
        canvas.value.height = video.value.videoHeight
        context.drawImage(video.value, 0, 0)
        canvas.value.toBlob((blob) => {
            emit('capture', blob)
        }, 'image/jpeg', 0.95)
    }
}
</script>

<template>
  <div class="relative w-full max-w-5xl mx-auto overflow-hidden rounded-3xl bg-black shadow-2xl border border-white/10 aspect-video group">
    <!-- Camera Feed -->
    <video
      ref="video"
      autoplay
      playsinline
      muted
      class="h-full w-full object-cover scale-x-[-1] transition-filter duration-700"
      :class="{ 'grayscale brightness-50': captureStatus === 'processing' }"
    ></video>

    <!-- Overlay Template -->
    <div class="absolute inset-0 flex items-center justify-around pointer-events-none px-4">
      <!-- Face Guide (Left) -->
      <div 
        class="w-[35%] aspect-[3/4] border-[3px] rounded-[100%] transition-all duration-500 flex flex-col items-center justify-center p-4 text-center"
        :class="captureStatus === 'ready' 
            ? 'border-primary shadow-[0_0_60px_rgba(var(--color-primary-rgb),0.4)] scale-105' 
            : 'border-white/20'"
      >
        <div class="text-[10px] text-white/40 uppercase tracking-widest font-mono">Face Slot</div>
        <div class="text-[9px] text-white/60 font-bold uppercase tracking-tight mt-2 min-h-[3em]">{{ guidanceMsg }}</div>
      </div>
      
      <!-- Card Guide (Right) -->
      <div 
        class="w-[45%] h-[60%] border-[3px] rounded-3xl transition-all duration-500 flex flex-col items-center justify-center"
        :class="captureStatus === 'ready' 
            ? 'border-primary shadow-[0_0_60px_rgba(var(--color-primary-rgb),0.5)]' 
            : 'border-white/20'"
      >
        <div class="text-[10px] text-white/40 uppercase tracking-widest font-mono">ID Card Slot</div>
        <div class="text-[9px] text-white/60 uppercase mt-2">Hold ID Card steady here</div>
      </div>
    </div>

    <!-- UI Controls -->
    <div class="absolute inset-x-0 bottom-0 p-8 flex flex-col items-center bg-gradient-to-t from-black/95 via-black/40 to-transparent">
        <h3 class="text-white text-xl font-black italic tracking-tighter uppercase">{{ title }}</h3>
        <p class="text-white/50 text-[10px] mt-1 font-medium tracking-widest uppercase">{{ description }}</p>
        
        <button 
            @click="handleCapture"
            :disabled="captureStatus !== 'ready'"
            class="mt-8 relative group active:scale-95 transition-all outline-none"
            :class="{ 
                'opacity-20 cursor-not-allowed': captureStatus !== 'ready',
                'animate-pulse-slow': captureStatus === 'ready'
            }"
        >
            <div class="w-20 h-20 rounded-full border-4 flex items-center justify-center transition-all duration-500"
                :class="captureStatus === 'ready' ? 'border-primary shadow-[0_0_40px_rgba(var(--color-primary-rgb),0.6)] scale-110' : 'border-white/20'"
            >
                <div 
                    class="w-14 h-14 rounded-full transition-all transform duration-300 shadow-inner"
                    :class="[
                        captureStatus === 'ready' ? 'bg-primary scale-100 shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.5)]' : 'bg-white/10 scale-90',
                        captureStatus === 'processing' ? 'scale-0 opacity-0' : 'opacity-100'
                    ]"
                ></div>
                <div v-if="captureStatus === 'processing'" class="absolute w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
        </button>
    </div>

    <canvas ref="canvas" class="hidden"></canvas>
    <div v-if="errorMsg" class="absolute inset-0 bg-black/90 flex flex-col items-center justify-center text-center p-10">
        <p class="text-red-400 font-bold uppercase tracking-widest italic">{{ errorMsg }}</p>
        <button @click="window.location.reload()" class="mt-4 px-6 py-2 border border-white/20 rounded-full text-xs text-white">RETRY</button>
    </div>
  </div>
</template>

<style scoped>
.aspect-video { aspect-ratio: 16 / 9; }
@keyframes pulse-slow {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}
.animate-pulse-slow { animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite; }
</style>
