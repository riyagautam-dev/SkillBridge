
import { useState, useEffect } from "react";
import api from "./api";
import { Plus, BookOpen, Trash2, ArrowLeft } from "lucide-react";

export default function ManageTests() {
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [selectedTest, setSelectedTest] = useState(null);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [duration, setDuration] = useState(30);

  const [questionTitle, setQuestionTitle] = useState("");
  const [questionDescription, setQuestionDescription] = useState("");
  const [questionType, setQuestionType] = useState("mcq");
  const [difficulty, setDifficulty] = useState("medium");

  const [options, setOptions] = useState(["", "", "", ""]);
  const [correctOption, setCorrectOption] = useState("1");

  const loadTests = async () => {
    try {
      const response = await api.get("/teacher/tests");
      setTests(response.data);
    } catch (error) {
      setMessage(error.response?.data?.detail || "Could not load tests");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTests();
  }, []);

  const createTest = async (e) => {
    e.preventDefault();
    try {
      await api.post("/teacher/tests", {
        title,
        description,
        duration_minutes: Number(duration)
      });

      setTitle("");
      setDescription("");
      setDuration(30);
      setMessage("Test created successfully!");
      loadTests();
    } catch (error) {
      setMessage(error.response?.data?.detail || "Test creation failed");
    }
  };

  const createQuestion = async (e) => {
    e.preventDefault();

    try {
      const response = await api.post(
        `/teacher/tests/${selectedTest.test_id}/questions`,
        {
          title: questionTitle,
          description: questionDescription,
          question_type: questionType,
          difficulty
        }
      );

      if (questionType === "mcq") {
        await api.post(
          `/teacher/questions/${response.data.question_id}/options`,
          {
            options,
            correct_option: Number(correctOption)
          }
        );
      }

      setMessage("Question added successfully!");
      setQuestionTitle("");
      setQuestionDescription("");
      setOptions(["", "", "", ""]);
      setCorrectOption("1");
    } catch (error) {
      setMessage(error.response?.data?.detail || "Question creation failed");
    }
  };

  return (
    <div className="dashboard-content">
      <h2>Manage Tests</h2>
      <p>Create tests and add questions for your students.</p>

      {message && <p>{message}</p>}

      {!selectedTest ? (
        <>
          <form onSubmit={createTest}>
            <h3><Plus size={18} /> Create New Test</h3>

            <input
              placeholder="Test title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              minLength={3}
            />

            <textarea
              placeholder="Test description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />

            <input
              type="number"
              min="1"
              max="300"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              required
            />

            <button type="submit">Create Test</button>
          </form>

          <h3>My Tests</h3>

          {loading ? (
            <p>Loading tests...</p>
          ) : tests.length === 0 ? (
            <p>No tests created yet.</p>
          ) : (
            tests.map((test) => (
              <div key={test.test_id} className="test-card">
                <BookOpen size={20} />
                <h4>{test.title}</h4>
                <p>{test.description}</p>
                <p>Status: {test.is_active ? "Active" : "Inactive"}</p>
                <p>Duration: {test.duration_minutes} minutes</p>
               <p>Total Questions: {test.total_questions}</p>
              <p>MCQ: {test.mcq_questions} | Coding: {test.coding_questions}</p>

                <button onClick={() => setSelectedTest(test)}>
                  Add Questions
                </button>
              </div>
            ))
          )}
        </>
      ) : (
        <>
          <button onClick={() => setSelectedTest(null)}>
            <ArrowLeft size={16} /> Back to Tests
          </button>

          <h3>{selectedTest.title}</h3>

          <form onSubmit={createQuestion}>
            <h3>Add Question</h3>

            <input
              placeholder="Question title"
              value={questionTitle}
              onChange={(e) => setQuestionTitle(e.target.value)}
              required
              minLength={3}
            />

            <textarea
              placeholder="Question description"
              value={questionDescription}
              onChange={(e) => setQuestionDescription(e.target.value)}
              required
            />

            <select
              value={questionType}
              onChange={(e) => setQuestionType(e.target.value)}
            >
              <option value="mcq">MCQ</option>
              <option value="coding">Coding</option>
            </select>

            <select
              value={difficulty}
              onChange={(e) => setDifficulty(e.target.value)}
            >
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>

            {questionType === "mcq" && (
              <>
                <h4>Options</h4>

                {options.map((option, index) => (
                  <input
                    key={index}
                    placeholder={`Option ${index + 1}`}
                    value={option}
                    onChange={(e) => {
                      const updated = [...options];
                      updated[index] = e.target.value;
                      setOptions(updated);
                    }}
                    required
                  />
                ))}

                <label>Correct Option</label>
                <select
                  value={correctOption}
                  onChange={(e) => setCorrectOption(e.target.value)}
                >
                  <option value="1">Option 1</option>
                  <option value="2">Option 2</option>
                  <option value="3">Option 3</option>
                  <option value="4">Option 4</option>
                </select>
              </>
            )}

            <button type="submit">Save Question</button>
          </form>
        </>
      )}
    </div>
  );
}
