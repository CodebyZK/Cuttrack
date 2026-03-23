{% extends "base.html" %}
{% block title %}Create Account — CutTrack{% endblock %}
{% block body %}
<div class="auth-wrap">
  <div class="auth-card">
    <div class="auth-logo">CUT<span>TRACK</span></div>
    <p class="auth-sub">Create your account</p>
    {% if error %}
    <div class="auth-error">{{ error }}</div>
    {% endif %}
    <form method="POST" action="/register">
      <div class="field">
        <label>Username</label>
        <input type="text" name="username" autocomplete="username" autofocus required>
      </div>
      <div class="field">
        <label>Password</label>
        <input type="password" name="password" autocomplete="new-password" required>
      </div>
      <button type="submit" class="btn btn-full">CREATE ACCOUNT</button>
    </form>
  </div>
</div>
{% endblock %}
