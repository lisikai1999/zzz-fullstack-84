<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <div class="logo">字幕对齐工具</div>
      <el-menu mode="horizontal" :router="true" :default-active="route.path">
        <el-menu-item index="/">项目列表</el-menu-item>
      </el-menu>
    </el-header>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<style scoped>
.app-container {
  height: 100vh;
}
.app-header {
  display: flex;
  align-items: center;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}
.logo {
  font-size: 18px;
  font-weight: bold;
  margin-right: 40px;
  white-space: nowrap;
}
</style>
