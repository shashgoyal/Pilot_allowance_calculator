<script setup>
defineProps({
  allowances: Object,
  formatCurrency: Function
})

const allowanceTypes = [
  {
    key: 'tail_swap',
    name: 'Tail Swap',
    icon: '🔄',
    class: 'tail-swap',
    getDetail: (a, fmt) => `${a.tail_swap.count} swaps × ${fmt(a.tail_swap.rate)}`
  },
  {
    key: 'transit',
    name: 'Transit',
    icon: '⏱️',
    class: 'transit',
    getDetail: (a, fmt) => `${a.transit.hours.toFixed(1)}h × ${fmt(a.transit.rate)}/h`
  },
  {
    key: 'layover',
    name: 'Layover',
    icon: '🏨',
    class: 'layover',
    getAmount: (a) => a.layover.total,
    getDetail: (a, fmt) => `${a.layover.count} layovers + ${a.layover.extra_hours.toFixed(1)}h extra`
  },
  {
    key: 'deadhead',
    name: 'Deadhead',
    icon: '💺',
    class: 'deadhead',
    getDetail: (a, fmt) => `${a.deadhead.hours.toFixed(1)}h × ${fmt(a.deadhead.rate)}/h`
  },
  {
    key: 'night',
    name: 'Night Flying',
    icon: '🌙',
    class: 'night',
    getDetail: (a, fmt) => `${a.night.hours.toFixed(1)}h × ${fmt(a.night.rate)}/h`
  }
]
</script>

<template>
  <div class="allowance-summary">
    <div
      v-for="type in allowanceTypes"
      :key="type.key"
      class="allowance-card"
      :class="type.class"
    >
      <div class="allowance-icon">{{ type.icon }}</div>
      <div class="allowance-name">{{ type.name }}</div>
      <div class="allowance-amount">
        {{ formatCurrency(type.getAmount ? type.getAmount(allowances) : allowances[type.key].amount) }}
      </div>
      <div class="allowance-detail">
        {{ type.getDetail(allowances, formatCurrency) }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.allowance-summary {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.allowance-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.allowance-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
}

.allowance-card.tail-swap::before { background: var(--accent-cyan); }
.allowance-card.transit::before { background: var(--accent-emerald); }
.allowance-card.layover::before { background: var(--accent-violet); }
.allowance-card.deadhead::before { background: var(--accent-amber); }
.allowance-card.night::before { background: var(--accent-rose); }

.allowance-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.2);
}

.allowance-icon {
  font-size: 28px;
  margin-bottom: 12px;
}

.allowance-name {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.allowance-amount {
  font-size: 1.5rem;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}

.allowance-card.tail-swap .allowance-amount { color: var(--accent-cyan); }
.allowance-card.transit .allowance-amount { color: var(--accent-emerald); }
.allowance-card.layover .allowance-amount { color: var(--accent-violet); }
.allowance-card.deadhead .allowance-amount { color: var(--accent-amber); }
.allowance-card.night .allowance-amount { color: var(--accent-rose); }

.allowance-detail {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
}
</style>

