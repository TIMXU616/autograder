<template>
  <div class="ag-page">
    <h1 class="ag-page-title">评分模板</h1>
    <p class="ag-page-desc">评分模板定义了一份报告要核查哪些评分点、每项多少分</p>

    <el-skeleton v-if="loading" :rows="6" animated />

    <el-empty v-else-if="!templates.length" description="暂无评分模板" />

    <div v-else class="template-grid">
      <div v-for="item in templates" :key="item.template_id" class="ag-card template-card">
        <div class="ag-row-between">
          <h2 class="template-name">{{ item.name }}</h2>
          <el-tag type="primary" effect="light">{{ item.item_count }} 项</el-tag>
        </div>
        <p class="ag-text-secondary">{{ item.description }}</p>

        <ul class="item-list">
          <li v-for="point in item.items" :key="point.name">
            <span>{{ point.name }}</span>
            <span class="ag-text-tertiary">{{ point.full_score }} 分</span>
          </li>
        </ul>

        <el-button class="ag-mt-lg" @click="router.push('/upload')">
          <el-icon><UploadFilled /></el-icon>
          <span>用此模板评阅</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { fetchTemplates } from '@/api'

const router = useRouter()
const loading = ref(true)
const templates = ref([])

onMounted(async () => {
  try {
    const res = await fetchTemplates()
    templates.value = res.list
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--ag-space-lg);
}

.template-card {
  display: flex;
  flex-direction: column;
}

.template-card + .template-card {
  margin-top: 0;
}

.template-name {
  margin: 0;
  font-size: var(--ag-font-size-lg);
  font-weight: var(--ag-font-weight-medium);
}

.item-list {
  margin: var(--ag-space-lg) 0 0;
  padding: 0;
  list-style: none;
  border-top: 1px solid var(--ag-color-border);
}

.item-list li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--ag-space-sm) 0;
  font-size: var(--ag-font-size-sm);
  border-bottom: 1px solid var(--ag-color-border);
}
</style>
