<script setup lang="ts">
/**
 * verify/[id].vue
 * Main orchestrator for the identity verification flow.
 */
const route = useRoute()
const requestId = route.params.id as string

type Step = 'init' | 'capture-face' | 'capture-front' | 'capture-back' | 'processing' | 'success' | 'failed'
const currentStep = ref<Step>('capture-face')
const errorMessage = ref('')

const steps = [
  { id: 'capture-face', title: 'Face Verification', desc: 'Securely capture your face for biometric matching.' },
  { id: 'capture-front', title: 'ID Card (Front)', desc: 'Align the front side of your government-issued ID.' },
  { id: 'capture-back', title: 'ID Card (Back)', desc: 'Align the back side of your government-issued ID.' }
]

const handleCapture = async (blob: Blob) => {
    // Determine target endpoint based on step
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

        // Assuming Backend is at port 8010
        const result = await $fetch(`http://localhost:8010${endpoint}${queryParams}`, {
            method: 'POST',
            body: formData
        })

        // Progress to next step
        if (currentStep.value === 'capture-face') {
            currentStep.value = 'capture-front'
        } else if (currentStep.value === 'capture-front') {
            currentStep.value = 'capture-back'
        } else {
            currentStep.value = 'success'
        }
    } catch (err: any) {
        errorMessage.value = "Cloud processing failed. Please try again."
        console.error(err)
    }
}
</script>

<template>
  <div class="min-h-screen bg-[#0A0A0A] text-white flex flex-col font-sans">
    <!-- Header -->
    <header class="p-8 flex justify-between items-center border-b border-white/5">
      <div class="flex items-center gap-2">
        <div class="w-2 h-8 bg-primary rounded-full"></div>
        <h1 class="text-xl font-bold tracking-widest text-primary">SANS IDENTITY</h1>
      </div>
      <div class="text-xs font-mono text-white/40 uppercase tracking-tighter">
        SESSION: {{ requestId }}
      </div>
    </header>

    <main class="flex-1 flex flex-col items-center justify-center p-6 space-y-12 max-w-5xl mx-auto w-full">
      
      <!-- Progress Stepper -->
      <div class="w-full flex justify-between max-w-md">
         <div v-for="(s, index) in steps" :key="s.id" class="flex flex-col items-center gap-2">
            <div 
              class="w-3 h-3 rounded-full transition-all duration-500"
              :class="[
                currentStep === s.id ? 'bg-primary scale-150 ring-4 ring-primary/20' : 
                steps.findIndex(x => x.id === currentStep) > index ? 'bg-green-500' : 'bg-white/10'
              ]"
            ></div>
         </div>
      </div>

      <div v-if="currentStep.startsWith('capture')" class="w-full space-y-8 animate-in fade-in slide-in-from-bottom-10 duration-700">
        <div class="text-center">
            <h2 class="text-3xl font-black italic tracking-tight">{{ steps.find(s => s.id === currentStep)?.title }}</h2>
            <p class="text-white/50 mt-2">{{ steps.find(s => s.id === currentStep)?.desc }}</p>
        </div>

        <VerificationCaptureContainer 
            :mode="currentStep === 'capture-face' ? 'face' : 'card'"
            :title="steps.find(s => s.id === currentStep)?.title || ''"
            :description="steps.find(s => s.id === currentStep)?.desc || ''"
            @capture="handleCapture"
        />
      </div>

      <!-- Result States -->
      <div v-else-if="currentStep === 'success'" class="text-center space-y-6 max-w-md py-20 animate-in zoom-in duration-500">
        <div class="w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
            <div class="w-12 h-12 bg-green-500 rounded-full"></div>
        </div>
        <h2 class="text-4xl font-black italic tracking-tight">VERIFICATION COMPLETE</h2>
        <p class="text-white/50">Your identity documents have been securely processed. You may now close this window or return to the main application.</p>
        <div class="pt-10">
            <NuxtLink to="/" class="sans-button-primary">RETURN TO COCKPIT</NuxtLink>
        </div>
      </div>

      <div v-if="errorMessage" class="text-red-500 bg-red-500/10 border border-red-500/20 px-6 py-4 rounded-2xl flex items-center gap-4">
        <span class="font-bold underline">ERROR:</span> {{ errorMessage }}
        <button @click="errorMessage = ''" class="ml-4 opacity-50 hover:opacity-100 italic transition-all">DISMISS</button>
      </div>
    </main>

    <!-- Footer Security -->
    <footer class="p-8 text-center text-[10px] text-white/20 uppercase tracking-[0.2em]">
      Secured by SANS-Way Distributed Ledger & biometric Hash encryption
    </footer>
  </div>
</template>

<style scoped>
.sans-button-primary {
  @apply bg-primary text-black font-black italic px-8 py-3 rounded-full hover:bg-white transition-all transform hover:scale-105;
}
</style>
