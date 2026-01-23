<script setup>
defineProps({
  pilot: Object,
  total: Number,
  formatCurrency: Function
})
</script>

<template>
  <div class="pilot-card">
    <div class="pilot-avatar">👨‍✈️</div>
    <div class="pilot-details">
      <h2>{{ pilot.name }}</h2>
      <div class="pilot-meta">
        <span>🪪 {{ pilot.employee_id }}</span>
        <span>🎖️ {{ pilot.rank_full }}</span>
        <span>🏠 {{ pilot.base }}</span>
        <span>🛩️ {{ pilot.aircraft_type }}</span>
      </div>
    </div>
    <div class="total-card">
      <div class="total-label">Total Allowance</div>
      <div class="total-amount">{{ formatCurrency(total) }}</div>
    </div>
  </div>
</template>

<style scoped>
.pilot-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 32px;
  margin-bottom: 32px;
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 32px;
  align-items: center;
}

.pilot-avatar {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--accent-cyan), var(--accent-violet));
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
}

.pilot-details h2 {
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.pilot-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  color: var(--text-secondary);
}

.pilot-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.95rem;
}

.total-card {
  background: linear-gradient(135deg, var(--accent-emerald), var(--accent-cyan));
  border-radius: 16px;
  padding: 20px 32px;
  text-align: center;
  min-width: 180px;
}

.total-label {
  font-size: 0.85rem;
  font-weight: 500;
  color: rgba(10, 15, 28, 0.7);
  margin-bottom: 4px;
}

.total-amount {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--bg-primary);
  font-family: 'JetBrains Mono', monospace;
}

@media (max-width: 768px) {
  .pilot-card {
    grid-template-columns: 1fr;
    text-align: center;
  }

  .pilot-avatar {
    margin: 0 auto;
  }

  .pilot-meta {
    justify-content: center;
  }

  .total-card {
    margin: 0 auto;
  }
}
</style>

