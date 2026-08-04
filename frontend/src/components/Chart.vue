<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

const props = defineProps({ option: { type: Object, required: true }, height: { type: String, default: '300px' } })
const el = ref(null)
let chart
function render() { if (!el.value) return; chart ||= echarts.init(el.value); chart.setOption(props.option, true); chart.resize() }
onMounted(() => { render(); window.addEventListener('resize', render) })
onBeforeUnmount(() => { window.removeEventListener('resize', render); chart?.dispose() })
</script>
<template><div ref="el" :style="{ height, width: '100%' }"></div></template>
