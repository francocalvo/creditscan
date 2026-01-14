import { defineStore } from 'pinia'
import { ref } from 'vue'

export type ConditionField = 'payee' | 'narration' | 'amount'
export type ConditionOperator = 'contains' | 'equals' | 'starts_with' | 'greater_than'

export interface Rule {
    id: string
    name: string
    field: ConditionField
    operator: ConditionOperator
    value: string
    assignTagId: string
    isActive: boolean
}

export const useRulesStore = defineStore('rules', () => {
    const defaultRules: Rule[] = [
        {
            id: '1',
            name: 'Starbucks Coffee',
            field: 'narration',
            operator: 'contains',
            value: 'Starbucks',
            assignTagId: '1', // Coffee
            isActive: true
        }
    ]

    const savedRules = localStorage.getItem('creditscan_rules')
    const rules = ref<Rule[]>(savedRules ? JSON.parse(savedRules) : defaultRules)

    const saveToStorage = () => {
        localStorage.setItem('creditscan_rules', JSON.stringify(rules.value))
    }

    const addRule = (rule: Omit<Rule, 'id'>) => {
        rules.value.push({
            id: crypto.randomUUID(),
            ...rule
        })
        saveToStorage()
    }

    const updateRule = (id: string, updates: Partial<Rule>) => {
        const index = rules.value.findIndex(r => r.id === id)
        if (index !== -1) {
            rules.value[index] = { ...rules.value[index], ...updates }
            saveToStorage()
        }
    }

    const deleteRule = (id: string) => {
        rules.value = rules.value.filter(r => r.id !== id)
        saveToStorage()
    }

    return {
        rules,
        addRule,
        updateRule,
        deleteRule
    }
})
