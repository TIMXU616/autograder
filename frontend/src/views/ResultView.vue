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

    <!-- 评阅进行中：直接访问结果页时的兜底 -->
    <div v-else-if="result.in_flight" class="ag-card">
      <h2 class="ag-card-title">评阅进行中</h2>
      <el-progress :percentage="60" :stroke-width="10" striped :show-text="false" />
      <p class="ag-text-secondary ag-mt-lg">{{ result.stage_text || '正在评阅，请稍候…' }}</p>
    </div>

    <!-- 评阅失败：展示错误码与原因（系统对失败可观测） -->
    <el-result
      v-else-if="result.is_failed"
      icon="error"
      title="评阅失败"
      :sub-title="`${result.error_text || '未知错误'}（错误码 ${result.error_code ?? '—'}）`"
    >
      <template #extra>
        <el-button @click="router.push('/upload')">重新上传报告</el-button>
      </template>
    </el-result>

    <template v-else>
      <h1 class="ag-page-title">评阅结果</h1>
      <p class="ag-page-desc">
        {{ result.file_name }} · {{ result.student }} · {{ result.template_name }} ·
        {{ result.created_at }}
      </p>

      <el-alert
        v-if="result.warnings.length"
        type="warning"
        :closable="false"
        class="ag-mb-lg"
        title="本次评阅存在未完成的评分点"
      >
        <ul class="warn-list">
          <li v-for="text in result.warnings" :key="text">{{ text }}</li>
        </ul>
      </el-alert>

      <div class="ag-card">
        <div class="score-head">
          <div class="score-main">
            <p class="ag-text-secondary">总分</p>
            <p class="score-value" :class="scoreClass">
              {{ result.total_score }}
              <span class="score-full">/ {{ result.full_score }}</span>
            </p>
            <p class="ag-text-tertiary">
              模型 {{ result.model }} · 第 {{ result.attempt_no }} 次评阅
              <template v-if="result.consistency !== null">
                · 两次评阅差值 {{ result.consistency }}
              </template>
            </p>
          </div>
          <div class="score-rate">
            <p class="ag-text-secondary">得分率</p>
            <el-progress
              type="dashboard"
              :percentage="result.score_rate"
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
          <el-table-column label="得分" width="130">
            <template #default="{ row }">
              <template v-if="row.score !== null">
                <span class="item-score">{{ row.score }}</span>
                <span class="ag-text-tertiary"> / {{ row.full_score }}</span>
              </template>
              <el-tag v-else type="danger" effect="light">{{ row.status_text }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="等级" width="110">
            <template #default="{ row }">
              <el-tag v-if="row.level" :type="row.level_tag" effect="light">
                {{ row.level_text }}
              </el-tag>
              <span v-else class="ag-text-tertiary">—</span>
            </template>
          </el-table-column>
          <el-table-column label="得分率" width="130">
            <template #default="{ row }">
              <el-progress
                v-if="row.rate !== null"
                :percentage="row.rate"
                :stroke-width="8"
                :color="barColor(row)"
                :show-text="false"
              />
              <span v-else class="ag-text-tertiary">—</span>
            </template>
          </el-table-column>
          <el-table-column label="判定依据" min-width="250">
            <template #default="{ row }">
              <span>{{ row.reason }}</span>
              <el-tag
                v-if="row.confidence === 'low'"
                size="small"
                type="info"
                effect="plain"
                class="ag-ml-sm"
              >
                置信度低
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="原文依据" min-width="270">
            <template #default="{ row }">
              <template v-if="row.evidence">
                <span class="evidence">“{{ row.evidence }}”</span>
                <el-button link type="primary" size="small" @click="openSource(row)">
                  查看原文
                </el-button>
              </template>
              <span v-else class="ag-text-tertiary">未命中原文，未采信</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="ag-card">
        <h2 class="ag-card-title">
          总评与建议
          <span v-if="result.summary_source === 'derived'" class="ag-text-tertiary summary-note">
            由评分结果自动汇总
          </span>
        </h2>
        <p class="ag-comment">{{ result.comment }}</p>

        <div class="ag-feedback">
          <div class="ag-feedback-block">
            <p class="ag-feedback-title">
              <el-icon :size="16"><CircleCheck /></el-icon>
              <span>亮点</span>
            </p>
            <ul v-if="result.highlights.length">
              <li v-for="text in result.highlights" :key="text">{{ text }}</li>
            </ul>
            <p v-else class="ag-text-tertiary">暂无</p>
          </div>
          <div class="ag-feedback-block">
            <p class="ag-feedback-title">
              <el-icon :size="16"><Star /></el-icon>
              <span>改进建议</span>
            </p>
            <ul v-if="result.suggestions.length">
              <li v-for="text in result.suggestions" :key="text">{{ text }}</li>
            </ul>
            <p v-else class="ag-text-tertiary">暂无</p>
          </div>
        </div>
      </div>

      <!-- 原文依据抽屉：点「查看原文」才按需拉取，/text 未上线/报告未解析完都不报错 -->
      <el-drawer v-model="drawer.visible" title="原文依据核查" size="520px">
        <div v-if="drawer.loading" class="ag-text-secondary">正在读取报告原文…</div>

        <template v-else>
          <p class="drawer-title">{{ drawer.item?.name }}</p>

          <!-- 接口不可用 / 报告还没解析完：如实说明，不假装成功 -->
          <el-alert
            v-if="drawer.mode === 'unavailable'"
            type="info"
            :closable="false"
            show-icon
            :title="drawer.message"
          />

          <template v-else>
            <div class="drawer-block">
              <p class="ag-text-secondary">本项引用的原文片段</p>
              <blockquote class="drawer-quote">“{{ drawer.item?.evidence }}”</blockquote>
            </div>

            <div class="drawer-block">
              <p class="ag-text-secondary">在报告正文中的位置</p>
              <p v-if="drawer.mode === 'located'" class="drawer-text">
                …{{ parts.before }}<mark class="drawer-hit">{{ parts.hit }}</mark>{{ parts.after }}…
              </p>
              <p v-else class="ag-text-tertiary">
                未能在当前正文中定位到该片段（多为换行/空格差异导致）。上方引文仍以后端返回为准。
              </p>
            </div>
          </template>
        </template>
      </el-drawer>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ArrowLeft, CircleCheck, Star } from '@element-plus/icons-vue'
import {
  fetchReportResult,
  waitForResult,
  fetchReportText,
  evidenceContext
} from '@/api'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref('')
const result = ref(null)

/* ---------- 原文依据抽屉 ----------
   /text 有三种「还没好」的情形必须分开处理（见 api/index.js fetchReportText）：
     · 路由未注册   → 框架级 404，响应体没有业务 code
     · 报告还在解析 → HTTP 200 + code 4090（axios 判成功，不能直接当有原文渲染）
     · 解析失败     → HTTP 200 + code 4003 / 4005
   任何一种都不能当成「有原文」，否则抽屉里会出现空对象。 */
const drawer = reactive({
  visible: false,
  loading: false,
  item: null,
  mode: '', // located（已定位）| not-found（拉到正文但没匹配上）| unavailable（接口/报告不可用）
  message: '',
  snippet: '',
  hit: ''
})
const sourceText = ref('')

/* 把上下文片段按命中位置切三段，中间那段加高亮 */
const parts = computed(() => {
  const { snippet, hit } = drawer
  if (!snippet || !hit) return { before: snippet, hit: '', after: '' }
  const at = snippet.indexOf(hit)
  if (at < 0) return { before: snippet, hit: '', after: '' }
  return { before: snippet.slice(0, at), hit, after: snippet.slice(at + hit.length) }
})

/* 点「查看原文」才拉接口 —— 不做进页面就预加载（现在必 404，会平白报错） */
async function openSource(row) {
  drawer.visible = true
  drawer.item = row
  drawer.mode = ''
  drawer.message = ''
  drawer.snippet = ''
  drawer.hit = ''

  /* 报告正文只拉一次，多个评分项共用 */
  if (!sourceText.value) {
    drawer.loading = true
    const res = await fetchReportText(route.params.id)
    drawer.loading = false
    if (!res.ok) {
      drawer.mode = 'unavailable'
      drawer.message = res.message
      return
    }
    sourceText.value = res.text
  }

  const ctx = evidenceContext(sourceText.value, row.evidence)
  if (ctx) {
    drawer.mode = 'located'
    drawer.snippet = ctx.snippet
    drawer.hit = sourceText.value.slice(ctx.hit_start, ctx.hit_end)
  } else {
    drawer.mode = 'not-found'
  }
}

const scoreColor = computed(() => {
  const rate = result.value?.score_rate ?? 0
  if (rate >= 90) return 'var(--ag-color-success)'
  if (rate >= 70) return 'var(--ag-color-primary)'
  if (rate >= 50) return 'var(--ag-color-warning)'
  return 'var(--ag-color-danger)'
})

const scoreClass = computed(() => {
  const rate = result.value?.score_rate ?? 0
  if (rate >= 90) return 'is-good'
  if (rate >= 50) return 'is-normal'
  return 'is-poor'
})

/* 色带与契约 5.3 的 level 口径一致：90 / 70 / 50 */
function barColor(row) {
  if (row.rate >= 90) return 'var(--ag-color-success)'
  if (row.rate >= 70) return 'var(--ag-color-primary)'
  if (row.rate >= 50) return 'var(--ag-color-warning)'
  return 'var(--ag-color-danger)'
}

async function load() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchReportResult(route.params.id)
    result.value = data
    /* 评阅未结束时继续轮询，直到出分或失败 */
    if (data.in_flight) {
      result.value = await waitForResult(route.params.id, { interval: 2000 })
    }
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

.evidence {
  color: var(--ag-color-text-secondary);
  font-size: var(--ag-font-size-sm);
}

.drawer-title {
  margin: 0 0 var(--ag-space-lg);
  font-weight: var(--ag-font-weight-medium);
}

.drawer-block {
  margin-bottom: var(--ag-space-xl);
}

.drawer-block > p {
  margin: 0 0 var(--ag-space-sm);
}

.drawer-quote {
  margin: 0;
  padding: var(--ag-space-sm) var(--ag-space-md);
  border-left: 3px solid var(--ag-color-primary);
  background: var(--ag-color-primary-weak);
  border-radius: var(--ag-radius-md);
  color: var(--ag-color-text-secondary);
  font-size: var(--ag-font-size-sm);
}

.drawer-text {
  margin: 0;
  padding: var(--ag-space-md);
  background: var(--ag-color-bg-hover);
  border-radius: var(--ag-radius-md);
  line-height: 1.9;
  font-size: var(--ag-font-size-sm);
  word-break: break-word;
}

.drawer-hit {
  background: var(--ag-color-warning-weak);
  color: var(--ag-color-warning);
  font-weight: var(--ag-font-weight-medium);
  padding: 0 2px;
  border-radius: 2px;
}

.warn-list {
  margin: var(--ag-space-xs) 0 0;
  padding-left: var(--ag-space-lg);
}

.summary-note {
  margin-left: var(--ag-space-sm);
  font-size: var(--ag-font-size-xs);
  font-weight: var(--ag-font-weight-normal);
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
