<script setup>
import { ref, computed } from 'vue'
import FileUpload from './components/FileUpload.vue'
import PilotCard from './components/PilotCard.vue'
import SummaryStats from './components/SummaryStats.vue'
import AllowanceCards from './components/AllowanceCards.vue'
import DatewiseTable from './components/DatewiseTable.vue'

// Configuration
const API_URL = 'http://localhost:8043'

// State
const scheduleFile = ref(null)
const logbookFile = ref(null)
const isLoading = ref(false)
const error = ref('')
const result = ref(null)

// Computed
const canCalculate = computed(() => scheduleFile.value !== null)

// Methods
const handleScheduleFile = (file) => {
  scheduleFile.value = file
}

const handleLogbookFile = (file) => {
  logbookFile.value = file
}

const calculateAllowances = async () => {
  isLoading.value = true
  error.value = ''
  result.value = null

  try {
    const formData = new FormData()
    formData.append('schedule_pdf', scheduleFile.value)
    if (logbookFile.value) {
      formData.append('logbook_pdf', logbookFile.value)
    }

    const response = await fetch(`${API_URL}/calculate`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json()
      throw new Error(errorData.detail || 'Failed to calculate allowances')
    }

    result.value = await response.json()
  } catch (err) {
    error.value = err.message
  } finally {
    isLoading.value = false
  }
}

const formatCurrency = (amount) => {
  return '₹' + Math.round(amount).toLocaleString('en-IN')
}
</script>

<template>
  <div class="app">
    <div class="bg-pattern"></div>
    <div class="grid-lines"></div>

    <div class="container">
      <!-- Header -->
      <header>
        <div class="logo">
          <div class="logo-icon">✈️</div>
          <h1>Pilot Allowance Calculator</h1>
        </div>
        <p class="subtitle">Upload your schedule files to calculate allowances</p>
      </header>

      <!-- Upload Section -->
      <section class="upload-section">
        <FileUpload
          title="Schedule Report"
          icon="📄"
          badge="Required"
          badge-type="required"
          accept=".pdf"
          placeholder="Drag & drop your ScheduleReport.pdf"
          @file-selected="handleScheduleFile"
        />
        <FileUpload
          title="Logbook Report"
          icon="📋"
          badge="Optional"
          badge-type="optional"
          accept=".pdf,.xls"
          placeholder="Drag & drop your JarfclrpReport.pdf"
          @file-selected="handleLogbookFile"
        />
      </section>

      <!-- Action Section -->
      <section class="action-section">
        <div v-if="error" class="error-message">
          {{ error }}
        </div>
        <button
          class="calculate-btn"
          :class="{ loading: isLoading }"
          :disabled="!canCalculate || isLoading"
          @click="calculateAllowances"
        >
          Calculate Allowances
        </button>
      </section>

      <!-- Results Section -->
      <section v-if="result" class="results-section">
        <PilotCard
          :pilot="result.pilot_info"
          :total="result.allowances.total_amount"
          :format-currency="formatCurrency"
        />

        <SummaryStats :summary="result.summary" />

        <AllowanceCards
          :allowances="result.allowances"
          :format-currency="formatCurrency"
        />

        <DatewiseTable :allowances="result.allowances" />
      </section>

      <!-- Footer -->
      <footer>
        <p>
          Pilot Allowance Calculator v1.0 |
          API runs on <a href="http://localhost:8043/docs" target="_blank">localhost:8043</a>
        </p>
      </footer>
    </div>
  </div>
</template>

<style>
:root {
  --bg-primary: #0a0f1c;
  --bg-secondary: #111827;
  --bg-card: #1a2234;
  --bg-hover: #243049;
  --accent-cyan: #06b6d4;
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;
  --accent-violet: #8b5cf6;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --border-color: #334155;
  --success: #22c55e;
  --error: #ef4444;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Outfit', sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
}

.app {
  position: relative;
}

.bg-pattern {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background: 
    radial-gradient(ellipse at 20% 20%, rgba(6, 182, 212, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 80%, rgba(139, 92, 246, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 50%, rgba(16, 185, 129, 0.04) 0%, transparent 50%);
}

.grid-lines {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  background-image: 
    linear-gradient(rgba(51, 65, 85, 0.15) 1px, transparent 1px),
    linear-gradient(90deg, rgba(51, 65, 85, 0.15) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(ellipse at center, black 40%, transparent 80%);
}

.container {
  position: relative;
  z-index: 1;
  max-width: 1400px;
  margin: 0 auto;
  padding: 40px 24px;
}

header {
  text-align: center;
  margin-bottom: 48px;
  animation: fadeInDown 0.6s ease-out;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.logo {
  display: inline-flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.logo-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-emerald));
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  box-shadow: 0 8px 32px rgba(6, 182, 212, 0.3);
}

h1 {
  font-size: 2.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, var(--text-primary), var(--accent-cyan));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 1.1rem;
  font-weight: 300;
}

.upload-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
  animation: fadeInUp 0.6s ease-out 0.2s both;
}

.action-section {
  text-align: center;
  margin-bottom: 48px;
  animation: fadeInUp 0.6s ease-out 0.4s both;
}

.error-message {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid var(--error);
  border-radius: 12px;
  padding: 16px 24px;
  color: var(--error);
  margin-bottom: 24px;
  animation: shake 0.4s ease;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-8px); }
  75% { transform: translateX(8px); }
}

.calculate-btn {
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-emerald));
  color: var(--bg-primary);
  border: none;
  padding: 18px 48px;
  font-size: 1.1rem;
  font-weight: 600;
  font-family: 'Outfit', sans-serif;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(6, 182, 212, 0.3);
}

.calculate-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 40px rgba(6, 182, 212, 0.4);
}

.calculate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.calculate-btn.loading {
  position: relative;
  color: transparent;
}

.calculate-btn.loading::after {
  content: '';
  position: absolute;
  width: 24px;
  height: 24px;
  top: 50%;
  left: 50%;
  margin: -12px 0 0 -12px;
  border: 3px solid rgba(10, 15, 28, 0.3);
  border-top-color: var(--bg-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.results-section {
  animation: fadeInUp 0.6s ease-out;
}

footer {
  text-align: center;
  padding: 40px 24px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

footer a {
  color: var(--accent-cyan);
  text-decoration: none;
}

footer a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .container {
    padding: 24px 16px;
  }

  h1 {
    font-size: 1.75rem;
  }
}
</style>

