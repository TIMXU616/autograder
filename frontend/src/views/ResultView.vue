<template>
  <div class="ag-page">
    <div class="ag-row ag-page-head">
      <el-button text @click="router.push('/reports')">
        <el-icon><ArrowLeft /></el-icon>
        <span>返回成绩列表</span>
      </el-button>
    </div>

    <el-skeleton v-if="loading" :rows="8" animated />

    <el-empty v-else-if="error" :description="error">
      <el-button type="primary" @click="load">重新加载</el-button>
    </el-empty>

    <template v-else>
      <h1 class="ag-page-title">评阅结果</h1>
      <p class="ag-page-desc">
        {{ result.file_name }} · {{ result.student }} · {{ result.template_name }} ·
        {{ result.created_at }}
      </p>

      <div class="ag-card">
        <div class="score-head">
          <div class="score-main">
            <p class="ag-text-secondary">总分</p>
            <p class="score-value" :class="scoreClass">
              {{ result.total_score }}
              <span class="score-full">/ {{ result.full_score }}</span>
            </p>
          </div>
          <div class="score-rate">
            <p class="ag-text-secondary">得分率</p>
            <el-progress
              type="dashboard"
              :percentage="scoreRate"
              :color="scoreColor"
              :width="132"
            />
          </div>
        </div>
      </div>

      <div class="ag-card">
        <h2 class="ag-card-title">评分点逐项核查</h2>
        <el-table :data="result.items" stripe style="width: 100%">
          <el-table-column prop="name" label="评分点" width="190" />
          <el-table-column label="得分" width="110">
            <template #default="{ row }">
              <span class="item-score">{{ row.score }}</span>
              <span class="ag-text-tertiary"> / {{ row.full_score }}</span>
            </template>
          </el-table-column>
          <el-table-column label="得分率" width="160">
            <template #default="{ row }">
              <el-progress
                :percentage="percentOf(row)"
                :stroke-width="8"
                :color="barColor(row)"
                :show-text="false"
              />
            </template>
          </el-table-column>
          <el-table-column prop="reason" label="判定依据" min-width="260" />
          <el-table-column prop="evidence" label="依据出处" width="180">
            <template #default="{ row }">
              <span class="ag-text-tertiary">{{ row.evidence }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="ag-card">
        <h2 class="ag-card-title">总评与建议</h2>
        <p class="ag-comment">{{ result.comment }}</p>

        <div class="ag-feedback">
          <div class="ag-feedback-block">
            <p class="ag-feedback-title">
              <el-icon :size="16"><CircleCheck /></el-icon>
              <span>亮点</span>
            </p>
            <ul>
              <li v-for="item in result.highlights" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div class="ag-feedback-block">
            <p class="ag-feedback-title">
              <el-icon :size="16"><Star /></el-icon>
              <span>改进建议</span>
            </p>
            <ul>
              <li v-for="item in result.suggestions" :key="item">{{ item }}</li>
            </ul>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CircleCheck, Star } from '@element-plus/icons-vue'
import { fetchReportResult } from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const result = ref(null)

const scoreRate = computed(() =>
  result.value ? Math.round((result.value.total_score / result.value.full_score) * 100) : 0
)

const scoreColor = computed(() => {
  const rate = scoreRate.value
  if (rate >= 85) return 'var(--ag-color-success)'
  if (rate >= 70) return 'var(--ag-color-primary)'
  if (rate >= 60) return 'var(--ag-color-warning)'
  return 'var(--ag-color-danger)'
})

const scoreClass = computed(() => {
  const rate = scoreRate.value
  if (rate >= 85) return 'is-good'
  if (rate >= 60) return 'is-normal'
  return 'is-poor'
})

function percentOf(row) {
  return Math.round((row.score / row.full_score) * 100)
}

function barColor(row) {
  const percent = percentOf(row)
  if (percent >= 85) return 'var(--ag-color-success)'
  if (percent >= 60) return 'var(--ag-color-primary)'
  return 'var(--ag-color-warning)'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    result.value = await fetchReportResult(route.params.id)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.ag-page-head {
  margin-bottom: var(--ag-space-md);
}

.score-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ag-space-2xl);
  flex-wrap: wrap;
}

.score-main p {
  margin: 0;
}

.score-value {
  font-size: var(--ag-font-size-display);
  font-weight: var(--ag-font-weight-medium);
  line-height: 1.2;
}

.score-value.is-good {
  color: var(--ag-color-success);
}

.score-value.is-normal {
  color: var(--ag-color-primary);
}

.score-value.is-poor {
  color: var(--ag-color-warning);
}

.score-full {
  font-size: var(--ag-font-size-base);
  color: var(--ag-color-text-tertiary);
  font-weight: var(--ag-font-weight-normal);
}

.score-rate p {
  margin: 0 0 var(--ag-space-sm);
}

.item-score {
  font-weight: var(--ag-font-weight-medium);
}

.ag-comment {
  margin: 0;
  color: var(--ag-color-text-secondary);
}

.ag-feedback {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--ag-space-lg);
  margin-top: var(--ag-space-xl);
}

.ag-feedback-block {
  background: var(--ag-color-primary-weak);
  border-radius: var(--ag-radius-md);
  padding: var(--ag-space-lg);
}

.ag-feedback-title {
  display: flex;
  align-items: center;
  gap: var(--ag-space-xs);
  margin: 0 0 var(--ag-space-sm);
  font-weight: var(--ag-font-weight-medium);
}

.ag-feedback-block ul {
  margin: 0;
  padding-left: var(--ag-space-lg);
  color: var(--ag-color-text-secondary);
  font-size: var(--ag-font-size-sm);
}
</style>
