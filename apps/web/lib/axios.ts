import axios from "axios"
import { env } from "@/env"

const api = axios.create({
  baseURL: env.NEXT_PUBLIC_API_URL,
  headers: {
    "Content-Type": "application/json",
  },
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      const { status, statusText } = error.response
      return Promise.reject(new Error(`API error: ${status} ${statusText}`))
    }
    if (error.request) {
      return Promise.reject(new Error("No response received from server"))
    }
    return Promise.reject(error)
  }
)

export { api }
