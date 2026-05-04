<template>
  <div class="rich-editor-wrapper" :class="{ 'is-disabled': disabled }">
    <div v-if="editor && !disabled" class="editor-toolbar">
      <n-button-group size="tiny">
        <n-button
          :type="editor.isActive('bold') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleBold().run()"
        >
          <strong>B</strong>
        </n-button>
        <n-button
          :type="editor.isActive('italic') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleItalic().run()"
        >
          <em>I</em>
        </n-button>
        <n-button
          :type="editor.isActive('strike') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleStrike().run()"
        >
          <s>S</s>
        </n-button>
        <n-button
          :type="editor.isActive('code') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleCode().run()"
        >
          &lt;/&gt;
        </n-button>
      </n-button-group>
      <n-button-group size="tiny" style="margin-left: 8px">
        <n-button
          :type="editor.isActive('heading', { level: 1 }) ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleHeading({ level: 1 }).run()"
        >
          H1
        </n-button>
        <n-button
          :type="editor.isActive('heading', { level: 2 }) ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleHeading({ level: 2 }).run()"
        >
          H2
        </n-button>
        <n-button
          :type="editor.isActive('heading', { level: 3 }) ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleHeading({ level: 3 }).run()"
        >
          H3
        </n-button>
      </n-button-group>
      <n-button-group size="tiny" style="margin-left: 8px">
        <n-button
          :type="editor.isActive('bulletList') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleBulletList().run()"
        >
          列表
        </n-button>
        <n-button
          :type="editor.isActive('orderedList') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleOrderedList().run()"
        >
          有序
        </n-button>
        <n-button
          :type="editor.isActive('codeBlock') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleCodeBlock().run()"
        >
          代码块
        </n-button>
        <n-button
          :type="editor.isActive('blockquote') ? 'primary' : 'default'"
          @click="editor.chain().focus().toggleBlockquote().run()"
        >
          引用
        </n-button>
      </n-button-group>
    </div>
    <editor-content :editor="editor" class="editor-content" />
  </div>
</template>

<script setup>
import { useEditor, EditorContent } from '@tiptap/vue-3'
import StarterKit from '@tiptap/starter-kit'
import Image from '@tiptap/extension-image'
import Placeholder from '@tiptap/extension-placeholder'
import { watch } from 'vue'
import api from '@/api'

const props = defineProps({
  modelValue: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  placeholder: { type: String, default: '请输入内容...' },
  uploadCategory: { type: String, default: '' },
  projectId: { type: Number, default: null },
})

const emit = defineEmits(['update:modelValue'])

const editor = useEditor({
  content: props.modelValue,
  editable: !props.disabled,
  editorProps: {
    handlePaste(_view, event) {
      const files = Array.from(event.clipboardData?.files || []).filter((file) =>
        file.type.startsWith('image/')
      )
      if (!files.length || !props.uploadCategory) return false
      event.preventDefault()
      files.forEach((file) => uploadAndInsertImage(file))
      return true
    },
  },
  extensions: [
    StarterKit,
    Image.configure({ inline: true }),
    Placeholder.configure({ placeholder: props.placeholder }),
  ],
  onUpdate: ({ editor }) => {
    emit('update:modelValue', editor.getHTML())
  },
})

async function uploadAndInsertImage(file) {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('category', props.uploadCategory)
  if (props.projectId) formData.append('project_id', props.projectId)
  const res = await api.uploadFile(formData)
  const fileId = res.data?.id
  if (fileId) {
    editor.value
      ?.chain()
      .focus()
      .setImage({ src: `/api/v1/file/download?file_id=${fileId}` })
      .run()
  }
}

watch(
  () => props.modelValue,
  (val) => {
    if (editor.value && val !== editor.value.getHTML()) {
      editor.value.commands.setContent(val || '')
    }
  }
)

watch(
  () => props.disabled,
  (val) => {
    editor.value?.setEditable(!val)
  }
)
</script>

<style scoped>
.rich-editor-wrapper {
  border: 1px solid #eee;
  border-radius: 6px;
  background: #fff;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
  overflow: hidden;
}
.rich-editor-wrapper:focus-within {
  border-color: #e88024;
}
.editor-toolbar {
  min-height: 34px;
  padding: 5px 10px;
  border-bottom: 1px solid #eee;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 3px;
  background: #fff;
}
.editor-toolbar :deep(.n-button) {
  --n-height: 22px;
  --n-padding: 0 6px;
  --n-font-size: 12px;
}
.editor-content {
  padding: 12px 16px;
  min-height: 108px;
}
.editor-content :deep(.ProseMirror) {
  outline: none;
  min-height: 108px;
  color: #333;
  font-size: 13px;
  line-height: 1.7;
}
.editor-content :deep(.ProseMirror p.is-editor-empty:first-child::before) {
  content: attr(data-placeholder);
  color: #999;
  pointer-events: none;
  float: left;
  height: 0;
}
.is-disabled .editor-content {
  background: #f5f6fb;
}
</style>
