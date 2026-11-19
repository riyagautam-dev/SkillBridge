
import { useState, useEffect } from 'react'
import Auth from './Auth'
import api from "./api"
import {
  LayoutDashboard, Users, BookOpen, ClipboardList,
  ChartNoAxesCombined, Settings, Bell, Search, Menu, X,
  Plus, ArrowUpRight, Clock, CheckCircle2,
  GraduationCap, LogOut, UserRound, BrainCircuit, Trophy,
  ChevronDown
} from 'lucide-react'
import './App.css'

const studentStats = [
  { title: 'Tests Completed', value: '12', note: '+2 this week', icon: ClipboardList },
  { title: 'Average Score', value: '78%', note: '+5% this month', icon: ChartNoAxesCombined },
  { title: 'Skills Improved', value: '8', note: 'Across 4 categories', icon: BrainCircuit },
  { title: 'Learning Hours', value: '24h', note: 'This month', icon: Clock },
]

const teacherStats = [
  { title: 'Total Students', value: '128', note: 'Across all batches', icon: Users },
  { title: 'Active Tests', value: '08', note: 'Currently available', icon: ClipboardList },
  { title: 'Questions', value: '246', note: 'MCQ + Coding', icon: BookOpen },
  { title: 'Average Score', value: '76%', note: 'Across all tests', icon: Trophy },
]

const tests = [
  { name: 'Python Skill Assessment', type: 'MCQ + Coding', questions: 21, duration: '45 min', status: 'Available' },
  { name: 'Data Structures & Algorithms', type: 'Coding', questions: 10, duration: '60 min', status: 'Available' },
  { name: 'Database Management', type: 'MCQ', questions: 20, duration: '30 min', status: 'Completed' },
]

const activities = [
  { title: 'Python Skill Assessment', detail: 'Test completed', time: 'Today, 10:30 AM', score: '85%' },
  { title: 'Database Management', detail: 'Test completed', time: 'Yesterday', score: '72%' },
  { title: 'Programming Basics', detail: 'Test completed', time: '12 Nov 2026', score: '90%' },
]

function App() {
  const savedUser = JSON.parse(localStorage.getItem('user') || 'null')

  const [role, setRole] = useState(savedUser?.role || 'student')
  const [page, setPage] = useState('Dashboard')
  const [mobileOpen, setMobileOpen] = useState(false)

  const [isAuthenticated, setIsAuthenticated] = useState(
    Boolean(localStorage.getItem('access_token'))
  )

  // Student tests API states
  const [availableTests, setAvailableTests] = useState([])
  const [testsLoading, setTestsLoading] = useState(false)
  const [testsError, setTestsError] = useState("")

  // Fetch available tests from backend
  useEffect(() => {
    if (!isAuthenticated || role !== "student") return

    let isMounted = true

    const fetchAvailableTests = async () => {
      try {
        setTestsLoading(true)
        setTestsError("")

        const response = await api.get("/student/tests")

        if (isMounted) {
          setAvailableTests(response.data)
        }
      } catch (error) {
        if (isMounted) {
          setTestsError(
            error.response?.data?.detail || "Unable to load available tests."
          )
        }
      } finally {
        if (isMounted) {
          setTestsLoading(false)
        }
      }
    }

    fetchAvailableTests()

    return () => {
      isMounted = false
    }
  }, [isAuthenticated, role])

  const isTeacher = role === 'teacher'
  const stats = isTeacher ? teacherStats : studentStats

  // Prepare dashboard test data
  const dashboardTests = isTeacher
    ? tests
    : availableTests.map((test) => ({
        id: test.test_id,
        name: test.title,
        type: "—",
        questions: "—",
        duration: `${test.duration_minutes} min`,
        status: "Available",
      }))

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

          <button className="mobile-close" onClick={() => setMobileOpen(false)}>
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
              {name === 'AI Questions' && <span className="new-tag">AI</span>}
            </button>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-link" onClick={() => setPage('Settings')}>
            <Settings size={19} />
            <span>Settings</span>
          </button>

          <div className="sidebar-profile">
            <div className="avatar">{isTeacher ? 'T' : 'S'}</div>

            <div className="profile-info">
              <strong>{isTeacher ? 'Teacher Account' : 'Student Account'}</strong>
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
                      <h3>{isTeacher ? 'Performance Overview' : 'Your Performance'}</h3>
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
                        {[42, 65, 54, 82, 68, 91, 76].map((height, i) => (
                          <div className="bar-column" key={i}>
                            <div
                              className="bar"
                              style={{ height: `${height}%` }}
                            />
                            <span>
                              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][i]}
                            </span>
                          </div>
                        ))}
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

                      {testsLoading && !isTeacher ? (
                        <tr>
                          <td colSpan="6">Loading tests...</td>
                        </tr>
                      ) : testsError && !isTeacher ? (
                        <tr>
                          <td colSpan="6">{testsError}</td>
                        </tr>
                      ) : dashboardTests.length === 0 ? (
                        <tr>
                          <td colSpan="6">No available tests found.</td>
                        </tr>
                      ) : (
                        dashboardTests.map((test) => (
                          <tr key={test.id || test.name}>
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
                                onClick={() => setPage(isTeacher ? 'Manage Tests' : 'My Tests')}
                              >
                                →
                              </button>
                            </td>
                          </tr>
                        ))
                      )}

                    </tbody>
                  </table>
                </div>

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

                {activities.map((item) => (
                  <div className="activity-row" key={item.title}>
                    <div className="activity-icon">
                      <CheckCircle2 size={19} />
                    </div>

                    <div className="activity-description">
                      <strong>{item.title}</strong>
                      <span>{item.detail} · {item.time}</span>
                    </div>

                    <strong className="activity-score">{item.score}</strong>
                  </div>
                ))}

              </section>

            </>
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
