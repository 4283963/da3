<script setup>
import { onMounted, ref } from 'vue'
import { api } from './api.js'
import { formatNum, gainClass } from './utils.js'
import ContractList from './components/ContractList.vue'

const contracts = ref([])
const summary = ref(null)
const loading = ref(false)
const error = ref('')
const message = ref('')

const form = ref({
  borrower_name: '',
  currency: 'USD',
  principal_amount: '',
  interest_rate: '',
  repayment_date: '',
})

async function refresh() {
  loading.value = true
  error.value = ''
  try {
    const [cs, sm] = await Promise.all([api.listContracts(), api.summary()])
    contracts.value = cs
    summary.value = sm
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

async function submit() {
  error.value = ''
  message.value = ''
  try {
    await api.createContract({
      borrower_name: form.value.borrower_name.trim(),
      currency: form.value.currency,
      principal_amount: Number(form.value.principal_amount),
      interest_rate: Number(form.value.interest_rate),
      repayment_date: form.value.repayment_date,
    })
    form.value = {
      borrower_name: '',
      currency: 'USD',
      principal_amount: '',
      interest_rate: '',
      repayment_date: '',
    }
    message.value = '合同创建成功'
    await refresh()
  } catch (e) {
    error.value = e.message
  }
}

async function autoRun() {
  error.value = ''
  message.value = ''
  try {
    const res = await api.autoRun()
    message.value = `已处理 ${res.processed} 笔到期合同的自动扣款`
    await refresh()
  } catch (e) {
    error.value = e.message
  }
}

onMounted(refresh)
</script>

<template>
  <div class="container">
    <header>
      <h1>跨国贷款合同划扣管理系统</h1>
      <div class="actions">
        <button @click="refresh" :disabled="loading">刷新</button>
        <button class="primary" @click="autoRun" :disabled="loading">
          执行到期自动扣款
        </button>
      </div>
    </header>

    <p v-if="error" class="error">⚠ {{ error }}</p>
    <p v-if="message" class="message">✓ {{ message }}</p>

    <section class="grid">
      <div class="card summary" v-if="summary">
        <h3>汇率冲抵总览</h3>
        <p class="total">
          累计盈亏 (CNY)：
          <strong :class="gainClass(summary.total_gain_loss_cny)">
            {{ formatNum(summary.total_gain_loss_cny) }}
          </strong>
        </p>
        <ul>
          <li v-for="c in summary.by_currency" :key="c.currency">
            <span class="badge">{{ c.currency }}</span>
            {{ c.contract_count }} 笔合同，冲抵盈亏
            <strong :class="gainClass(c.total_gain_loss_cny)">
              {{ formatNum(c.total_gain_loss_cny) }}
            </strong>
            CNY（本金合计 {{ formatNum(c.total_original_amount) }}）
          </li>
          <li v-if="!summary.by_currency.length" class="muted">暂无冲抵记录</li>
        </ul>
      </div>

      <div class="card form-card">
        <h3>新建贷款合同</h3>
        <form @submit.prevent="submit">
          <label>
            借款人
            <input v-model="form.borrower_name" required placeholder="如：Somchai" />
          </label>
          <label>
            币种
            <select v-model="form.currency">
              <option value="USD">USD 美元</option>
              <option value="THB">THB 泰铢</option>
            </select>
          </label>
          <label>
            本金
            <input v-model="form.principal_amount" type="number" step="0.01" required />
          </label>
          <label>
            年利率（0.085 表示 8.5%）
            <input v-model="form.interest_rate" type="number" step="0.0001" required />
          </label>
          <label>
            还款日
            <input v-model="form.repayment_date" type="date" required />
          </label>
          <button type="submit">创建合同</button>
        </form>
      </div>
    </section>

    <ContractList :contracts="contracts" :loading="loading" />
  </div>
</template>

<style scoped>
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
h1 {
  font-size: 22px;
  margin: 0;
}
.actions {
  display: flex;
  gap: 8px;
}
.grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.summary .total {
  font-size: 16px;
}
.summary ul {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
}
.summary li {
  padding: 6px 0;
  border-bottom: 1px dashed var(--border);
}
.badge {
  display: inline-block;
  background: #eef;
  color: #335;
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 12px;
  margin-right: 6px;
}
.form-card form {
  display: grid;
  gap: 10px;
}
.form-card label {
  display: grid;
  gap: 4px;
  font-size: 13px;
  color: #555;
}
.gain {
  color: #1a7f37;
}
.loss {
  color: #cf222e;
}
@media (max-width: 768px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
