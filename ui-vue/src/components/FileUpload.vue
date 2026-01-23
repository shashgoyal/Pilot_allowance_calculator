<script setup>
import { ref } from 'vue'

const props = defineProps({
  title: String,
  icon: String,
  badge: String,
  badgeType: String,
  accept: String,
  placeholder: String
})

const emit = defineEmits(['file-selected'])

const isDragging = ref(false)
const selectedFile = ref(null)
const fileInput = ref(null)

const handleClick = () => {
  fileInput.value?.click()
}

const handleDragOver = (e) => {
  e.preventDefault()
  isDragging.value = true
}

const handleDragLeave = () => {
  isDragging.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  isDragging.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    selectFile(file)
  }
}

const handleFileChange = (e) => {
  const file = e.target.files[0]
  if (file) {
    selectFile(file)
  }
}

const selectFile = (file) => {
  selectedFile.value = file
  emit('file-selected', file)
}
</script>

<template>
  <div class="upload-card" :class="badgeType">
    <div class="upload-label">
      <h3>{{ icon }} {{ title }}</h3>
      <span class="badge" :class="badgeType">{{ badge }}</span>
    </div>
    <div
      class="dropzone"
      :class="{ dragover: isDragging, 'has-file': selectedFile }"
      @click="handleClick"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
    >
      <template v-if="selectedFile">
        <div class="dropzone-icon">✅</div>
        <p>File selected:</p>
        <div class="file-name">{{ selectedFile.name }}</div>
      </template>
      <template v-else>
        <div class="dropzone-icon">📁</div>
        <p>{{ placeholder }}<br>or click to browse</p>
      </template>
      <input
        ref="fileInput"
        type="file"
        :accept="accept"
        @change="handleFileChange"
      >
    </div>
  </div>
</template>

<style scoped>
.upload-card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: 20px;
  padding: 32px;
  transition: all 0.3s ease;
}

.upload-card:hover {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 40px rgba(6, 182, 212, 0.1);
}

.upload-card.required {
  border-left: 4px solid var(--accent-cyan);
}

.upload-card.optional {
  border-left: 4px solid var(--accent-violet);
}

.upload-label {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.upload-label h3 {
  font-size: 1.25rem;
  font-weight: 600;
}

.badge {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.badge.required {
  background: rgba(6, 182, 212, 0.15);
  color: var(--accent-cyan);
}

.badge.optional {
  background: rgba(139, 92, 246, 0.15);
  color: var(--accent-violet);
}

.dropzone {
  border: 2px dashed var(--border-color);
  border-radius: 16px;
  padding: 40px 24px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(17, 24, 39, 0.5);
}

.dropzone:hover,
.dropzone.dragover {
  border-color: var(--accent-cyan);
  background: rgba(6, 182, 212, 0.05);
}

.dropzone.has-file {
  border-color: var(--success);
  background: rgba(34, 197, 94, 0.05);
}

.dropzone-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.dropzone p {
  color: var(--text-secondary);
  font-size: 0.95rem;
}

.file-name {
  color: var(--success);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  margin-top: 8px;
  word-break: break-all;
}

input[type="file"] {
  display: none;
}
</style>

