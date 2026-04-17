<script setup lang="ts">
import { 
  FaceLandmarker, 
  FilesetResolver,
} from "@mediapipe/tasks-vision";

/**
 * CaptureContainer.vue
 * High-fidelity webcam capture with real-time MediaPipe AI for face validation.
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
const guidanceMsg = ref('Initializing AI...')
const errorMsg = ref('')

// MediaPipe State
let faceLandmarker: FaceLandmarker | null = null;
let lastVideoTime = -1;

onMounted(async () => {
    console.log("[CaptureContainer] Mounting... Mode:", props.mode);
    // 1. Initialize Webcam
    try {
        stream.value = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: props.mode === 'face' ? 'user' : 'environment',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            } 
        })
        console.log("[CaptureContainer] Webcam stream acquired.");
        if (video.value) {
            video.value.srcObject = stream.value
        }
    } catch (err: any) {
        console.error("[CaptureContainer] MediaDevices Error:", err);
        errorMsg.value = "Webcam access denied. Please check permissions."
        return
    }

    // 2. Initialize MediaPipe if in Face mode
    if (props.mode === 'face') {
        guidanceMsg.value = "Loading Face AI...";
        console.log("[CaptureContainer] Initializing MediaPipe FaceLandmarker...");
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
            
            console.log("[CaptureContainer] MediaPipe initialized successfully.");
            guidanceMsg.value = "Position your face in the frame";
            
            // Start Prediction Loop
            if (video.value) {
                // If video is already loaded, start manually
                if (video.value.readyState >= 2) {
                    console.log("[CaptureContainer] Video already loaded, starting loop.");
                    predictWebcam();
                } else {
                    console.log("[CaptureContainer] Waiting for video loadeddata event...");
                    video.value.addEventListener("loadeddata", predictWebcam);
                }
            }
        } catch (err) {
            console.error("[CaptureContainer] AI Initialization Error:", err);
            errorMsg.value = "AI failed to load. Please check your internet connection.";
            captureStatus.value = 'ready';
        }
    } else {
        console.log("[CaptureContainer] Card mode: skipping AI.");
        captureStatus.value = 'ready';
        guidanceMsg.value = "Place your ID card in the frame";
    }
})

const predictWebcam = async () => {
    if (!video.value || !faceLandmarker) {
        console.warn("[CaptureContainer] Loop aborted: video or landmarker missing.");
        return;
    }

    if (video.value.currentTime !== lastVideoTime) {
        lastVideoTime = video.value.currentTime;
        const startTimeMs = performance.now();
        const results = faceLandmarker.detectForVideo(video.value, startTimeMs);

        if (results.faceLandmarks && results.faceLandmarks.length > 0) {
            const landmarks = results.faceLandmarks[0];
            
            // --- AI HEURISTICS ---
            const nose = landmarks[1];
            const leftEye = landmarks[33];
            const rightEye = landmarks[263];

            // --- LOOSENED HEURISTICS ---

            const isCenteredX = nose.x > 0.15 && nose.x < 0.85; 
            const isCenteredY = nose.y > 0.1 && nose.y < 0.9;
            const symmetry = Math.abs((nose.x - leftEye.x) - (rightEye.x - nose.x));
            const isLookingForward = symmetry < 0.25; // More lenient (was 0.15)
            const faceWidth = Math.abs(rightEye.x - leftEye.x);
            const isRightDistance = faceWidth > 0.02 && faceWidth < 0.8; // Very wide bounds

            // --- GUIDANCE LOGIC ---
            if (!isCenteredX || !isCenteredY) {
                guidanceMsg.value = "Adjust face position";
                captureStatus.value = 'scanning';
            } else if (!isLookingForward) {
                guidanceMsg.value = "Look at the camera";
                captureStatus.value = 'scanning';
            } else if (!isRightDistance) {
                guidanceMsg.value = "Adjust distance";
                captureStatus.value = 'scanning';
            } else {
                guidanceMsg.value = "Ready! Alignment focused.";
                captureStatus.value = 'ready';
            }
        } else {
            if (Math.random() < 0.05) console.warn("[CaptureContainer] No face detected.");
            guidanceMsg.value = "No face detected. Adjust lighting.";
            captureStatus.value = 'scanning';
        }
    }
    
    if (captureStatus.value !== 'processing') {
        window.requestAnimationFrame(predictWebcam);
    }
};

onUnmounted(() => {
    if (stream.value) {
        stream.value.getTracks().forEach(track => track.stop())
    }
    if (faceLandmarker) {
        faceLandmarker.close();
    }
})

const handleCapture = () => {
    if (captureStatus.value !== 'ready' && props.mode === 'face') return;
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
  <div class="relative w-full max-w-3xl mx-auto overflow-hidden rounded-3xl bg-black shadow-2xl border border-white/10 aspect-video group">
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
    <div class="absolute inset-0 flex items-center justify-center pointer-events-none">
      <!-- Face Template Overlay -->
      <div v-if="mode === 'face'" 
        class="w-72 h-96 border-[3px] rounded-[100%] transition-all duration-500 flex flex-col items-center justify-center p-8 text-center"
        :class="captureStatus === 'ready' 
            ? 'border-primary shadow-[0_0_60px_rgba(var(--color-primary-rgb),0.4)] scale-105' 
            : 'border-white/20'"
      >
        <div class="text-[10px] text-white/40 uppercase tracking-widest font-mono">{{ captureStatus === 'ready' ? 'Ready' : 'Scanning' }}</div>
        <div class="text-xs text-white font-bold uppercase tracking-tight mt-2 min-h-[3em] flex items-center">{{ guidanceMsg }}</div>
      </div>
      
      <!-- Card Template Overlay -->
      <div v-else 
        class="w-[80%] h-[60%] border-[3px] rounded-3xl transition-all duration-500 flex items-center justify-center"
        :class="captureStatus === 'ready' ? 'border-primary shadow-[0_0_60px_rgba(var(--color-primary-rgb),0.4)]' : 'border-white/20'"
      >
        <div class="text-[10px] text-white/40 uppercase tracking-widest font-mono">Place Card in Frame</div>
      </div>
    </div>

    <!-- UI Controls -->
    <div class="absolute inset-x-0 bottom-0 p-8 flex flex-col items-center bg-gradient-to-t from-black/95 via-black/40 to-transparent">
        <h3 class="text-white text-xl font-black italic tracking-tighter uppercase">{{ title }}</h3>
        <p class="text-white/50 text-xs mt-1 font-medium tracking-wide uppercase">{{ description }}</p>
        
        <button 
            @click="handleCapture"
            :disabled="captureStatus !== 'ready' && mode === 'face'"
            class="mt-8 relative group active:scale-95 transition-all outline-none"
            :class="{ 
                'opacity-20 cursor-not-allowed': captureStatus !== 'ready' && mode === 'face',
                'animate-pulse-slow': captureStatus === 'ready'
            }"
        >
            <!-- Camera Ring -->
            <div class="w-20 h-20 rounded-full border-4 flex items-center justify-center transition-all duration-500"
                :class="captureStatus === 'ready' 
                    ? 'border-primary shadow-[0_0_40px_rgba(var(--color-primary-rgb),0.6)] scale-110' 
                    : 'border-white/20'"
            >
                <!-- Inner Button -->
                <div 
                    class="w-14 h-14 rounded-full transition-all transform duration-300 shadow-inner"
                    :class="[
                        captureStatus === 'ready' ? 'bg-primary scale-100 shadow-[0_0_20px_rgba(var(--color-primary-rgb),0.5)]' : 'bg-white/10 scale-90',
                        captureStatus === 'processing' ? 'scale-0 opacity-0' : 'opacity-100'
                    ]"
                ></div>
                <!-- Processing Spinner -->
                <div v-if="captureStatus === 'processing'" class="absolute w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            </div>
        </button>
    </div>

    <!-- Hidden Canvas for capture -->
    <canvas ref="canvas" class="hidden"></canvas>
    
    <!-- Error Overlay -->
    <div v-if="errorMsg" class="absolute inset-0 bg-black/90 flex flex-col items-center justify-center p-10 text-center space-y-4">
        <div class="w-16 h-16 bg-red-500/10 rounded-full flex items-center justify-center text-red-500">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
        </div>
        <p class="text-red-400 font-bold italic tracking-tight">{{ errorMsg }}</p>
        <button @click="window.location.reload()" class="sans-button-secondary text-xs">RETRY ACCESS</button>
    </div>
  </div>
</template>

<style scoped>
.aspect-video {
    aspect-ratio: 16 / 9;
}

@keyframes pulse-slow {
  0%, 100% { transform: scale(1); opacity: 1; }
  50% { transform: scale(1.05); opacity: 0.9; }
}

.animate-pulse-slow {
  animation: pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}
</style>
