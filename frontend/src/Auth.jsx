

import { useState } from "react";
import {
  GraduationCap, Mail, Lock, User, ArrowRight
} from "lucide-react";
import api from "./api";
import "./Auth.css";

export default function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true);
  const [role, setRole] = useState("student");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const switchMode = (loginMode) => {
    setIsLogin(loginMode);
    setError("");
    setMessage("");
    setPassword("");
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");

    if (!isLogin && role === "teacher") {
      setError(
        "Teacher registration requires an invitation code. We will connect it separately."
      );
      return;
    }

    setLoading(true);

    try {
      if (isLogin) {
        const response = await api.post("/login", {
          email,
          password,
        });

        const { access_token, user } = response.data;

        if (user.role !== role) {
          setError(
            `This account is registered as ${user.role}. Please select the correct role.`
          );
          return;
        }

        localStorage.setItem("access_token", access_token);
        localStorage.setItem("user", JSON.stringify(user));

        onLogin(user);
      } else {
        await api.post("/register", {
          name,
          email,
          password,
        });

        setMessage("Registration successful! Please login.");
        setIsLogin(true);
        setPassword("");
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to connect to server. Please check that your backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-card">

        <div className="auth-brand">
          <GraduationCap size={38} />
          <h1>SkillBridge</h1>
          <p>Build Skills. Shape Your Future.</p>
        </div>

        {/* Login / Register Tabs */}
        <div className="auth-tabs">
          <button
            type="button"
            className={isLogin ? "active" : ""}
            onClick={() => switchMode(true)}
          >
            Login
          </button>

          <button
            type="button"
            className={!isLogin ? "active" : ""}
            onClick={() => switchMode(false)}
          >
            Register
          </button>
        </div>

        <h2>
          {isLogin ? "Welcome Back!" : "Create Your Account"}
        </h2>

        <p className="auth-subtitle">
          {isLogin
            ? "Login to continue your learning journey."
            : "Join SkillBridge and start growing."}
        </p>

        {/* Role Selection */}
        <div className="role-options">
          <button
            type="button"
            className={role === "student" ? "selected" : ""}
            onClick={() => setRole("student")}
          >
            Student
          </button>

          <button
            type="button"
            className={role === "teacher" ? "selected" : ""}
            onClick={() => setRole("teacher")}
          >
            Teacher
          </button>
        </div>

        {error && <p className="auth-error">{error}</p>}
        {message && <p className="auth-success">{message}</p>}

        {/* Authentication Form */}
        <form onSubmit={handleSubmit}>

          {!isLogin && (
            <label>
              Full Name
              <div className="auth-input">
                <User size={18} />
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your name"
                  required
                />
              </div>
            </label>
          )}

          <label>
            Email Address
            <div className="auth-input">
              <Mail size={18} />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your email"
                required
              />
            </div>
          </label>

          <label>
            Password
            <div className="auth-input">
              <Lock size={18} />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                required
              />
            </div>
          </label>

          <button
            className="auth-submit"
            type="submit"
            disabled={loading}
          >
            {loading
              ? "Please wait..."
              : isLogin
                ? "Login to Dashboard"
                : "Create Account"}

            <ArrowRight size={18} />
          </button>

        </form>

        {/* Bottom Login / Register Switch */}
        <div className="auth-switch">
          {isLogin ? (
            <p>
              Don't have an account?{" "}
              <button
                type="button"
                onClick={() => switchMode(false)}
              >
                Register
              </button>
            </p>
          ) : (
            <p>
              Already have an account?{" "}
              <button
                type="button"
                onClick={() => switchMode(true)}
              >
                Login
              </button>
            </p>
          )}
        </div>

      </div>
    </div>
  );
}
