<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import 'echarts-wordcloud'

const props = defineProps({ data: { type: Array, default: () => [] } })
const emit = defineEmits(['select'])
const el = ref(null)
let chart
const option = computed(() => ({
  tooltip: { formatter: p => `${p.name}: ${p.value}` },
  series: [{ type: 'wordCloud', shape: 'circle', left: 'center', top: 'center', width: '92%', height: '88%', sizeRange: [14, 54], rotationRange: [-35, 35], rotationStep: 15, gridSize: 7, drawOutOfBound: false, layoutAnimation: true, textStyle: { fontFamily: 'Inter, system-ui, sans-serif', fontWeight: 700, color: () => ['#2f6f6d', '#7b61a8', '#c47c35', '#356a9a'][Math.floor(Math.random() * 4)] }, data: props.data.map(x => ({ name: x.name, value: x.value })) }],
}))
function render() { if (!el.value) return; chart ||= echarts.init(el.value); chart.setOption(option.value, true); chart.resize() }
onMounted(() => { render(); chart?.on('click', p => emit('select', p.name)); window.addEventListener('resize', render) })
watch(() => props.data, render, { deep: true })
onBeforeUnmount(() => { window.removeEventListener('resize', render); chart?.dispose() })
</script>
<template><div ref="el" class="word-cloud-chart"></div></template>
