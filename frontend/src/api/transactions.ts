import type { CancelablePromise } from './core/CancelablePromise'
import { OpenAPI } from './core/OpenAPI'
import { request as __request } from './core/request'

export type Transaction = {
    id: string
    amount: number
    currency: string
    description: string
    txn_date: string
    category?: string
    status?: string
    statement_id: string
    user_id: string
    created_at: string
    updated_at: string
    payee?: string | null
}

export type TransactionsPublic = {
    data: Transaction[]
    count: number
}

export class TransactionsService {
    /**
     * List Transactions
     * Retrieve transactions.
     * @param skip Number of records to skip
     * @param limit Number of records to return
     * @returns TransactionsPublic Successful Response
     * @throws ApiError
     */
    public static listTransactions(
        skip: number = 0,
        limit: number = 100,
    ): CancelablePromise<TransactionsPublic> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/api/v1/transactions/',
            query: {
                skip,
                limit,
            },
            errors: {
                422: 'Validation Error',
            },
        })
    }
}
