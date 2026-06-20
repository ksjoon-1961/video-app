// sb (Supabase client) is initialized in index.html before this script loads

/* ── 화면 높이 보정 ── */
function setAppHeight() {
  document.documentElement.style.setProperty('--app-height', `${window.innerHeight}px`);
}
setAppHeight();
window.addEventListener('resize', setAppHeight);
window.addEventListener('orientationchange', () => setTimeout(setAppHeight, 150));

/* ── PWA 설치 프롬프트 ── */
let _installPrompt = null;

window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  _installPrompt = e;
  document.getElementById('install-btn').classList.remove('hidden');
});

window.addEventListener('appinstalled', () => {
  _installPrompt = null;
  document.getElementById('install-btn').classList.add('hidden');
});

async function handleInstall() {
  if (!_installPrompt) return;
  _installPrompt.prompt();
  const { outcome } = await _installPrompt.userChoice;
  if (outcome === 'accepted') {
    document.getElementById('install-btn').classList.add('hidden');
  }
  _installPrompt = null;
}

const authSection = document.getElementById('auth-section');
const userSection = document.getElementById('user-section');
const authMsg     = document.getElementById('auth-msg');

/* ── 현재 상세 화면에 표시 중인 영상 ── */
let _current = null;

/* ── 화면 전환 (홈 ↔ 상세) ── */
function showScreen(name) {
  if (name !== 'detail') closePlayer();
  ['home', 'detail'].forEach(s => {
    document.getElementById('screen-' + s).classList.toggle('hidden', s !== name);
  });
  document.querySelectorAll('.nav-item').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.screen === name);
  });
}

/* ── 영상 버튼 클릭 → 상세 화면 열기 ── */
function openDetail(video, token) {
  _current = { video, token };
  document.getElementById('detail-title').textContent = video.name;
  closePlayer();
  showDetailTab('info');
  showScreen('detail');
  playCurrent();
}

/* ── 상세 화면에서 현재 영상 재생 ── */
function playCurrent() {
  if (!_current) return;
  playVideo(_current.video.id, _current.token, document.querySelector('.detail-play-btn'));
}

/* ── 상세 탭 전환 ── */
function showDetailTab(name) {
  ['info', 'cast', 'watch', 'schedule', 'ratings', 'series'].forEach(t => {
    document.getElementById('tab-' + t).classList.toggle('hidden', t !== name);
  });
  document.querySelectorAll('.detail-tab').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === name);
  });
}

/* ── 로그인/회원가입 탭 전환 ── */
function showTab(tab) {
  document.getElementById('login-form').classList.toggle('hidden',  tab !== 'login');
  document.getElementById('signup-form').classList.toggle('hidden', tab !== 'signup');
  document.getElementById('tab-login').classList.toggle('active',   tab === 'login');
  document.getElementById('tab-signup').classList.toggle('active',  tab === 'signup');
  setMsg('');
}

/* ── 메시지 표시 ── */
function setMsg(text, isError = false) {
  authMsg.textContent = text;
  authMsg.className = 'msg' + (text ? (isError ? ' error' : ' success') : '');
}

/* ── 버튼 로딩 상태 ── */
function setLoading(btnId, loading) {
  const btn = document.getElementById(btnId);
  btn.disabled = loading;
  btn.textContent = loading ? '처리 중…'
    : (btnId === 'login-btn' ? '로그인' : '회원가입');
}

/* ── 플레이어 닫기 (포스터 정보 뷰로 복귀) ── */
function closePlayer() {
  const videoEl = document.getElementById('video-player');
  if (!videoEl) return;
  videoEl.pause();
  videoEl.src = '';
  videoEl.classList.add('hidden');
  document.querySelector('.player-close').classList.add('hidden');
  document.querySelector('#screen-detail .detail-header-row').classList.remove('hidden');
  const msg = document.getElementById('detail-player-msg');
  msg.textContent = '';
  msg.className = 'msg';
}

/* ── 영상 재생 (상세 포스터에서) ── */
async function playVideo(videoId, token, btn) {
  const videoEl  = document.getElementById('video-player');
  const closeBtn = document.querySelector('.player-close');
  const header   = document.querySelector('#screen-detail .detail-header-row');
  const msg      = document.getElementById('detail-player-msg');

  msg.textContent = '';
  msg.className = 'msg';

  const prevText = btn ? btn.textContent : '';
  if (btn) { btn.disabled = true; btn.textContent = '…'; }

  try {
    const res = await fetch(`/api/videos/${videoId}/url`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      msg.textContent = data.detail === 'video not ready'
        ? '준비 중입니다.'
        : '영상을 불러오지 못했습니다.';
      msg.className = 'msg error';
      return;
    }
    const { url } = await res.json();
    videoEl.src = url;
    videoEl.load();
    header.classList.add('hidden');
    closeBtn.classList.remove('hidden');
    videoEl.classList.remove('hidden');
    videoEl.play().catch(() => {});
  } catch (err) {
    msg.textContent = '오류: ' + err.message;
    msg.className = 'msg error';
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = prevText; }
  }
}

/* ── 영상 버튼 렌더링 ── */
async function loadVideos(token) {
  const container = document.getElementById('video-buttons');
  const status    = document.getElementById('videos-status');
  container.innerHTML = '';
  status.textContent  = '영상 목록 불러오는 중…';

  try {
    const res = await fetch('/api/videos', {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) { status.textContent = '목록을 불러오지 못했습니다.'; return; }

    const list = await res.json();
    status.textContent = '';

    if (list.length === 0) { status.textContent = '등록된 영상이 없습니다.'; return; }

    const GRID_COLS = 3;
    const GRID_ROWS = 4;
    const GRID_SIZE = GRID_COLS * GRID_ROWS;

    list.forEach(video => {
      const btn = document.createElement('button');
      btn.className   = 'video-btn';
      btn.textContent = video.name;

      if (video.is_ready) {
        btn.onclick = () => openDetail(video, token);
      } else {
        btn.classList.add('not-ready');
        btn.onclick = () => {
          const playerMsg = document.getElementById('player-msg');
          playerMsg.textContent = '준비 중입니다.';
          playerMsg.className = 'msg';
        };
      }
      container.appendChild(btn);
    });

    const remaining = GRID_SIZE - list.length;
    for (let i = 0; i < remaining; i++) {
      const btn = document.createElement('button');
      btn.className   = 'video-btn not-ready';
      btn.textContent = '준비 중';
      btn.onclick     = () => {};
      container.appendChild(btn);
    }
  } catch (err) {
    status.textContent = '오류: ' + err.message;
  }
}

/* ── 로그인 후 화면 전환 ── */
async function showUser(session) {
  authSection.classList.add('hidden');
  userSection.classList.remove('hidden');
  showScreen('home');
  document.getElementById('user-email').textContent = session.user.email;
  await loadVideos(session.access_token);
}

/* ── 로그인 모듈 가용 여부 확인 ── */
function ensureSb() {
  if (!sb) {
    setMsg('로그인 모듈을 불러오지 못했습니다. 새로고침 해주세요.', true);
    return false;
  }
  return true;
}

/* ── 로그인 ── */
async function handleLogin(e) {
  e.preventDefault();
  if (!ensureSb()) return;
  setLoading('login-btn', true);
  try {
    const { data, error } = await sb.auth.signInWithPassword({
      email:    document.getElementById('login-email').value,
      password: document.getElementById('login-password').value,
    });
    if (error) { setMsg(error.message, true); return; }
    await showUser(data.session);
  } catch (err) {
    setMsg('연결 오류: ' + (err.message || err), true);
  } finally {
    setLoading('login-btn', false);
  }
}

/* ── 회원가입 ── */
async function handleSignup(e) {
  e.preventDefault();
  if (!ensureSb()) return;
  setLoading('signup-btn', true);
  try {
    const { error } = await sb.auth.signUp({
      email:    document.getElementById('signup-email').value,
      password: document.getElementById('signup-password').value,
    });
    if (error) { setMsg(error.message, true); return; }
    setMsg('확인 이메일을 발송했습니다. 메일함을 확인해 주세요.');
  } catch (err) {
    setMsg('연결 오류: ' + (err.message || err), true);
  } finally {
    setLoading('signup-btn', false);
  }
}

/* ── 로그아웃 ── */
async function handleLogout() {
  closePlayer();
  await sb.auth.signOut();
  document.getElementById('video-buttons').innerHTML = '';
  document.getElementById('player-msg').textContent = '';
  document.getElementById('player-msg').className = 'msg';
  userSection.classList.add('hidden');
  authSection.classList.remove('hidden');
  setMsg('');
}

/* ── 페이지 로드 시 기존 세션 복원 ── */
if (sb) {
  sb.auth.getSession().then(({ data: { session } }) => {
    if (session) showUser(session);
  });
} else {
  setMsg('로그인 모듈을 불러오지 못했습니다. 새로고침 해주세요.', true);
}
