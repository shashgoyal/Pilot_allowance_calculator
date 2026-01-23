<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  allowances: Object
})

const filter = ref('')

// Collect all details with type
const allDetails = computed(() => {
  const details = []
  const a = props.allowances

  a.tail_swap.details.forEach(d => {
    details.push({ ...d, type: 'tail-swap', typeName: 'Tail Swap' })
  })
  a.transit.details.forEach(d => {
    details.push({ ...d, type: 'transit', typeName: 'Transit' })
  })
  a.layover.details.forEach(d => {
    details.push({ ...d, type: 'layover', typeName: 'Layover' })
  })
  a.deadhead.details.forEach(d => {
    details.push({ ...d, type: 'deadhead', typeName: 'Deadhead' })
  })
  a.night.details.forEach(d => {
    details.push({ ...d, type: 'night', typeName: 'Night' })
  })

  // Sort by date
  details.sort((a, b) => {
    const [dayA, monthA, yearA] = a.date.split('/').map(Number)
    const [dayB, monthB, yearB] = b.date.split('/').map(Number)
    const dateA = new Date(2000 + (yearA || 0), (monthA || 1) - 1, dayA || 1)
    const dateB = new Date(2000 + (yearB || 0), (monthB || 1) - 1, dayB || 1)
    return dateA - dateB
  })

  return details
})

// Filter details
const filteredDetails = computed(() => {
  if (!filter.value) return allDetails.value
  const f = filter.value.toLowerCase()
  return allDetails.value.filter(d =>
    d.date.toLowerCase().includes(f) ||
    d.typeName.toLowerCase().includes(f) ||
    d.description.toLowerCase().includes(f)
  )
})

// Group by date
const groupedDetails = computed(() => {
  const grouped = {}
  filteredDetails.value.forEach(d => {
    if (!grouped[d.date]) {
      grouped[d.date] = []
    }
    grouped[d.date].push(d)
  })
  return grouped
})
</script>

<template>
  <div class="table-section">
    <div class="table-header">
      <h3>📅 Date-wise Breakdown</h3>
      <input
        v-model="filter"
        type="text"
        class="filter-input"
        placeholder="Filter by date (DD/MM)"
      >
    </div>
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="Object.keys(groupedDetails).length === 0">
            <tr>
              <td colspan="3">
                <div class="empty-state">
                  <div class="empty-state-icon">📭</div>
                  <p>No allowance entries found</p>
                </div>
              </td>
            </tr>
          </template>
          <template v-else>
            <template v-for="(items, date) in groupedDetails" :key="date">
              <tr class="date-group-row">
                <td colspan="3">
                  📅 {{ date }} ({{ items.length }} {{ items.length === 1 ? 'entry' : 'entries' }})
                </td>
              </tr>
              <tr v-for="(item, idx) in items" :key="`${date}-${idx}`">
                <td class="date-cell">{{ item.date }}</td>
                <td>
                  <span class="type-badge" :class="item.type">{{ item.typeName }}</span>
                </td>
                <td class="description-cell">{{ item.description }}</td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.table-section {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  overflow: hidden;
}

.table-header {
  background: var(--bg-secondary);
  padding: 24px 32px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
}

.filter-input {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  padding: 10px 16px;
  color: var(--text-primary);
  font-family: 'Outfit', sans-serif;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.filter-input:focus {
  outline: none;
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.1);
}

.table-container {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  background: var(--bg-secondary);
  padding: 16px 20px;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border-color);
  white-space: nowrap;
}

td {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.95rem;
}

tr:hover td {
  background: var(--bg-hover);
}

.date-cell {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
  color: var(--accent-cyan);
  white-space: nowrap;
}

.description-cell {
  color: var(--text-secondary);
  max-width: 300px;
}

.type-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.type-badge.tail-swap {
  background: rgba(6, 182, 212, 0.15);
  color: var(--accent-cyan);
}

.type-badge.transit {
  background: rgba(16, 185, 129, 0.15);
  color: var(--accent-emerald);
}

.type-badge.layover {
  background: rgba(139, 92, 246, 0.15);
  color: var(--accent-violet);
}

.type-badge.deadhead {
  background: rgba(245, 158, 11, 0.15);
  color: var(--accent-amber);
}

.type-badge.night {
  background: rgba(244, 63, 94, 0.15);
  color: var(--accent-rose);
}

.empty-state {
  text-align: center;
  padding: 60px 24px;
  color: var(--text-muted);
}

.empty-state-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.date-group-row td {
  background: var(--bg-secondary);
  padding: 12px 20px;
  font-weight: 600;
  color: var(--text-primary);
  border-bottom: 2px solid var(--accent-cyan);
}

@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    gap: 16px;
  }

  .filter-input {
    width: 100%;
  }
}
</style>

