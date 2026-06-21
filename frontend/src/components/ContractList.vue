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
            <th>状态</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="muted">加载中...</td>
          </tr>
          <tr v-else-if="!contracts.length">
            <td colspan="8" class="muted">暂无合同，请新建一笔。</td>
          </tr>
          <tr v-for="c in contracts" :key="c.id">
            <td>{{ c.id }}</td>
            <td>{{ c.borrower_name }}</td>
            <td>{{ c.currency }}</td>
            <td>{{ formatNum(c.principal_amount) }}</td>
            <td>{{ (Number(c.interest_rate) * 100).toFixed(2) }}%</td>
            <td>{{ c.repayment_date }}</td>
            <td>{{ formatNum(c.base_rate_to_cny, 4) }}</td>
            <td>
              <span :class="['tag', statusClass(c.status)]">
                {{ statusText(c.status) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </section>
</template>
