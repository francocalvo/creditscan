import { describe, it, expect } from 'vitest'

describe('Example tests', () => {
  it('should add two numbers correctly', () => {
    expect(2 + 2).toBe(4)
  })

  it('should check if array contains element', () => {
    const arr = [1, 2, 3, 4, 5]
    expect(arr).toContain(3)
  })

  it('should check string equality', () => {
    const greeting = 'Hello World'
    expect(greeting).toBe('Hello World')
  })
})
