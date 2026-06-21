<script setup>
import { formatNum, statusText, statusClass } from '../utils.js'

defineProps({
  contracts: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})
</script>

<template>
  <section class="card">
    <h3>合同列表</h3>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>借款人</th>
            <th>币种</th>
            <th>本金</th>
            <th>年利率</th>
            <th>还款日</th>
            <th>基准汇率(→CNY)</th>
            <th>预期 CNY</th>
            <th>实际 CNY</th>
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="10" class="muted">加载中...</td>
          </tr>
          <tr v-else-if="!contracts.length">
            <td colspan="10" class="muted">暂无合同，请新建一笔。</td>
          </tr>
          <tr
            v-for="c in contracts"
            :key="c.id"
            :class="{ 'row-severe-loss': c.severe_loss_flag }"
          >
            <td>{{ c.id }}</td>
            <td>{{ c.borrower_name }}</td>
            <td>{{ c.currency }}</td>
            <td>{{ formatNum(c.principal_amount) }}</td>
            <td>{{ (Number(c.interest_rate) * 100).toFixed(2) }}%</td>
            <td>{{ c.repayment_date }}</td>
            <td>{{ formatNum(c.base_rate_to_cny, 4) }}</td>
            <td>{{ c.expected_cny != null ? formatNum(c.expected_cny) : '—' }}</td>
            <td>{{ c.actual_cny != null ? formatNum(c.actual_cny) : '—' }}</td>
            <td>
              <span :class="['tag', statusClass(c.status)]">
                {{ statusText(c.status) }}
              </span>
              <span v-if="c.severe_loss_flag" class="loss-warn">
                这笔账亏损严重
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>

<style scoped>
.row-severe-loss {
  color: #cf222e;
  background: #fff5f5;
}
.row-severe-loss td {
  color: #cf222e;
  font-weight: 600;
}
.row-severe-loss:hover {
  background: #ffebeb !important;
}
.loss-warn {
  display: inline-block;
  margin-left: 8px;
  padding: 2px 8px;
  background: #cf222e;
  color: #fff;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.3px;
  animation: pulse 2s ease-in-out infinite;
}
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}
</style>
