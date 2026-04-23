<script setup lang="ts">
definePageMeta({ layout: false })
/**
 * verify/[id].vue
 * Main orchestrator for the identity verification flow.
 */
const route = useRoute()
const requestId = route.params.id as string

type Step = 'init' | 'capture-face' | 'capture-front' | 'capture-back' | 'processing' | 'success' | 'failed'
const currentStep = ref<Step>('capture-face')
const errorMessage = ref('')
const extractedData = ref<any>(null)
const matchResults = ref<any>(null)

const steps = [
  { id: 'capture-face', title: 'Face Verification', desc: 'Securely capture your face for biometric matching.' },
  { id: 'capture-front', title: 'ID Card (Front)', desc: 'Align the front side of your government-issued ID.' },
  { id: 'capture-back', title: 'ID Card (Back)', desc: 'Align the back side of your government-issued ID.' }
]

// Handle the portal's handshake payload
const query = route.query
const payload = query.payload ? JSON.parse(decodeURIComponent(atob(query.payload as string))) : null
const callbackUrl = payload?.callback_url

const resetFlow = () => {
    errorMessage.value = ''
    currentStep.value = 'capture-face'
    extractedData.value = null
    matchResults.value = null
}

const forceVerify = async () => {
    if (!callbackUrl) {
        errorMessage.value = "PROTOCOL_ERROR: No callback URL provided in portal handshake."
        return
    }
    
    try {
        currentStep.value = 'processing'
        // Synchronized Loop: idVerifyApp -> frontend (proxy) -> backend (sink)
        await $fetch(callbackUrl, {
            method: 'POST',
            body: {
                request_id: requestId,
                status: 'success',
                data: [{
                    verificationStatus: 'Verified',
                    verificationData: { 
                      method: 'ManualMock', 
                      timestamp: new Date().toISOString(),
                      refObject: payload.data?.[0]?.refObject,
                      refId: payload.data?.[0]?.refId
                    }
                }]
            }
        })
        currentStep.value = 'success'
    } catch (err: any) {
        errorMessage.value = `Callback failed: ${err.message}`
        console.error("Verification callback failed", err)
    }
}

const handleCapture = async (blob: Blob) => {
    let endpoint = ''
    let queryParams = `?request_id=${requestId}`
    
    if (currentStep.value === 'capture-face') {
        endpoint = '/verify/capture/face'
    } else {
        endpoint = '/verify/capture/card'
        const side = currentStep.value === 'capture-front' ? 'front' : 'back'
        queryParams += `&side=${side}`
    }

    try {
        const formData = new FormData()
        formData.append('file', blob, 'capture.jpg')

        const result: any = await $fetch(`http://localhost:8010${endpoint}${queryParams}`, {
            method: 'POST',
            body: formData
        })

        if (result.status === 'rejected') {
            errorMessage.value = result.message
            return
        }

        // Store OCR results if available
        if (result.ocr) {
            extractedData.value = result.ocr.raw_text
        }
        if (result.matching) {
            matchResults.value = result.matching
        }

        // Progress to next step
        if (currentStep.value === 'capture-face') {
            currentStep.value = 'capture-front'
        } else if (currentStep.value === 'capture-front') {
            currentStep.value = 'capture-back'
        } else {
            currentStep.value = 'processing'
            // Final verification delay for effect
            setTimeout(() => {
                currentStep.value = 'success'
            }, 2000)
        }
    } catch (err: any) {
        errorMessage.value = "Secure processing failed. Please check server connectivity."
        console.error(err)
    }
}
</script>

<template>
  <div class="min-h-screen bg-[#050505] text-white flex flex-col font-sans selection:bg-primary selection:text-black">
    <!-- Premium Backdrop Glow -->
    <div class="fixed inset-0 overflow-hidden pointer-events-none">
        <div class="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-primary/10 rounded-full blur-[120px] animate-pulse"></div>
        <div class="absolute top-[20%] -right-[10%] w-[30%] h-[30%] bg-blue-500/5 rounded-full blur-[100px]"></div>
    </div>

    <main class="relative flex-1 flex flex-col items-center justify-center p-6 space-y-12 max-w-5xl mx-auto w-full">
      
      <!-- High-Fidelity Progress Stepper -->
      <div class="w-full max-w-lg space-y-4">
          <div class="flex justify-between items-end px-2">
              <div v-for="(s, index) in steps" :key="s.id" class="flex flex-col gap-2">
                  <span 
                    class="text-[9px] font-black uppercase tracking-widest transition-colors duration-500"
                    :class="currentStep === s.id ? 'text-primary' : 'text-white/20'"
                  >
                    0{{ index + 1 }}
                  </span>
              </div>
          </div>
          <div class="h-1.5 w-full bg-white/5 rounded-full overflow-hidden flex p-0.5">
            <div 
                v-for="(s, index) in steps" :key="s.id"
                class="h-full transition-all duration-700 rounded-full"
                :style="{ width: '33.33%' }"
                :class="[
                    currentStep === s.id ? 'bg-primary shadow-[0_0_15px_rgba(var(--primary-rgb),0.4)]' : 
                    steps.findIndex(x => x.id === currentStep) > index ? 'bg-emerald-500' : 'bg-transparent'
                ]"
            ></div>
          </div>
      </div>

      <!-- Capture Container -->
      <div v-if="currentStep.startsWith('capture')" class="w-full space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-700">
        <div class="text-center space-y-3">
            <h2 class="text-4xl font-black italic tracking-tighter uppercase leading-none">{{ steps.find(s => s.id === currentStep)?.title }}</h2>
            <p class="text-white/40 text-[11px] font-bold uppercase tracking-[0.2em]">{{ steps.find(s => s.id === currentStep)?.desc }}</p>
        </div>

        <div class="glass-container p-4 rounded-[2.5rem] bg-white/[0.02] border border-white/5 shadow-2xl">
            <VerificationCaptureContainer 
                :mode="currentStep === 'capture-face' ? 'face' : 'card'"
                :title="steps.find(s => s.id === currentStep)?.title || ''"
                :description="steps.find(s => s.id === currentStep)?.desc || ''"
                @capture="handleCapture"
            />
        </div>
      </div>

      <!-- Processing State -->
      <div v-else-if="currentStep === 'processing'" class="text-center space-y-10 py-20 animate-in fade-in duration-700">
        <div class="relative w-40 h-40 mx-auto">
            <div class="absolute inset-0 border-2 border-primary/10 rounded-full"></div>
            <div class="absolute inset-0 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
            <div class="absolute inset-4 border border-white/5 rounded-full flex items-center justify-center">
                <span class="text-primary font-black italic tracking-tighter text-xl">SANS</span>
            </div>
            <!-- Dynamic scanning ring -->
            <div class="absolute inset-0 border-2 border-emerald-400/30 rounded-full animate-ping opacity-20"></div>
        </div>
        <div class="space-y-3">
            <h2 class="text-4xl font-black italic tracking-tighter uppercase">Analyzing Biometrics</h2>
            <div class="flex flex-col items-center gap-1">
                <p class="text-white/30 uppercase text-[10px] font-bold tracking-[0.4em]">Algorithmic matching in progress</p>
                <div class="flex gap-1">
                    <div v-for="i in 3" :key="i" class="w-1 h-1 bg-primary rounded-full animate-bounce" :style="{ animationDelay: `${i * 150}ms` }"></div>
                </div>
            </div>
        </div>
      </div>

      <!-- Result States -->
      <div v-else-if="currentStep === 'success'" class="text-center space-y-8 max-w-xl py-10 animate-in zoom-in-95 duration-500">
        <div class="relative w-32 h-32 mx-auto">
            <div class="absolute inset-0 bg-emerald-500/20 rounded-full blur-2xl animate-pulse"></div>
            <div class="w-full h-full bg-white/[0.03] border border-emerald-500/30 rounded-full flex items-center justify-center relative">
                <div class="w-16 h-16 bg-emerald-500 rounded-full flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.4)]">
                    <svg class="w-8 h-8 text-black" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="4">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                    </svg>
                </div>
            </div>
        </div>
        
        <div class="space-y-4">
            <h2 class="text-5xl font-black italic tracking-tighter uppercase leading-none">Identity Verified</h2>
            <p class="text-white/40 font-medium tracking-tight max-w-sm mx-auto">Documentation securely processed and biometrically matched.</p>
        </div>
        
        <!-- Extracted Data Summary Card -->
        <div v-if="matchResults" class="bg-white/[0.03] border border-white/10 rounded-[2rem] p-8 text-left space-y-6 backdrop-blur-sm relative overflow-hidden group">
            <div class="absolute top-0 right-0 p-4 opacity-5">
                <svg class="w-20 h-20" fill="currentColor" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
            </div>
            
            <h4 class="text-[10px] text-primary uppercase tracking-[0.3em] font-black">Verification Audit Summary</h4>
            <div class="grid grid-cols-2 gap-y-6 gap-x-12">
                <div v-for="(score, field) in matchResults.match_scores" :key="field" class="space-y-2">
                    <div class="flex justify-between items-center">
                        <span class="text-[10px] font-black uppercase text-white/30 tracking-widest">{{ field }}</span>
                        <span class="text-[10px] font-bold text-emerald-400 font-mono">{{ (score * 100).toFixed(1) }}%</span>
                    </div>
                    <div class="h-1 w-full bg-white/5 rounded-full overflow-hidden">
                        <div class="h-full bg-emerald-500 rounded-full" :style="{ width: `${score * 100}%` }"></div>
                    </div>
                </div>
            </div>
            <div class="pt-6 border-t border-white/5 flex items-center justify-between">
                <div class="flex items-center gap-2">
                    <div class="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-ping"></div>
                    <span class="text-[9px] font-bold text-emerald-500/80 uppercase tracking-widest">Trust Level: Absolute</span>
                </div>
                <span class="text-[9px] font-mono text-white/20 italic">Hash-Ref: {{ requestId.substring(0,8) }}...</span>
            </div>
        </div>

        <div class="pt-8">
            <NuxtLink to="/" class="sans-action-btn">
                <span>RETURN TO COCKPIT</span>
                <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="3" d="M14 5l7 7m0 0l-7 7m7-7H3" /></svg>
            </NuxtLink>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="errorMessage" class="w-full max-w-2xl bg-red-500/10 border border-red-500/20 px-8 py-6 rounded-[2rem] flex flex-col md:flex-row items-center justify-between gap-6 animate-in slide-in-from-top-8 backdrop-blur-xl">
        <div class="flex items-center gap-6">
            <div class="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center shrink-0">
                <AlertTriangle class="w-6 h-6 text-red-500" />
            </div>
            <div class="space-y-1">
                <h4 class="text-[10px] font-black text-red-500 uppercase tracking-widest">Verification Rejected</h4>
                <p class="text-xs text-white/70 font-medium">{{ errorMessage }}</p>
            </div>
        </div>
        <div class="flex items-center gap-3">
            <button @click="resetFlow" class="px-6 py-2.5 bg-red-500 text-white text-[10px] font-black rounded-xl hover:bg-red-600 transition-all uppercase tracking-widest active:scale-95 shadow-lg shadow-red-500/20">Restart</button>
            <button @click="errorMessage = ''" class="px-5 py-2.5 bg-white/5 text-[10px] font-bold rounded-xl hover:bg-white/10 transition-all uppercase tracking-widest text-white/40">Dismiss</button>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.sans-action-btn {
  @apply bg-primary text-black font-black italic px-10 py-4 rounded-full hover:bg-white transition-all transform hover:scale-105 inline-flex items-center gap-3 shadow-xl shadow-primary/20 cursor-pointer;
}

.glass-container {
  @apply backdrop-blur-3xl;
}

/* Custom Primary Variable for RGB usage in shadow */
:root {
  --primary-rgb: 0, 153, 255; /* Blue fallback */
}
/* Assuming primary is emerald-ish from earlier context, adjusting for SANS style */
.text-primary { color: #00FF94; }
.bg-primary { background-color: #00FF94; }
:root { --primary-rgb: 0, 255, 148; }

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}
</style>

<style scoped>
.sans-button-primary {
  @apply bg-primary text-black font-black italic px-8 py-3 rounded-full hover:bg-white transition-all transform hover:scale-105;
}
</style>
