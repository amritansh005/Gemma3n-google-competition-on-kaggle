// server.js

const express = require('express');
const { spawn } = require('child_process');
const app = express();
const axios = require('axios');
const port = 3000;

app.use(express.json());

app.post('/generate_exam', async (req, res) => {
  try {
    const response = await axios.post('http://127.0.0.1:8000/generate_exam', req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).send(error.message);
  }
});

app.post('/generate_mcqs', async (req, res) => {
  try {
    const response = await axios.post('http://127.0.0.1:8000/generate_mcqs', req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).send(error.message);
  }
});

app.post('/submit_answers', async (req, res) => {
  try {
    const response = await axios.post('http://127.0.0.1:8000/submit_answers', req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).send(error.message);
  }
});

app.post('/feedback', async (req, res) => {
  try {
    const response = await axios.post('http://127.0.0.1:8000/feedback', req.body);
    res.json(response.data);
  } catch (error) {
    res.status(error.response?.status || 500).send(error.message);
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});
