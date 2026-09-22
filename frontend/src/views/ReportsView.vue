<template>
  <div class="ag-page">
    <h1 class="ag-page-title">成绩管理</h1>
    <p class="ag-page-desc">查看全部评阅记录，支持按文件名与评分模板筛选</p>

    <div class="ag-card">
      <div class="filter-row">
        <el-input
          v-model="filters.keyword"
          placeholder="搜索报告文件名"
          clearable
          style="width: 260px"
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>

        <el-select
          v-model="filters.templateId"
          placeholder="全部评分模板"
          clearable
          style="width: 240px"
        >
          <el-option
            v-for="item in templates"
            :key="item.template_id"
            :label="item.name"
            :value="item.template_id"
          />
        </el-select>

        <el-button type="primary" @click="handleSearch">
          <el-icon><Search /></el-icon>
          <span>查询</span>
        </el-button>
        <el-button @click="handleReset">
          <el-icon><Refresh /></el-icon>
          <span>重置</span>
        </el-button>
      </div>

      <el-table
        v-loading="loading"
        :data="rows"
        stripe
        style="width: 100%"
        :empty-text="emptyText"
        class="ag-mt-lg"
      >
        <el-table-column prop="file_name" label="报告文件" min-width="300" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="row.status === 'success' ? 'success' : 'warning'" effect="light">
              {{ row.status === 'success' ? '已完成' : '部分完成' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="template_name" label="评分模板" min-width="200" />
        <el-table-column label="得分" width="140">
          <template #default="{ row }">
            <el-tag :type="tagType(row)" effect="light">{{ row.total_score }}</el-tag>
            <span class="ag-text-tertiary"> / {{ row.full_score }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="评阅时间" width="170" />
        <el-table-column label="操作" width="110" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="router.push(`/result/${row.report_id}`)">
              查看详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pager">
        <el-pagination
          v-model:current-page="page"
          :page-size="size"
          :total="total"
          layout="total, prev, pager, next"
          background
          @current-change="load"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Search, Refresh } from '@element-plus/icons-vue'
import { fetchReports, fetchTemplates } from '@/api'

const router = useRouter()

const loading = ref(false)
const rows = ref([])
const total = ref(0)
const page = ref(1)
const size = 5
const templates = ref([])

const filters = reactive({ keyword: '', templateId: '' })

/* 空态要区分「一条记录都没有」和「筛选无结果」 */
const hasFilter = computed(() => Boolean(filters.keyword.trim()) || Boolean(filters.templateId))
const emptyText = computed(() =>
  hasFilter.value ? '没有符合筛选条件的评阅记录，请调整条件后重试' : '暂无评阅记录，请先上传报告并发起评阅'
)

/* 色带与契约 5.3 的 level 口径一致：90 / 70 / 50 */
function tagType(row) {
  if (row.score_rate >= 90) return 'success'
  if (row.score_rate >= 70) return 'primary'
  if (row.score_rate >= 50) return 'warning'
  return 'danger'
}

async function load() {
  loading.value = true
  try {
    const res = await fetchReports({
      page: page.value,
      size,
      keyword: filters.keyword.trim(),
      templateId: filters.templateId
    })
    rows.value = res.list
    total.value = res.total
  } catch (error) {
    rows.value = []
    total.value = 0
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  page.value = 1
  load()
}

function handleReset() {
  filters.keyword = ''
  filters.templateId = ''
  page.value = 1
  load()
}

onMounted(async () => {
  try {
    const res = await fetchTemplates()
    templates.value = res.items ?? res.list ?? []
  } catch (error) {
    ElMessage.error(error.message)
  }
  load()
})
</script>

<style scoped>
.filter-row {
  display: flex;
  align-items: center;
  gap: var(--ag-space-md);
  flex-wrap: wrap;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: var(--ag-space-lg);
}
</style>
