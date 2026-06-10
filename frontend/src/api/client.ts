import axios from 'axios'

const client = axios.create({
  baseURL: '/',
  timeout: 60000,
})

export default client
