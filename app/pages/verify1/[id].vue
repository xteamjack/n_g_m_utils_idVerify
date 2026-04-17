<script setup lang="ts">
/**
 * verify1/[id].vue
 * Streamlined variant: Combines Face and ID Front capture into one side-by-side photo.
 */
const route = useRoute()
const requestId = route.params.id as string

type Step = 'capture-combined' | 'capture-back' | 'processing' | 'success' | 'failed'
const currentStep = ref<Step>('capture-combined')
const errorMessage = ref('')
const extractedData = ref<any>(null)
const matchResults = ref<any>(null)

const steps = [
  { id: 'capture-combined', title: 'Face & ID (Front)', desc: 'Align both your face (left) and ID card (right) in the frame.' },
  { id: 'capture-back', title: 'ID Card (Back)', desc: 'Align the back side of your government-issued ID.' }
]

const resetFlow = () => {
    errorMessage.value = ''
    currentStep.value = 'capture-combined'
    extractedData.value = null
    matchResults.value = null
}

const handleCapture = async (blob: Blob) => {
    let endpoint = ''
    let queryParams = `?request_id=${requestId}`
    
    if (currentStep.value === 'capture-combined') {
        endpoint = '/verify/capture/combined'
    } else {
        endpoint = '/verify/capture/card'
        queryParams += `&side=back`
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

        // Store results
        if (result.ocr) {
            extractedData.value = result.ocr.raw_text
        }
        if (result.matching) {
            matchResults.value = result.matching
        }

        // Step transition
        if (currentStep.value === 'capture-combined') {
            currentStep.value = 'capture-back'
        } else {
            currentStep.value = 'processing'
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
  <div class="min-h-screen bg-[#050505] text-white flex flex-col font-sans selection:bg-primary/30">
    <header class="p-8 flex justify-between items-center border-b border-white/5">
      <div class="flex items-center gap-2">
        <div class="w-2 h-8 bg-primary rounded-full shadow-[0_0_15px_rgba(var(--color-primary-rgb),0.5)]"></div>
        <h1 class="text-xl font-black tracking-widest text-primary italic">SANS SECURE</h1>
      </div>
      <div class="text-[10px] font-mono text-white/30 uppercase tracking-[0.3em]">
        SESSION: {{ requestId }} // COMBINED_MODE_V1
      </div>
    </header>

    <main class="flex-1 flex flex-col items-center justify-center p-6 space-y-12 max-w-6xl mx-auto w-full">
      
      <!-- Progress -->
      <div class="flex gap-2">
         <div v-for="s in steps" :key="s.id" 
            class="h-1 w-20 rounded-full transition-all duration-700"
            :class="[currentStep === s.id ? 'bg-primary shadow-[0_0_10px_rgba(var(--color-primary-rgb),0.5)]' : 'bg-white/5']"
         ></div>
      </div>

      <div v-if="currentStep.startsWith('capture')" class="w-full space-y-8 animate-in fade-in slide-in-from-bottom-5 duration-700">
        <div class="text-center">
            <h2 class="text-4xl font-black italic tracking-tighter uppercase">{{ steps.find(s => s.id === currentStep)?.title }}</h2>
            <p class="text-white/40 mt-1 text-sm font-medium tracking-wide">{{ steps.find(s => s.id === currentStep)?.desc }}</p>
        </div>

        <!-- Use Combined Container for Step 1, Standard for Step 2 -->
        <VerificationCaptureContainerCombined 
            v-if="currentStep === 'capture-combined'"
            :title="steps[0].title"
            :description="steps[0].desc"
            @capture="handleCapture"
        />
        <VerificationCaptureContainer 
            v-else
            mode="card"
            :title="steps[1].title"
            :description="steps[1].desc"
            @capture="handleCapture"
        />
      </div>

      <!-- Processing -->
      <div v-else-if="currentStep === 'processing'" class="text-center space-y-10 py-20">
        <div class="relative w-40 h-40 mx-auto">
            <div class="absolute inset-0 border-2 border-primary/10 rounded-full"></div>
            <div class="absolute inset-0 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
            <div class="absolute inset-0 flex items-center justify-center">
                <span class="text-primary font-black italic text-2xl animate-pulse">SANS</span>
            </div>
        </div>
        <div class="space-y-3">
            <h2 class="text-3xl font-black italic tracking-tighter uppercase">Unified Biometric Audit</h2>
            <p class="text-white/20 uppercase text-[10px] tracking-[0.5em] font-bold">Executing multi-layer OCR & biometric hashing</p>
        </div>
      </div>

      <!-- Success -->
      <div v-else-if="currentStep === 'success'" class="text-center space-y-8 max-w-xl animate-in zoom-in-95 duration-700">
        <div class="w-32 h-32 bg-primary/10 rounded-full flex items-center justify-center mx-auto border border-primary/20">
            <div class="w-16 h-16 bg-primary rounded-full shadow-[0_0_40px_rgba(var(--color-primary-rgb),0.8)]"></div>
        </div>
        <div class="space-y-2">
            <h2 class="text-5xl font-black italic tracking-tighter">VERIFICATION COMPLETE</h2>
            <p class="text-white/40 font-medium">Identity matches established profile with high confidence.</p>
        </div>
        
        <div v-if="matchResults" class="bg-white/[0.02] border border-white/5 rounded-[2rem] p-8 text-left space-y-6">
            <div class="grid grid-cols-2 gap-6">
                <div v-for="(score, field) in matchResults.match_scores" :key="field" class="space-y-1">
                    <div class="text-[9px] text-white/30 uppercase font-bold tracking-widest">{{ field }}</div>
                    <div class="flex items-center gap-2">
                        <div class="h-1 flex-1 bg-white/5 rounded-full overflow-hidden">
                            <div class="h-full bg-primary" :style="{ width: (score * 100) + '%' }"></div>
                        </div>
                        <span class="text-[10px] font-mono text-primary">{{ (score * 100).toFixed(0) }}%</span>
                    </div>
                </div>
            </div>
        </div>

        <div class="pt-8 flex justify-center gap-4">
            <button @click="resetFlow" class="px-8 py-3 border border-white/10 rounded-full text-xs font-bold hover:bg-white/5 transition-all">RETRY</button>
            <NuxtLink to="/" class="px-8 py-3 bg-primary text-black font-black italic rounded-full hover:scale-105 transition-all">DASHBOARD</NuxtLink>
        </div>
      </div>

      <!-- Error -->
      <div v-if="errorMessage" class="fixed bottom-10 left-1/2 -translate-x-1/2 w-full max-w-2xl px-6 animate-in slide-in-from-bottom-10">
        <div class="bg-red-900/90 backdrop-blur-xl border border-red-500/30 p-4 rounded-2xl flex items-center justify-between shadow-2xl shadow-red-500/20">
            <div class="flex items-center gap-4 text-red-100">
                <div class="w-8 h-8 bg-red-500 rounded-full flex items-center justify-center font-black">!</div>
                <div class="text-sm font-bold italic tracking-tight uppercase">{{ errorMessage }}</div>
            </div>
            <div class="flex gap-2">
                <button @click="resetFlow" class="px-4 py-2 bg-red-500 text-white text-[10px] font-black italic rounded-lg">RESTART</button>
                <button @click="errorMessage = ''" class="px-4 py-2 bg-white/10 text-white text-[10px] font-bold rounded-lg uppercase">Dismiss</button>
            </div>
        </div>
      </div>
    </main>

    <footer class="p-8 text-center text-[9px] text-white/10 uppercase tracking-[0.4em] font-bold">
      Encrypted Session // Peer-to-Peer Biometric Validation Protocol
    </footer>
  </div>
</template>

<style scoped>
.selection\:bg-primary\/30 ::selection {
  background-color: rgba(var(--color-primary-rgb), 0.3);
}
</style>
