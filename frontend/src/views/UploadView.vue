<template>
  <div class="ag-page">
    <h1 class="ag-page-title">上传实验报告</h1>
    <p class="ag-page-desc">选择评分模板并上传报告，AI 将按评分点逐项核查并生成成绩与评语</p>

    <div class="ag-card">
      <h2 class="ag-card-title">1. 选择评分模板</h2>

      <el-empty v-if="templateError" :image-size="90" :description="templateError">
        <el-button type="primary" @click="loadTemplates">重新加载模板</el-button>
      </el-empty>

      <el-select
        v-else
        v-model="templateId"
        placeholder="请选择评分模板"
        style="width: 320px"
        :loading="templateLoading"
      >
        <el-option
          v-for="item in templates"
          :key="item.template_id"
          :label="item.name"
          :value="item.template_id"
        >
          <span>{{ item.name }}</span>
          <span class="option-count">{{ item.item_count }} 个评分点</span>
        </el-option>
      </el-select>

      <p v-if="currentTemplate" class="ag-text-secondary ag-mt-lg">
        评分点：{{ currentTemplate.items.map((i) => i.name).join(' / ') }}
      </p>
    </div>

    <div class="ag-card">
      <h2 class="ag-card-title">2. 上传报告文件</h2>
      <el-upload
        ref="uploadRef"
        drag
        class="ag-upload"
        :auto-upload="false"
        :limit="1"
        accept=".docx,.pdf"
        :on-change="handleFileChange"
        :on-exceed="handleExceed"
        :on-remove="handleRemove"
      >
        <el-icon class="ag-upload-icon" :size="40"><UploadFilled /></el-icon>
        <div class="ag-upload-text">将文件拖到此处，或点击选择文件</div>
        <template #tip>
          <div class="ag-text-tertiary">仅支持 docx / pdf 格式，单个文件不超过 20MB</div>
        </template>
      </el-upload>

      <div class="ag-row ag-mt-lg">
        <el-button
          type="primary"
          size="large"
          :loading="submitting"
          :disabled="!canSubmit"
          @click="handleSubmit"
        >
          提交评阅
        </el-button>
        <span v-if="!canSubmit && !submitting" class="ag-text-tertiary">
          请先选择模板并上传文件
        </span>
      </div>

      <div v-if="submitting" class="ag-progress">
        <el-progress :percentage="progress" :stroke-width="10" striped />
        <p class="ag-text-secondary">{{ stageText }}</p>
      </div>
    </div>

    <div class="ag-card">
      <h2 class="ag-card-title">评阅说明</h2>
      <el-steps :active="3" align-center>
        <el-step title="解析报告" description="抽取正文、代码块与结论" />
        <el-step title="逐项核查" description="按评分点判定得分与依据" />
        <el-step title="生成评语" description="输出总评、亮点与改进建议" />
      </el-steps>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { fetchTemplates, uploadReport, triggerGrading, waitForResult } from '@/api'

const router = useRouter()

const templates = ref([])
const templateId = ref(null)
const templateLoading = ref(false)
const templateError = ref('')
const uploadRef = ref(null)
const file = ref(null)
const submitting = ref(false)
const progress = ref(0)
const stageText = ref('')

const MAX_SIZE = 20 * 1024 * 1024
const ALLOW_EXT = ['docx', 'pdf']

/* 契约没有 progress 字段，进度按状态机的阶段换算（契约第 3 节） */
const STAGE_PERCENT = { uploaded: 20, parsing: 45, parsed: 65, grading: 88 }

const currentTemplate = computed(
  () => templates.value.find((item) => item.template_id === templateId.value) || null
)

const canSubmit = computed(
  () => Boolean(file.value) && Boolean(templateId.value) && !submitting.value
)

async function loadTemplates() {
  templateLoading.value = true
  templateError.value = ''
  try {
    const res = await fetchTemplates()
    templates.value = res.items ?? res.list ?? []
    if (!templates.value.length) {
      templateError.value = '后端暂无评分点模板，请先在后台导入模板'
      return
    }
    templateId.value = templates.value[0].template_id
  } catch (error) {
    templateError.value = error.message
  } finally {
    templateLoading.value = false
  }
}

onMounted(loadTemplates)

function handleFileChange(uploadFile) {
  const raw = uploadFile.raw
  const ext = raw.name.split('.').pop().toLowerCase()
  if (!ALLOW_EXT.includes(ext)) {
    ElMessage.error('仅支持 docx / pdf 格式的文件')
    uploadRef.value.clearFiles()
    file.value = null
    return
  }
  if (raw.size > MAX_SIZE) {
    ElMessage.error('文件超过 20MB，请压缩后重新上传')
    uploadRef.value.clearFiles()
    file.value = null
    return
  }
  if (raw.size === 0) {
    ElMessage.error('文件为空，请重新上传')
    uploadRef.value.clearFiles()
    file.value = null
    return
  }
  file.value = raw
}

function handleExceed() {
  ElMessage.warning('一次只能上传一份报告，请先移除已选文件')
}

function handleRemove() {
  file.value = null
}

/* 契约 7.2 → 7.3 → 7.4：上传只落库，另需触发评阅，再轮询结果 */
async function handleSubmit() {
  if (!canSubmit.value) return
  submitting.value = true
  progress.value = 8
  stageText.value = '正在上传报告…'
  let reportId = null
  try {
    const uploaded = await uploadReport({ file: file.value, templateId: templateId.value })
    reportId = uploaded.report_id

    stageText.value = '上传完成，正在启动评阅…'
    progress.value = STAGE_PERCENT.uploaded
    await triggerGrading(reportId)

    const result = await waitForResult(reportId, {
      onStage: (r) => {
        stageText.value = r.stage_text || '正在评阅…'
        progress.value = STAGE_PERCENT[r.status] ?? progress.value
      },
      interval: 2000
    })

    if (result.status === 'failed') {
      ElMessage.error(result.error_text || '评阅失败，请检查报告内容')
    } else if (result.is_partial) {
      ElMessage.warning('部分评分点未完成，已展示已出分项')
    } else {
      ElMessage.success('评阅完成')
    }
    router.push(`/result/${reportId}`)
  } catch (error) {
    if (reportId) router.push(`/result/${reportId}`)
    else ElMessage.error(error.message)
  } finally {
    submitting.value = false
    progress.value = 0
    stageText.value = ''
    uploadRef.value?.clearFiles()
    file.value = null
  }
}
</script>

<style scoped>
.option-count {
  float: right;
  margin-left: var(--ag-space-lg);
  color: var(--ag-color-text-tertiary);
  font-size: var(--ag-font-size-xs);
}

.ag-upload-icon {
  color: var(--ag-color-text-tertiary);
}

.ag-upload-text {
  margin-top: var(--ag-space-sm);
  font-size: var(--ag-font-size-sm);
  color: var(--ag-color-text-secondary);
}

.ag-progress {
  margin-top: var(--ag-space-lg);
  max-width: 520px;
}

.ag-progress p {
  margin: var(--ag-space-sm) 0 0;
}
</style>
