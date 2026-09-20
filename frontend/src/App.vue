<template>
  <div class="ag-layout">
    <aside class="ag-sidebar">
      <div class="ag-brand">
        <el-icon class="ag-brand-icon" :size="20"><Reading /></el-icon>
        <div>
          <p class="ag-brand-name">AutoGrader</p>
          <p class="ag-brand-sub">实验报告智能评阅</p>
        </div>
      </div>

      <el-menu :default-active="activePath" router class="ag-menu">
        <el-menu-item index="/upload">
          <el-icon><UploadFilled /></el-icon>
          <span>上传报告</span>
        </el-menu-item>
        <el-menu-item index="/reports">
          <el-icon><Document /></el-icon>
          <span>成绩管理</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <el-icon><Files /></el-icon>
          <span>评分模板</span>
        </el-menu-item>
      </el-menu>

      <div class="ag-sidebar-foot">
        <p class="ag-text-tertiary">粤港澳大湾区 AI Coding 创新大赛</p>
        <p class="ag-text-tertiary">赛题方向一 · AI + 教学管理助手</p>
      </div>
    </aside>

    <main class="ag-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Reading, UploadFilled, Document, Files } from '@element-plus/icons-vue'

const route = useRoute()

/* 评阅结果页属于成绩管理链路，菜单高亮跟随 */
const activePath = computed(() => (route.path.startsWith('/result') ? '/reports' : route.path))
</script>

<style scoped>
.ag-layout {
  display: flex;
  min-height: 100vh;
}

.ag-sidebar {
  width: var(--ag-sidebar-width);
  flex: 0 0 var(--ag-sidebar-width);
  display: flex;
  flex-direction: column;
  background: var(--ag-color-bg-card);
  border-right: 1px solid var(--ag-color-border);
}

.ag-brand {
  display: flex;
  align-items: center;
  gap: var(--ag-space-md);
  height: var(--ag-header-height);
  padding: 0 var(--ag-space-lg);
  border-bottom: 1px solid var(--ag-color-border);
}

.ag-brand-icon {
  color: var(--ag-color-primary);
}

.ag-brand-name {
  margin: 0;
  font-size: var(--ag-font-size-base);
  font-weight: var(--ag-font-weight-medium);
}

.ag-brand-sub {
  margin: 0;
  font-size: var(--ag-font-size-xs);
  color: var(--ag-color-text-tertiary);
}

.ag-menu {
  flex: 1;
  border-right: none;
  padding-top: var(--ag-space-sm);
}

.ag-sidebar-foot {
  padding: var(--ag-space-lg);
  border-top: 1px solid var(--ag-color-border);
}

.ag-sidebar-foot p {
  margin: 0;
}

.ag-main {
  flex: 1;
  min-width: 0;
  overflow-x: hidden;
}
</style>
