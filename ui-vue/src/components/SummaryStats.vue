<script setup>
defineProps({
  summary: Object
})
</script>

<template>
  <div class="summary-grid">
    <div class="stat-card">
      <div class="stat-value">{{ summary.block_hours || '0:00' }}</div>
      <div class="stat-label">Block Hours</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.duty_hours || '0:00' }}</div>
      <div class="stat-label">Duty Hours</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.operating_flights }}</div>
      <div class="stat-label">Operating Flights</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.deadhead_flights }}</div>
      <div class="stat-label">Deadhead Flights</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.layover_count }}</div>
      <div class="stat-label">Layovers</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.flight_days || '0' }}</div>
      <div class="stat-label">Flight Days</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.off_days || '0' }}</div>
      <div class="stat-label">Off Days</div>
    </div>
    <div class="stat-card">
      <div class="stat-value">{{ summary.standby_days || '0' }}</div>
      <div class="stat-label">Standby Days</div>
    </div>
  </div>
</template>

<style scoped>
.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 16px;
  margin-bottom: 40px;
}

.stat-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  padding: 20px;
  text-align: center;
  transition: all 0.3s ease;
}

.stat-card:hover {
  border-color: var(--accent-cyan);
  transform: translateY(-2px);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-emerald));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>

