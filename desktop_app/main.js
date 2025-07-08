const backendUrl = "http://127.0.0.1:8000";
const userId = "testuser"; // TODO: Replace with dynamic user ID if available

// Fetch and display previous tests on page load
window.addEventListener("DOMContentLoaded", () => {
  // Tab switching logic
  const tabMcq = document.getElementById("tab-mcq");
  const tabHistory = document.getElementById("tab-history");
  const mcqSection = document.getElementById("mcq-section");
  const historySection = document.getElementById("previous-tests-section");

  function setActiveTab(tab) {
    document.querySelectorAll(".sidebar-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");
  }

  tabMcq.addEventListener("click", () => {
    setActiveTab(tabMcq);
    mcqSection.style.display = "";
    historySection.style.display = "none";
  });

  tabHistory.addEventListener("click", () => {
    setActiveTab(tabHistory);
    mcqSection.style.display = "none";
    historySection.style.display = "";
    fetchPreviousTests();
  });

  // Default: show MCQ section
  mcqSection.style.display = "";
  historySection.style.display = "none";
  setActiveTab(tabMcq);
});

async function fetchPreviousTests() {
  const listDiv = document.getElementById("previous-tests-list");
  listDiv.innerHTML = "Loading...";
  try {
    const res = await fetch(`${backendUrl}/user_submissions/${userId}`);
    if (!res.ok) {
      listDiv.innerHTML = "Failed to load previous tests.";
      return;
    }
    const submissions = await res.json();
    if (submissions.length === 0) {
      listDiv.innerHTML = "No previous tests found.";
      return;
    }
    // Render list
    listDiv.innerHTML = "";
    const ul = document.createElement("ul");
    submissions.forEach((sub, idx) => {
      const li = document.createElement("li");
      li.style.cursor = "pointer";
      li.textContent = `Test ${idx + 1}: ${sub.submitted_at} | Score: ${sub.correct}/${sub.total} | Subjects: ${getSubjectsString(sub.filters)}`;
      li.onclick = () => fetchTestDetails(sub.filename);
      ul.appendChild(li);
    });
    listDiv.appendChild(ul);
  } catch (err) {
    listDiv.innerHTML = "Error loading previous tests.";
  }
}

function getSubjectsString(filters) {
  if (!filters) return "";
  if (Array.isArray(filters)) {
    return filters.map(f => `${f.subject} (G${f.grade}, ${f.difficulty})`).join(", ");
  }
  // fallback for old format
  return Object.values(filters).join(", ");
}

async function fetchTestDetails(filename) {
  const detailsDiv = document.getElementById("test-details");
  detailsDiv.innerHTML = "Loading test details...";
  try {
    const res = await fetch(`${backendUrl}/submission/${filename}`);
    if (!res.ok) {
      detailsDiv.innerHTML = "Failed to load test details.";
      return;
    }
    const data = await res.json();
    renderTestDetails(data, detailsDiv);
  } catch (err) {
    detailsDiv.innerHTML = "Error loading test details.";
  }
}

function renderTestDetails(data, container) {
  let html = `<h3>Test Details</h3>`;
  html += `<b>Date:</b> ${data.submitted_at || ""}<br>`;
  html += `<b>Score:</b> ${data.correct} / ${data.total} (${((data.score || 0) * 100).toFixed(1)}%)<br>`;
  html += `<b>Subjects:</b> ${getSubjectsString(data.filters)}<br>`;
  html += `<hr>`;
  html += `<b>Questions & Answers:</b><br>`;
  // Prefer questions_with_answers if present (for MCQ review)
  if (Array.isArray(data.questions_with_answers) && data.questions_with_answers.length > 0) {
    html += "<ol>";
    data.questions_with_answers.forEach((q, idx) => {
      const userAns = q.user_answer !== undefined ? q.user_answer : "(no answer)";
      const correctAns = q.correct_answer || "";
      html += `<li><b>${q.question || "Question"}</b><br>`;
      html += `Your answer: <span style="color:${String(userAns).trim().toLowerCase() === String(correctAns).trim().toLowerCase() ? 'green' : 'red'}">${userAns}</span><br>`;
      html += `Correct answer: <b>${correctAns}</b><br>`;
      html += `<i>Subject: ${q.subject || ""}, Topic: ${q.topic || ""}, Difficulty: ${q.difficulty || ""}</i>`;
      html += `</li>`;
    });
    html += "</ol>";
  } else if (Array.isArray(data.questions)) {
    html += "<ol>";
    data.questions.forEach((q, idx) => {
      const qid = String(q.id || q.question_id || q.QID || q.qid || q.index || idx);
      const userAns = data.answers && data.answers[qid] !== undefined ? data.answers[qid] : "(no answer)";
      const correctAns = q.answer || q.Answer || q.correct_answer || "";
      html += `<li><b>${q.question || q.Question || "Question"}</b><br>`;
      html += `Your answer: <span style="color:${String(userAns).trim().toLowerCase() === String(correctAns).trim().toLowerCase() ? 'green' : 'red'}">${userAns}</span><br>`;
      html += `Correct answer: <b>${correctAns}</b><br>`;
      html += `<i>Subject: ${q.subject || ""}, Topic: ${q.topic || ""}, Difficulty: ${q.difficulty || ""}</i>`;
      html += `</li>`;
    });
    html += "</ol>";
  }
  container.innerHTML = html;

  // --- Performance Graphs ---
  const perfGraph = document.getElementById("performance-graph");
  if (!perfGraph) return;

  // Compute subject-wise and topic-wise performance
  const perf = computePerformance(data.questions, data.answers);
  // Show subject-wise bar chart
  if (perf.subjects.labels.length > 0) {
    perfGraph.style.display = "";
    renderBarChart(perfGraph, perf.subjects.labels, perf.subjects.correct, perf.subjects.incorrect, "Subject-wise Performance");
  } else {
    perfGraph.style.display = "none";
  }
}

function computePerformance(questions, answers) {
  // Returns { subjects: {labels, correct, incorrect}, topics: {labels, correct, incorrect} }
  const subjStats = {};
  const topicStats = {};
  questions.forEach((q, idx) => {
    const qid = String(q.id || q.question_id || q.QID || q.qid || q.index || idx);
    const userAns = answers && answers[qid] !== undefined ? answers[qid] : null;
    const correctAns = q.answer || q.Answer || q.correct_answer || "";
    const isCorrect = userAns !== null && String(userAns).trim().toLowerCase() === String(correctAns).trim().toLowerCase();
    // Subject
    const subj = q.subject || "Unknown";
    if (!subjStats[subj]) subjStats[subj] = { correct: 0, incorrect: 0 };
    if (isCorrect) subjStats[subj].correct += 1;
    else subjStats[subj].incorrect += 1;
    // Topic
    const topic = q.topic || "Unknown";
    if (!topicStats[topic]) topicStats[topic] = { correct: 0, incorrect: 0 };
    if (isCorrect) topicStats[topic].correct += 1;
    else topicStats[topic].incorrect += 1;
  });
  return {
    subjects: {
      labels: Object.keys(subjStats),
      correct: Object.values(subjStats).map(s => s.correct),
      incorrect: Object.values(subjStats).map(s => s.incorrect)
    },
    topics: {
      labels: Object.keys(topicStats),
      correct: Object.values(topicStats).map(s => s.correct),
      incorrect: Object.values(topicStats).map(s => s.incorrect)
    }
  };
}

let chartInstance = null;
function renderBarChart(canvas, labels, correctData, incorrectData, title) {
  if (chartInstance) {
    chartInstance.destroy();
  }
  chartInstance = new Chart(canvas, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Correct",
          data: correctData,
          backgroundColor: "rgba(75, 192, 192, 0.7)"
        },
        {
          label: "Incorrect",
          data: incorrectData,
          backgroundColor: "rgba(255, 99, 132, 0.7)"
        }
      ]
    },
    options: {
      responsive: false,
      plugins: {
        title: {
          display: true,
          text: title
        }
      },
      scales: {
        x: { stacked: true },
        y: { beginAtZero: true, stacked: true }
      }
    }
  });
}
