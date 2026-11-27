import { useState, useEffect } from 'react'
import Auth from './Auth'
import api from './api'
import ManageTests from './ManageTests'
import {
  LayoutDashboard, Users, BookOpen, ClipboardList,
  ChartNoAxesCombined, Settings, Bell, Search, Menu, X,
  Plus, ArrowUpRight, Clock, CheckCircle2,
  GraduationCap, LogOut, UserRound, BrainCircuit, Trophy,
  ChevronDown
} from 'lucide-react'
import './App.css'






// Temporary teacher test data
const tests = [
  { name: 'Python Skill Assessment', type: 'MCQ + Coding', questions: 21, duration: '45 min', status: 'Available' },
  { name: 'Data Structures & Algorithms', type: 'Coding', questions: 10, duration: '60 min', status: 'Available' },
  { name: 'Database Management', type: 'MCQ', questions: 20, duration: '30 min', status: 'Completed' },
]

// Temporary teacher activities
const activities = [
  { title: 'Python Skill Assessment', detail: 'Test completed', time: 'Today', score: '85%' },
  { title: 'Database Management', detail: 'Test completed', time: 'Yesterday', score: '72%' },
  { title: 'Programming Basics', detail: 'Test completed', time: 'Recently', score: '90%' },
]


function App() {
  const [teacherTests, setTeacherTests] = useState([])
  const [teacherTestsLoading, setTeacherTestsLoading] = useState(false)
  const [teacherTestsError, setTeacherTestsError] = useState('')

  // Teacher dashboard statistics
  const [teacherDashboardStats, setTeacherDashboardStats] = useState({
    total_students: 0,
    active_tests: 0,
    total_questions: 0,
    average_score: 0,
  })
  const [teacherPerformance, setTeacherPerformance] = useState([])
  // Teacher dashboard cards
  const teacherStats = [
    {
      title: 'Total Students',
      value: String(teacherDashboardStats.total_students),
      note: 'Across all batches',
      icon: Users,
    },
    {
      title: 'Active Tests',
      value: String(teacherDashboardStats.active_tests).padStart(2, '0'),
      note: 'Currently available',
      icon: ClipboardList,
    },
    {
      title: 'Questions',
      value: String(teacherDashboardStats.total_questions),
      note: 'MCQ + Coding',
      icon: BookOpen,
    },
    {
      title: 'Average Score',
      value: `${teacherDashboardStats.average_score}%`,
      note: 'Across all tests',
      icon: Trophy,
    },
  ]

  const savedUser = JSON.parse(localStorage.getItem('user') || 'null')

  const [role, setRole] = useState(savedUser?.role || 'student')
  const [page, setPage] = useState('Dashboard')
  const [mobileOpen, setMobileOpen] = useState(false)

  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(localStorage.getItem('access_token'))
  )

  const [availableTests, setAvailableTests] = useState([])
  const [testsLoading, setTestsLoading] = useState(false)
  const [testsError, setTestsError] = useState('')

  // Student results API state
  const [studentResults, setStudentResults] = useState({
    total_tests: 0,
    results: [],
  })

  // Active test states
  const [activeAttempt, setActiveAttempt] = useState(null)
  const [resumableAttempt, setResumableAttempt] = useState(null)
  const [activeTest, setActiveTest] = useState(null)
  const [testQuestions, setTestQuestions] = useState([])
  const [startingTestId, setStartingTestId] = useState(null)
  const [testError, setTestError] = useState('')
  const [selectedAnswers, setSelectedAnswers] = useState({})
  const [answerMessage, setAnswerMessage] = useState('')
  // Start test and fetch questions
   const handleStartTest = async (test) => {
  if (startingTestId) return
    setStartingTestId(test.id)
    setTestError('')

    try {
      let attempt = activeAttempt

      // Existing attempt ko dobara create nahi karenge
      if (!attempt || attempt.test_id !== test.id) {
        const startResponse = await api.post(
          `/student/tests/${test.id}/start`
        )

        attempt = startResponse.data
        setActiveAttempt(attempt)
      }

      // Attempt ID ke saath questions fetch karna
      const questionsResponse = await api.get(
        `/student/tests/${test.id}/questions`,
        {
          params: {
            attempt_id: attempt.attempt_id,
          },
        }
      )

      setActiveTest(questionsResponse.data)
      setTestQuestions(questionsResponse.data.questions || [])
      setPage('Take Test')

    } catch (error) {
      setTestError(
        error.response?.data?.detail ||
        'Unable to start the test.'
      )
    } finally {
      setStartingTestId(null)
    }
  }

    const handleResumeTest = async () => {
  if (!resumableAttempt || startingTestId) return

  setStartingTestId(resumableAttempt.test_id)
  setTestError('')

  try {
    const questionsResponse = await api.get(
      `/student/tests/${resumableAttempt.test_id}/questions`,
      {
        params: {
          attempt_id: resumableAttempt.attempt_id,
        },
      }
    )

    setActiveAttempt({
      attempt_id: resumableAttempt.attempt_id,
      test_id: resumableAttempt.test_id,
    })

    setActiveTest(questionsResponse.data)
    setTestQuestions(questionsResponse.data.questions || [])
    setPage('Take Test')
  } catch (error) {
    setTestError(
      error.response?.data?.detail ||
      'Unable to resume the test.'
    )
  } finally {
    setStartingTestId(null)
  }
}
  
    const handleSubmitAnswer = async (questionId) => {
    try {
      const selectedOptionId = selectedAnswers[questionId]

      if (!selectedOptionId) {
        setAnswerMessage('Please select an option first.')
        return
      }

      const response = await api.post(
        `/student/attempts/${activeAttempt.attempt_id}/answer`,
        { selected_option_id: selectedOptionId },
        { params: { question_id: questionId } }
      )

      setAnswerMessage(
        response.data.message || 'Answer submitted successfully!'
      )
    } catch (error) {
      setAnswerMessage(
        error.response?.data?.detail || 'Failed to submit answer.'
      )
    }
  }
  // Student recent activities
  const studentActivities = studentResults.results.map((result) => ({
    title: result.test_title,
    detail: 'Test completed',
    time: result.submitted_at
      ? new Date(result.submitted_at).toLocaleString('en-IN')
      : 'Date unavailable',
    score: `${Math.round(result.percentage || 0)}%`,
  }))

  // Average score calculation
  const averageScore = studentResults.results.length > 0
    ? studentResults.results.reduce(
        (total, result) => total + (result.percentage || 0),
        0
      ) / studentResults.results.length
    : 0

  // Student dashboard stats
  const studentStats = [
    {
      title: 'Tests Completed',
      value: String(studentResults.total_tests),
      note: 'Completed tests',
      icon: ClipboardList,
    },
    {
      title: 'Average Score',
      value: `${Math.round(averageScore)}%`,
      note: 'Across completed tests',
      icon: ChartNoAxesCombined,
    },
    {
      title: 'Skills Improved',
      value: '—',
      note: 'Skill tracking coming soon',
      icon: BrainCircuit,
    },
    {
      title: 'Learning Hours',
      value: '—',
      note: 'Time tracking coming soon',
      icon: Clock,
    },
  ]

  // Fetch student dashboard data
  useEffect(() => {
    if (!isAuthenticated || role !== 'student') return

    let isMounted = true

    const fetchAvailableTests = async () => {
      try {
        setTestsLoading(true)
        setTestsError('')

        const response = await api.get('/student/tests')

        if (isMounted) {
          setAvailableTests(response.data)
        }
      } catch (error) {
        if (isMounted) {
          setTestsError(
            error.response?.data?.detail ||
            'Unable to load available tests.'
          )
        }
      } finally {
        if (isMounted) {
          setTestsLoading(false)
        }
      }
    }

    const fetchStudentResults = async () => {
      try {
        const response = await api.get('/student/results')

        if (isMounted) {
          setStudentResults(response.data)
        }
      } catch (error) {
        console.error(
          'Unable to load student results:',
          error.response?.data || error.message
        )
      }
    }
    const fetchActiveAttempt = async () => {
  try {
    const response = await api.get('/student/attempts/active')

    if (isMounted) {
      setResumableAttempt(response.data.attempt || null)
      console.log('ACTIVE ATTEMPT:', response.data)
    }
  } catch (error) {
    console.error(
      'Unable to load active attempt:',
      error.response?.data || error.message
    )
  }
}

    fetchAvailableTests()
    fetchStudentResults()
    fetchActiveAttempt()

    return () => {
      isMounted = false
    }
  }, [isAuthenticated, role])
 
// Fetch teacher dashboard tests
useEffect(() => {
  if (!isAuthenticated || role !== 'teacher') return

  let isMounted = true

  const fetchTeacherTests = async () => {
    try {
      setTeacherTestsLoading(true)
      setTeacherTestsError('')

      const response = await api.get('/teacher/tests')
      const statsResponse = await api.get('/teacher/dashboard')

      if (isMounted) {
        // Teacher tests
        setTeacherTests(response.data)

        // Teacher dashboard statistics
        const stats = statsResponse.data.statistics
        const performance = statsResponse.data.performance

        setTeacherDashboardStats({
          total_students: stats.total_students,
          active_tests: stats.active_tests,
          total_questions: stats.total_questions_created,
          average_score: Math.round(performance.average_percentage),
        })

        // Test-wise performance
        setTeacherPerformance(
          statsResponse.data.test_performance || []
        )

        console.log('TEACHER TESTS:', response.data)
        console.log('FIRST TEST:', response.data[0])
      }
    } catch (error) {
      if (isMounted) {
        setTeacherTestsError(
          error.response?.data?.detail ||
          'Unable to load teacher tests.'
        )
      }
    } finally {
      if (isMounted) {
        setTeacherTestsLoading(false)
      }
    }
  }

  fetchTeacherTests()

  return () => {
    isMounted = false
  }
}, [isAuthenticated, role])

const isTeacher = role === 'teacher'

console.log('CURRENT ROLE:', role)
console.log('IS TEACHER:', isTeacher)

const stats = isTeacher ? teacherStats : studentStats


  const dashboardTests = isTeacher
  ? teacherTests.map((test) => ({
      id: test.test_id,
      name: test.title,
      type: `${test.mcq_questions} MCQ + ${test.coding_questions} Coding`,
      questions: test.total_questions,
      duration: `${test.duration_minutes} min`,
      status: test.is_active ? 'Available' : 'Inactive',
    }))
  : availableTests.map((test) => ({
      id: test.test_id,
      name: test.title,
      type: '—',
      questions: '—',
      duration: `${test.duration_minutes} min`,
      status: 'Available',
    }))
      console.log('DEBUG:', JSON.stringify({
  role,
  availableTests,
  dashboardTests
}, null, 2))

  const studentMenu = [
    { name: 'Dashboard', icon: LayoutDashboard },
    { name: 'My Tests', icon: ClipboardList },
    { name: 'My Results', icon: ChartNoAxesCombined },
    { name: 'My Skills', icon: BrainCircuit },
    { name: 'Profile', icon: UserRound },
  ]

  const teacherMenu = [
    { name: 'Dashboard', icon: LayoutDashboard },
    { name: 'Students', icon: Users },
    { name: 'Manage Tests', icon: ClipboardList },
    { name: 'Question Bank', icon: BookOpen },
    { name: 'AI Questions', icon: BrainCircuit },
    { name: 'Results & Analytics', icon: ChartNoAxesCombined },
    { name: 'Profile', icon: UserRound },
  ]

  const menu = isTeacher ? teacherMenu : studentMenu

  function changeRole(nextRole) {
    setRole(nextRole)
    setPage('Dashboard')
    setMobileOpen(false)
  }

  function handleLogout() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('user')

    setIsAuthenticated(false)
    setRole('student')
    setPage('Dashboard')
  }

  if (!isAuthenticated) {
    return (
      <Auth
        onLogin={(selectedRole) => {
          setRole(selectedRole)
          setPage('Dashboard')
          setIsAuthenticated(true)
        }}
      />
    )
  }

  return (
    <div className="app-shell">

      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>

        <div className="brand">
          <div className="brand-icon">
            <GraduationCap size={25} />
          </div>

          <div>
            <h2>SkillBridge</h2>
            <span>CAREER DEVELOPMENT</span>
          </div>

          <button
            className="mobile-close"
            onClick={() => setMobileOpen(false)}
          >
            <X />
          </button>
        </div>

        <div className="workspace-label">WORKSPACE</div>

        <div className="role-switch">
          <button
            className={role === 'student' ? 'active' : ''}
            onClick={() => changeRole('student')}
          >
            Student
          </button>

          <button
            className={role === 'teacher' ? 'active' : ''}
            onClick={() => changeRole('teacher')}
          >
            Teacher
          </button>
        </div>

        <div className="menu-label">MENU</div>

        <nav className="nav-menu">
          {menu.map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={`nav-link ${page === name ? 'selected' : ''}`}
              onClick={() => {
                setPage(name)
                setMobileOpen(false)
              }}
            >
              <Icon size={19} />
              <span>{name}</span>
              {name === 'AI Questions' && (
                <span className="new-tag">AI</span>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">

          <button
            className="nav-link"
            onClick={() => setPage('Settings')}
          >
            <Settings size={19} />
            <span>Settings</span>
          </button>

          <div className="sidebar-profile">
            <div className="avatar">{isTeacher ? 'T' : 'S'}</div>

            <div className="profile-info">
              <strong>
                {isTeacher ? 'Teacher Account' : 'Student Account'}
              </strong>
              <span>{isTeacher ? 'Educator' : 'Learner'}</span>
            </div>

            <button
              className="logout-icon"
              title="Logout"
              onClick={handleLogout}
            >
              <LogOut size={17} />
            </button>
          </div>

        </div>
      </aside>

      {mobileOpen && (
        <div
          className="mobile-overlay"
          onClick={() => setMobileOpen(false)}
        />
      )}

      <main className="main-area">

        <header className="topbar">

          <button
            className="mobile-menu"
            onClick={() => setMobileOpen(true)}
          >
            <Menu />
          </button>

          <div className="breadcrumb">
            Workspace <span>/</span> <strong>{page}</strong>
          </div>

          <div className="topbar-actions">

            <div className="search-box">
              <Search size={17} />
              <input placeholder="Search anything..." />
            </div>

            <button className="notification-button">
              <Bell size={19} />
              <i />
            </button>

            <div className="top-avatar">{isTeacher ? 'T' : 'S'}</div>

          </div>
        </header>

        <div className="page-content">

          <section className="welcome-row">

            <div>
              <div className="eyebrow">YOUR LEARNING JOURNEY</div>

              <h1>
                {page === 'Dashboard'
                  ? (isTeacher ? 'Teacher Dashboard' : 'Welcome back!')
                  : page}
              </h1>

              <p>
                {page === 'Dashboard'
                  ? (isTeacher
                    ? 'Manage your students and track their progress.'
                    : 'Keep learning, keep growing. Your career journey continues here.')
                  : `Explore and manage your ${page.toLowerCase()} on SkillBridge.`}
              </p>
            </div>

            {isTeacher && (
              <button
                className="primary-button"
                onClick={() => setPage('Manage Tests')}
              >
                <Plus size={18} /> Create New Test
              </button>
            )}

          </section>

          {page === 'Dashboard' ? (
            <>

              <section className="stats-grid">

                {stats.map(({ title, value, note, icon: Icon }) => (
                  <div className="stat-card" key={title}>

                    <div className="stat-top">
                      <span>{title}</span>
                      <div className="stat-icon">
                        <Icon size={20} />
                      </div>
                    </div>

                    <div className="stat-value">{value}</div>
                    <div className="stat-note">{note}</div>

                  </div>
                ))}

              </section>

              
<section className="dashboard-grid">

  <div className="panel performance-panel">

    <div className="panel-heading">
      <div>
        <h3>
          {isTeacher ? 'Performance Overview' : 'Your Performance'}
        </h3>
        <p>
          {isTeacher
            ? 'Overall student performance'
            : 'Your progress over time'}
        </p>
      </div>

      <button className="period-button">
        This week <ChevronDown size={15} />
      </button>
    </div>

    <div className="chart-area">

      <div className="chart-y-labels">
        <span>100%</span>
        <span>75%</span>
        <span>50%</span>
        <span>25%</span>
        <span>0%</span>
      </div>

      <div className="chart">

        <div className="chart-gridlines">
          <i /><i /><i /><i /><i />
        </div>

        <div className="chart-bars">
          {isTeacher && teacherPerformance.length > 0 ? (
            teacherPerformance.map((test) => (
              <div className="bar-column" key={test.test_id}>
                <div
                  className="bar"
                  style={{
                    height: `${Math.min(test.average_percentage || 0, 100)}%`,
                  }}
                />
                <span>
                  {test.title.length > 10
                    ? `${test.title.slice(0, 10)}...`
                    : test.title}
                </span>
              </div>
            ))
          ) : (
            <p>No completed test performance available.</p>
          )}
        </div>

      </div>
    </div>

  </div>

  <div className="panel skills-panel">

    <div className="panel-heading">
      <div>
        <h3>{isTeacher ? 'Top Skills' : 'Skill Progress'}</h3>
        <p>
          {isTeacher
            ? 'Popular student skills'
            : 'Your current skill levels'}
        </p>
      </div>
    </div>

    {[
      ['Python Programming', 85],
      ['Problem Solving', 72],
      ['Data Structures', 64],
      ['Database Management', 78],
    ].map(([name, value]) => (
      <div className="skill-item" key={name}>

        <div className="skill-meta">
          <span>{name}</span>
          <strong>{value}%</strong>
        </div>

        <div className="progress-track">
          <div style={{ width: `${value}%` }} />
        </div>

      </div>
    ))}

  </div>

</section>

              <section className="panel tests-panel">
                {!isTeacher && resumableAttempt && (
  <div className="resume-test-card">
    <div>
      <h3>Continue Your Test</h3>
      <p>{resumableAttempt.test_title}</p>
    </div>

    <button
      className="primary-button"
      onClick={handleResumeTest}
      disabled={startingTestId !== null}
    >
      {startingTestId === resumableAttempt.test_id
        ? 'Resuming...'
        : 'Resume Test'}
    </button>
  </div>
)}

                <div className="panel-heading">

                  <div>
                    <h3>{isTeacher ? 'Recent Tests' : 'Available Tests'}</h3>
                    <p>
                      {isTeacher
                        ? 'Recently created assessments'
                        : 'Continue improving your skills'}
                    </p>
                  </div>

                  <button
                    className="text-button"
                    onClick={() => setPage(isTeacher ? 'Manage Tests' : 'My Tests')}
                  >
                    View all <ArrowUpRight size={16} />
                  </button>

                </div>

                <div className="table-wrap">

                  <table>

                    <thead>
                      <tr>
                        <th>TEST NAME</th>
                        <th>TYPE</th>
                        <th>QUESTIONS</th>
                        <th>DURATION</th>
                        <th>STATUS</th>
                        <th />
                      </tr>
                    </thead>

                    
<tbody>
  {(isTeacher ? teacherTestsLoading : testsLoading) ? (
    <tr>
      <td colSpan="6">Loading tests...</td>
    </tr>
  ) : (isTeacher ? teacherTestsError : testsError) ? (
    <tr>
      <td colSpan="6">
        {isTeacher ? teacherTestsError : testsError}
      </td>
    </tr>
  ) : dashboardTests.length === 0 ? (
    <tr>
      <td colSpan="6">No available tests found.</td>
    </tr>
  ) : (
    dashboardTests.map((test) => (
      <tr key={test.id}>
        <td><strong>{test.name}</strong></td>
        <td>{test.type}</td>
        <td>{test.questions}</td>
        <td>{test.duration}</td>
        <td>
          <span className={`status ${test.status.toLowerCase()}`}>
            {test.status}
          </span>
        </td>
        <td>
          <button
            className="row-action"
            onClick={() => {
              if (isTeacher) {
                setPage('Manage Tests')
              } else {
                handleStartTest(test)
              }
            }}
            disabled={!isTeacher && startingTestId === test.id}
          >
            {!isTeacher && startingTestId === test.id ? '...' : '→'}
          </button>
        </td>
      </tr>
    ))
  )}
</tbody>

                  </table>

                </div>

                {testError && (
                  <p className="error-message">{testError}</p>
                )}

              </section>

              
<section className="panel activity-panel">

  <div className="panel-heading">
    <div>
      <h3>{isTeacher ? 'Recent Activity' : 'Recent Attempts'}</h3>
      <p>
        {isTeacher
          ? 'Latest student activity'
          : 'Your latest assessment history'}
      </p>
    </div>
  </div>

  {!isTeacher && studentResults.results.length === 0 && (
    <p>No completed tests yet.</p>
  )}

  {(isTeacher ? activities : studentResults.results).map((item, index) => (
    <div
      className="activity-row"
      key={isTeacher ? `${item.title}-${index}` : item.attempt_id}
    >
      <div className="activity-icon">
        <CheckCircle2 size={19} />
      </div>

      <div className="activity-description">
        <strong>{isTeacher ? item.title : item.test_title}</strong>
        <span>
          {isTeacher
            ? `${item.detail} · ${item.time}`
            : `${item.total_questions} Questions · ${item.percentage}%`}
        </span>
      </div>

      <strong className="activity-score">
        {isTeacher
          ? item.score
          : `${item.final_score}/${item.total_marks}`}
      </strong>
    </div>
  ))}

</section>

            </>
          
) : page === 'Take Test' ? (

  <section className="panel tests-panel">
    <button
      className="text-button"
      onClick={() => setPage('Dashboard')}
    >
      ← Back to Dashboard
    </button>

    <h2>{activeTest?.test_title || 'Take Test'}</h2>

    <p>
      Attempt ID: {activeAttempt?.attempt_id}
    </p>

    {testQuestions.length === 0 ? (
      <p>No questions available in this test.</p>
    ) : (
      testQuestions.map((question, index) => (
        <div className="question-card" key={question.id}>
          <h3>
            Q{index + 1}. {question.question_text}
          </h3>

          {question.options?.map((option) => (
            <label key={option.id} className="option-row">
              <input
                type="radio"
                name={`question-${question.id}`}
                value={option.id}
                checked={
                  String(selectedAnswers[question.id]) === String(option.id)
                }
                onChange={() =>
                  setSelectedAnswers((prev) => ({
                    ...prev,
                    [question.id]: option.id,
                  }))
                }
              />
              {option.option_text}
            </label>
          ))}

          <button
            className="primary-button"
            onClick={() => handleSubmitAnswer(question.id)}
          >
            Submit Answer
          </button>
        </div>
      ))
    )}

    {answerMessage && <p>{answerMessage}</p>}
  </section>

) : (

            <section className="panel placeholder-panel">

              <div className="placeholder-icon">
                <BookOpen size={30} />
              </div>

              <h2>{page}</h2>
              <p>This section is ready for the next development step.</p>

              <button
                className="primary-button"
                onClick={() => setPage('Dashboard')}
              >
                Back to Dashboard
              </button>

            </section>

          )}

          <footer className="footer">
            © 2026 SkillBridge. Empowering your career journey.
          </footer>

        </div>
      </main>
    </div>
  )
}

export default App 