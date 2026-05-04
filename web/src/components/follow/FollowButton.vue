<template>
  <n-button size="small" :type="followed ? 'warning' : 'default'" @click="toggle">
    <template #icon>
      <the-icon :icon="followed ? 'material-symbols:star' : 'material-symbols:star-outline'" :size="16" />
    </template>
    {{ followed ? '已关注' : '关注' }}
  </n-button>
</template>

<script setup>
import { NButton } from 'naive-ui'
import TheIcon from '@/components/icon/TheIcon.vue'
import api from '@/api'

const props = defineProps({
  targetType: { type: String, required: true },
  targetId: { type: Number, required: true },
})

const $message = useMessage()
const followed = ref(false)

async function checkStatus() {
  try {
    const res = await api.checkFollowStatus({ target_type: props.targetType, target_id: props.targetId })
    followed.value = res.data?.followed || false
  } catch {}
}

async function toggle() {
  await api.toggleFollow({ target_type: props.targetType, target_id: props.targetId })
  followed.value = !followed.value
  $message.success(followed.value ? '已关注' : '已取消关注')
}

onMounted(() => { checkStatus() })
watch(() => props.targetId, () => { checkStatus() })
</script>
