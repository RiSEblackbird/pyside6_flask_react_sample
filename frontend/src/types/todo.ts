export interface Todo {
    id: number;
    title: string;
    completed: boolean;
    created_at: string;
}

export interface ApiResponse {
    id?: number;
    success: boolean;
}