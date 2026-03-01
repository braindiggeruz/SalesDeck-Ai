const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');

const app = express();

app.use('/', createProxyMiddleware({
  target: 'http://127.0.0.1:8001',
  changeOrigin: true,
  ws: true
}));

app.listen(3000, '0.0.0.0', () => {
  console.log('Frontend proxy running on port 3000');
});
