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

      <div v-if="submitting || failure" class="ag-progress">
        <el-progress
          :percentage="progress"
          :stroke-width="10"
          :status="failure ? 'exception' : undefined"
          :striped="!failure"
          :show-text="!failure"
        />
        <p class="ag-text-secondary">{{ failure ? '评阅未完成' : stageText }}</p>
      </div>

      <!-- 失败常驻提示：归类 + 错误码 + 可执行的下一步（契约要求，不用 ElMessage 一闪而过） -->
      <el-alert v-if="failure" type="error" :closable="false" show-icon class="ag-mt-lg">
        <template #title>
          {{ failure.kind_text }}<template v-if="failure.code">（错误码 {{ failure.code }}）</template>
        </template>
        <span class="failure-msg">{{ failure.message }}</span>
        <el-button size="small" type="primary" plain class="ag-mt-sm" @click="resetFailure">
          重新上传
        </el-button>
      </el-alert>
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
/* 常驻失败态：{ code, kind, kind_text, message }
   用 el-alert 常驻展示，而不是 ElMessage 一闪而过 —— 契约要求失败时给出
   「错误码 + 下一步动作」，闪一下用户来不及看清也没法照着做。 */
const failure = ref(null)

const MAX_SIZE = 20 * 1024 * 1024
const ALLOW_EXT = ['docx', 'pdf']

/* 契约没有 progress 字段，进度按状态机的阶段换算。
   口径直接取契约第 4 节的建议值：uploaded 10 / parsing 30 / parsed 50 / grading 80，
   终态 100，失败转错误态（原先代码里的 30/50/65/85 契约里没有，已按契约统一）。 */
const STAGE_PERCENT = { uploaded: 10, parsing: 30, parsed: 50, grading: 80 }

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

/* 「重新上传」：清掉常驻错误与进度，回到可选文件的状态 */
function resetFailure() {
  failure.value = null
  progress.value = 0
  stageText.value = ''
  uploadRef.value?.clearFiles()
  file.value = null
}

/* 契约 7.2 → 7.3 → 7.4：上传只落库，另需触发评阅，再轮询结果
   失败分三类处理（卡片1）：
     · 文件/参数问题（4001/4002/4004/4041/4091）+ 网络问题（3001/3002）
       → 发生在上传或触发阶段，留在本页常驻展示，给「重新上传」
     · 服务端问题（4003/4005/5001–5005）→ 契约规定为 HTTP 200 + 任务置 failed，
       只在轮询到 status==='failed' 时才读得到，交结果页常驻展示 */
async function handleSubmit() {
  if (!canSubmit.value) return
  failure.value = null
  submitting.value = true
  progress.value = 8
  stageText.value = '正在上传报告…'
  let reportId = null
  try {
    const uploaded = await uploadReport({ file: file.value, templateId: templateId.value })
    reportId = uploaded.report_id

    if (uploaded.reused) ElMessage.info('该报告已存在，正在打开已有评阅结果')
    stageText.value = uploaded.reused ? '该报告已存在，正在打开已有评阅结果…' : '上传完成，正在启动评阅…'
    progress.value = STAGE_PERCENT.uploaded
    await triggerGrading(reportId)

    const result = await waitForResult(reportId, {
      onStage: (r) => {
        stageText.value = r.stage_text || '正在评阅…'
        /* 终态（success / partial_success / failed）统一推到 100%，
           否则进度条会停在 grading 的 80% 上不动 */
        progress.value = r.in_flight ? (STAGE_PERCENT[r.status] ?? progress.value) : 100
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
    /* 已经拿到 report_id 时（上传成功、后续触发/轮询失败）不能静默跳转 ——
       那会让用户以为一切正常。先把原因说出来，再打开该报告的结果页。 */
    if (reportId) {
      ElMessage.warning(`${error.message}（已为你打开该报告的结果页）`)
      router.push(`/result/${reportId}`)
      return
    }
    /* 上传/触发阶段的同步错误：留在本页常驻展示错误码与归类，进度条转错误态 */
    failure.value = {
      code: error.code ?? null,
      kind: error.kind ?? 'server',
      kind_text: error.kind_text ?? '请求失败',
      message: error.message
    }
    progress.value = 100
  } finally {
    submitting.value = false
    /* 失败时保留进度条（错误态）与所选文件，用户可以直接点「重新上传」重试 */
    if (!failure.value) {
      progress.value = 0
      stageText.value = ''
      uploadRef.value?.clearFiles()
      file.value = null
    }
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

.failure-msg {
  display: block;
  margin: 0 0 var(--ag-space-sm);
}
</style>
