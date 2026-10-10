(function () {
  'use strict';

  var $ = function (id) { return document.getElementById(id); };

  /* ================= world channels ================= */
  var API = {
    topology:   '/api/topology',
    verts:      '/api/verts',
    state:      '/api/state',
    touchHit:   '/api/touch_hit',
    touchClear: '/api/touch_clear',
    progress:   '/api/progress'
  };

  var playerName = 'wanderer';
  var holding = false;        // true while the engine is holding a press
  var lessonsKnown = {};      // progress already saved under this name
  var judge = { woke: false, passed: false };
  var lastTouchForce = 0;
  /* H7 (D5 judge integrity): WHEN the hand last landed a press that the
     engine accepted. The judge refuses to latch a pressure goal unless the
     crossing happened inside this window -- "the qualifying input occurred
     under your hand". Without it a lesson could pass on residual or
     injected cell pressure that no press ever caused.
     L1 BY-HAND FIX: the window used to be a bare 2.5 s clock from the press
     START, so it expired while the player was still holding -- the walker's
     scripted 2.0-2.2 s presses fit inside it, but a human holding a press
     and watching the gauge climb (measured holds of 4-5 s in the by-hand
     audit) had the latch silently refuse mid-hold. While `holding` is true
     the press IS under the hand -- the engine holds it and every release
     funnel (pointerup, keyup, ESC, blur, tab-hide, let-go) clears it -- so
     the window stays open for the whole live press and keeps the 2.5 s
     tail for a crossing seen just after release. */
  var lastTouchAt = 0;
  function pressFresh() { return holding || (Date.now() - lastTouchAt < 2500); }
  /* H7 (D7): the engine's broken zero-volume cells (measured: cell4
     V=4.66e-9 m3 -- nominally zero, five orders below the smallest real
     compartment's 0.288 m3 -- reporting P up to 1.62 GPa; an engine-side
     defect another agent owns). A cell with no water has no pressure to
     judge or heal; the page skips it in every check and shows "sealed
     solid". Threshold 1e-6 m3 = 1 cm3: a real cell never gets near it. */
  var BROKEN_V_M3 = 1e-6;
  function brokenCell(c) {
    if (!c) return false;
    var v = Number(c.V);
    /* a MISSING V (pre-V engines) is not proof of brokenness -- judge on
       P as before; only a measured effectively-zero V is "sealed solid" */
    return isFinite(v) && v <= BROKEN_V_M3;
  }
  /* H9 AUDIO FIX: the wake-whoosh memo is WORLD-scoped (one whoosh per
     crossing across lesson switches); see the loop in judgeState. */
  var worldWokeMemo = {};

  /* W4 SOUND RAIL: every sound the page makes goes through snd() -- a
     window guard AND a try/catch, so a missing sound.js (failed load,
     no WebAudio) or a throwing synth can never break a game path: the
     failure mode is silence, never a dead page. Region hints pass the
     world points the page already holds (sound.js matches their Y
     against the live per-cell bands).
     H9 AUDIO FIX (failure visibility): silence is now DIAGNOSABLE. A
     missing synth or a throwing method used to vanish without a trace
     (measured live: an injected thrower, zero console output, no state
     anywhere). Failures count per method into window.__sndFailures, and
     with ?debug=1 the judge line carries a snd-fail tally. Still ZERO
     console output, ever -- only the visibility changed. */
  var sndFailures = {};
  window.__sndFailures = sndFailures;
  function snd(method) {
    try {
      var S = window.ChimeraSound;
      if (S && typeof S[method] === 'function')
        return S[method].apply(S, Array.prototype.slice.call(arguments, 1));
      sndFailures[method] = (sndFailures[method] || 0) + 1;
    } catch (err) {
      sndFailures[method] = (sndFailures[method] || 0) + 1;
    }
  }

  /* R4: the five lessons, data-driven (tools/game_shell/lessons.json) */
  var LESSONS = [];
  var lessonIdx = 0;
  var lessonShownAt = 0;       // L1: when the current lesson card was shown
                               // (the 25 s stall hint keys off this)
  var lessonState = {};        // id -> {goalMet, passed, phase}
  var JOINT_INDEX = { hip_L: 13, hip_R: 14, knee_L: 15, knee_R: 16,
                      ankle_L: 17, ankle_R: 18 };
  /* L1 BY-HAND FIX (judge 2: "the four blood cells are never labeled -- I
     poked the whole body to guess which is which"): the four compartments
     have NAMES -- the pack's own cell map -- and the page now speaks them:
     the blood panel, the pressed-part readout, and every lesson hint use
     the body part, not a bare index. */
  var CELL_PARTS = ['feet', 'torso', 'thighs', 'shins'];
  function cellPart(i) { return CELL_PARTS[i] || ('cell ' + i); }
  function cellIs(i) { return cellPart(i) + (i === 1 ? ' is' : ' are'); }
  /* W1 (R4, LESSON_JUDGE_SPEC §2/§9): the goal types this page implements.
     A lesson whose goal.type is not on this list HOLDS -- it can neither
     crash the judge nor pass by accident. */
  var KNOWN_GOAL_TYPES = ['pressure_above', 'pressure_below', 'pose_reach',
                          'pose_pair', 'gravity_on', 'cells_woken', 'pressure_isolation'];
  var POSE_TOL_DEG   = 2;     // pose intent tolerance around the goal deg
  var ROOT_VY_SETTLE = 0.05;  // m/s -- gravity_on "settled means settled"
  var ROOT_SETTLE_M  = 0.002; // m  -- the root left its authored rest
  var WOKEN_PA       = 20000; // Pa -- cells_woken wake bar (squeeze only)
  /* RUPTURE_FAILURE (SPEC new): a held press whose real cell climbs past this
     gauge pressure has burst the compartment — the lesson FAILS and the
     attempt locks until recovery. Chosen on the measured force->P map: lesson
     1's goal is 20 kPa, so 500 kPa gives ~25x headroom (a press that wakes the
     cell passes safely); the browser-click peak measured ~1.098 MPa and the
     vertex-snap belly peaks ~2.735 MPa at slider top, so 0.5 MPa sits below
     those — cranking the slider high and pressing hard on a strong point will
     reach it. Reachable by force, avoidable by a gentle hand. */
  var RUPTURE_PA     = 500000; // Pa (0.5 MPa)
  function curLesson() { return LESSONS[lessonIdx] || null; }
  function curState() {
    var l = curLesson();
    if (!l) return { goalMet: false, passed: false, phase: 'goal' };
    // W1: per-lesson latches -- pairOk (pose_pair, per joint), wokenSet
    // (cells_woken, distinct cell indices), gravityArmed (gravity_on).
    if (!lessonState[l.id]) lessonState[l.id] = { goalMet: false, passed: false,
      phase: 'goal', pairOk: {}, wokenSet: {}, gravityArmed: false,
      ruptured: false, rupturedCell: -1 };
    return lessonState[l.id];
  }
  async function loadLessons() {
    try {
      var d = await fetch('/lessons.json').then(function (r) { return r.json(); });
      LESSONS = d.lessons || [];
      showLesson(0);
    } catch (err) { setVerdict('the lesson scroll would not open.', 'warn'); }
  }
  async function showLesson(i) {
    if (!LESSONS.length) return;
    lessonIdx = (i + LESSONS.length) % LESSONS.length;
    var l = LESSONS[lessonIdx];
    /* H7 FIX (D1): a lesson STARTS fresh. The judge state used to persist
       per id for the whole session (goalMet / phase / per-cell memos rode
       over from any earlier visit), and the engine touch + lastTouchForce
       rode over from the PREVIOUS lesson -- the walker's the_heavy_hand and
       the_graduation sat in phase=release with a garbage cell blocking the
       calm check, and a press held in lesson N leaked its pressures into
       lesson N+1's judge. Only the PASSED latch survives (progress). */
    clearTouch();
    if (touchPulseTimer) { clearTimeout(touchPulseTimer); touchPulseTimer = null; }
    lastTouchForce = 0;
    lastTouchAt = 0;
    var st0 = lessonState[l.id];
    if (st0) {
      st0.goalMet = false; st0.phase = 'goal';
      st0.pairOk = {}; st0.wokenSet = {};
      st0.gravityArmed = false;
      st0.ruptured = false; st0.rupturedCell = -1;   // RUPTURE_FAILURE: clear a burst
      st0.primaryMet = false; st0.alsoMet = false; st0.halfNote = false;
      st0.pairNote = false; st0.forceNote = false; st0.hintShown = false;
    }
    lessonShownAt = Date.now();
    $('lesson-index').textContent = (lessonIdx + 1) + ' / ' + LESSONS.length;
    $('lesson-title').textContent = l.title;
    $('lesson-body').textContent = l.body;
    // W1 (SPEC §6): pose lessons get the pose-wish CONTROL -- one row per
    // wish (joint, angle slider the player sets, a post button per row).
    // L1 BY-HAND FIX: the old single button posted the goal verbatim (one
    // click passed; L6's single click posted BOTH wishes and then sat
    // inert). The lesson now demands its action.
    var isPose = l.goal.type === 'pose_reach' || l.goal.type === 'pose_pair';
    $('pose-btn-wrap').style.display = isPose ? 'block' : 'none';
    if (isPose) buildPoseCtrl(l);
    // L1 BY-HAND FIX: the gravity lesson's control is the player's -- the
    // page used to enable the world's weight itself at lesson start, so the
    // lesson passed with no action at all. Now the player presses it.
    var isGravity = l.goal.type === 'gravity_on';
    $('gravity-btn-wrap').style.display = isGravity ? 'block' : 'none';
    if (isGravity) {
      var gb = $('gravity-btn');
      gb.disabled = false;
      gb.textContent = "wake the world's weight";
    }
    // a pressure lesson must start with the body AT REST: a held pose
    // shifts the volumes off v0 and every calm check would dead-end.
    // H10-WALKER FIX: the reset is now AWAITED (and each joint post
    // retried -- see resetPose). It used to be fire-and-forget: under a
    // storm its six posts could all 429 silently and the next lesson's
    // judge window opened ON the previous lesson's held pose -- measured
    // live, the verdict flipped 8 ms after ']' while the cells still
    // carried the ankle pose's 6 MPa signature. Callers that do not
    // await showLesson simply move on; the window still opens only
    // after the world is verifiably back at rest.
    // L1 BY-HAND FIX: a POSE lesson no longer auto-resets 1.8 s after its
    // pass (the old timeout reset the body so fast that judge 1 "never saw
    // the knee bend"); the bend now STAYS until the player leaves -- and
    // entering any pressure lesson still resets, right here.
    if (!isPose) await resetPose();
    var st = curState();
    // G2 (SPEC §9, KNOWN_GOAL_TYPES hold guard): a lesson whose goal.type
    // the page has not implemented HOLDs AND SAYS SO -- judgeState already
    // refuses to latch or pass it; the verdict names the hold instead of
    // leaving the player waiting on a lesson that will never judge.
    if (KNOWN_GOAL_TYPES.indexOf(l.goal.type) < 0)
      setVerdict('the teachers have not built this lesson yet.', '');
    else if (st.passed) setVerdict('PASSED — this one is yours already. the controls below still answer — play it again.', 'good');
    else if (st.goalMet) setVerdict('the goal is met — finish the release.', 'accent');
    else if (isGravity) setVerdict("the creature waits at rest — wake the world's weight when you are ready.", '');
    else setVerdict('the creature waits.', '');
    syncTouchTarget();
    syncRuptureUI();                 // RUPTURE_FAILURE: a new lesson is not burst
  }

  /* L1 BY-HAND FIX: the pose-wish control. One row per wish: the joint's
     name, an angle slider the player sets by hand, and a post button that
     sends ONLY that wish. The judge (observePose) still latches on the
     engine's accepted post within +-2 degrees of the lesson's goal -- but
     now the player, not the button, chooses the angle. */
  function buildPoseCtrl(l) {
    var wrap = $('pose-btn-wrap');
    wrap.innerHTML = '';
    var wishes = (l.goal.type === 'pose_reach')
      ? [{ joint: l.goal.joint, deg: l.goal.deg }]
      : (l.goal.joints || []);
    for (var i = 0; i < wishes.length; i++) {
      var w = wishes[i];
      var suffix = (l.goal.type === 'pose_pair') ? '-' + i : '';
      var row = document.createElement('div');
      row.className = 'pose-row';
      row.id = 'pose-row' + suffix;
      row.innerHTML =
        '<span class="pose-joint">' + w.joint + '</span>' +
        '<input type="range" id="pose-angle' + suffix + '" min="-90" max="90" step="1" value="0"' +
        ' aria-label="' + w.joint + ' angle">' +
        '<span class="pose-val" id="pose-val' + suffix + '">' + w.joint + ' → 0°</span>' +
        '<button class="btn pose-post" id="pose-post' + suffix + '" type="button">post</button>';
      wrap.appendChild(row);
      (function (joint, sfx) {
        var angle = $('pose-angle' + sfx), val = $('pose-val' + sfx);
        angle.addEventListener('input', function () {
          val.textContent = joint + ' → ' + angle.value + '°';
          angle.style.setProperty('--fill', ((Number(angle.value) + 90) / 180 * 100) + '%');
        });
        angle.style.setProperty('--fill', ((Number(angle.value) + 90) / 180 * 100) + '%');
        $('pose-post' + sfx).addEventListener('click', async function () {
          var l2 = curLesson();
          if (!l2) return;
          var want = (l2.goal.type === 'pose_reach') ? l2.goal : (l2.goal.joints || []).filter(function (q) { return q.joint === joint; })[0];
          if (!want) return;
          var deg = Number(angle.value);
          var body = await postPose(JOINT_INDEX[joint], deg);
          if (!(body && body.ok === true)) { poseRefused(body); return; }
          if (Math.abs(deg - want.deg) <= POSE_TOL_DEG) {
            markPoseRow(sfx, true);                     // the wish is held
          } else {
            // HONEST REFUSAL (by-hand audit (d)): an accepted wish that is
            // not the lesson's wish says so, with both numbers.
            setVerdict('the wish held ' + joint + ' at ' + deg + '° — this lesson waits for ' +
              joint + ' at ' + want.deg + '°.', 'warn');
          }
        });
      })(w.joint, suffix);
    }
  }
  function markPoseRow(sfx, held) {
    var row = $('pose-row' + sfx);
    if (!row) return;
    row.classList.toggle('latched', !!held);
    var btn = $('pose-post' + sfx);
    if (btn && held) btn.textContent = 'held';
  }
  $('lesson-prev').addEventListener('click', function () { showLesson(lessonIdx - 1); });
  $('lesson-next').addEventListener('click', function () { showLesson(lessonIdx + 1); });
  /* H10-WALKER FIX (the false arm): the enable used to be
     postJSON(...).then(armed = true) -- and fetch RESOLVES on any http
     answer, so a 429'd enable armed the judge over a world whose gravity
     was never turned on (measured live: 1x429 -> armed=true, root_y still
     exactly 0 -- the stand could never latch and the walker's diagnostic
     fallback was silenced by the lie). Arm ONLY on the engine's own
     ok:true body; retry the enable gently; if the world will not take it,
     the link line says so and the judge stays honestly unarmed. */
  async function enableGravity(stg) {
    for (var attempt = 0; attempt < 3; attempt++) {
      if (attempt) await sleepTouch(400 * attempt * (0.7 + 0.6 * Math.random()));
      try {
        var res = await postJSON('/api/gravity', { on: true });
        var body = null;
        try { body = await res.json(); } catch (e) { body = null; }
        if (res.ok && body && body.ok === true) { stg.gravityArmed = true; return; }
        if (res.status !== 429 && res.status < 500) break;   // refused: do not spin
      } catch (err) { /* network: retry */ }
    }
    stg.gravityArmed = false;
    setLink('the world did not take the gravity wish — the judge stays unarmed.');
  }
  /* W1 (SPEC §6): EVERY pose the page sends rides this one sender, and the
     judge observes it here. The latch fires only when the ENGINE accepted
     (body ok:true) -- a refused post comes back HTTP 200 with ok:false and
     never latches. */
  async function postPose(joint_index, deg) {
    var body = null;
    try {
      var res = await postJSON('/api/pose', { joint_index: joint_index, deg: deg });
      body = await res.json();
    } catch (err) { body = null; }
    observePose(joint_index, deg, !!(body && body.ok === true));
    return body;
  }
  /* L1 BY-HAND FIX: which pose row carries this joint (for the held mark) */
  function poseRowSuffix(joint) {
    var l = curLesson();
    if (!l) return '';
    if (l.goal.type === 'pose_reach') return (l.goal.joint === joint) ? '' : null;
    var js = l.goal.joints || [];
    for (var i = 0; i < js.length; i++)
      if (js[i].joint === joint) return '-' + i;
    return null;
  }
  function observePose(joint_index, deg, accepted) {
    var l = curLesson();
    if (!l) return;
    var g = l.goal;
    if (g.type !== 'pose_reach' && g.type !== 'pose_pair') return;  // pose goals only
    var st = curState();
    /* L1 BY-HAND FIX (judge 2's L4: the chip "stayed on screen and my click
       on it did nothing"): a PASSED lesson's pose control stays LIVE. A
       replayed wish that matches the goal re-speaks the lesson's own pass
       line instead of being swallowed. */
    if (st.passed) {
      if (!accepted) return;
      var wishes = (g.type === 'pose_reach') ? [g] : (g.joints || []);
      for (var rp = 0; rp < wishes.length; rp++) {
        var wr = wishes[rp];
        if (joint_index === JOINT_INDEX[wr.joint] &&
            Math.abs(deg - wr.deg) <= POSE_TOL_DEG) {
          snd('passed');
          setVerdict(passLine(l, 'the lesson is yours.'), 'good');
          var sfx0 = poseRowSuffix(wr.joint);
          if (sfx0 !== null) markPoseRow(sfx0, true);
        }
      }
      return;
    }
    if (!accepted) return;      // refused: do not latch
    if (g.type === 'pose_reach') {
      if (joint_index === JOINT_INDEX[g.joint] && Math.abs(deg - g.deg) <= POSE_TOL_DEG) {
        st.goalMet = true; st.passed = true;
        snd('passed');
        // the lesson's OWN pass line, and it STAYS: the knee keeps its bend
        // until the player leaves (entering any pressure lesson resets).
        setVerdict(passLine(l, 'the joint obeys the muscle.'), 'good');
      }
    } else {
      // W1 pose_pair: per-joint sticky latches, any order, any moments
      for (var i = 0; i < g.joints.length; i++) {
        var j = g.joints[i];
        if (joint_index === JOINT_INDEX[j.joint] &&
            Math.abs(deg - j.deg) <= POSE_TOL_DEG) {
          st.pairOk[j.joint] = true;
          var sfx = poseRowSuffix(j.joint);
          if (sfx !== null) markPoseRow(sfx, true);
        }
      }
      var all = true, k;
      for (k = 0; k < g.joints.length; k++)
        if (!st.pairOk[g.joints[k].joint]) all = false;
      if (all) {
        st.goalMet = true; st.passed = true;
        snd('passed');
        setVerdict(passLine(l, 'two wishes, one balance.'), 'good');
      } else {
        setVerdict('one wish is held — the other waits.', 'accent');
      }
    }
  }
  async function resetPose() {
    // return EVERY joint to rest: the volumes follow exactly (measured
    // pixel-exact) and the pressure lessons' calm bar becomes reachable
    // (W1: rides postPose, so the judge observes the page's only pose path)
    // H10-WALKER FIX: each joint post is RETRIED until the engine takes
    // it -- a silently-dropped post used to leave that joint held and
    // the calm bar unreachable for the whole lesson.
    for (var j in JOINT_INDEX) {
      for (var attempt = 0; attempt < 3; attempt++) {
        var body = await postPose(JOINT_INDEX[j], 0);
        if (body && body.ok === true) break;
        if (attempt < 2)
          await sleepTouch(400 * (attempt + 1) * (0.7 + 0.6 * Math.random()));
      }
    }
  }
  /* H7 (D7): a refused pose now says WHY -- the engine's own error text
     ("the pose was refused." with no reason was the H5 dry-run's S7). */
  function poseRefused(body) {
    var why = (body && body.error) ? String(body.error) : 'the world gave no reason.';
    setVerdict('the pose was refused — ' + why, 'warn');
  }

  /* L1 BY-HAND FIX (the_stand): the world's weight is the PLAYER'S verb
     now. The judge arms only when this click's enable resolves ok:true
     (H10's false-arm fix carries over), so the pass always sits downstream
     of a real press. */
  $('gravity-btn').addEventListener('click', async function () {
    var l = curLesson();
    if (!l || l.goal.type !== 'gravity_on') return;
    var stg = curState();
    if (stg.gravityArmed) return;
    var gb = $('gravity-btn');
    gb.disabled = true;
    gb.textContent = 'the world is taking the weight…';
    stg.gravityArmed = false;
    await enableGravity(stg);
    if (stg.gravityArmed) {
      gb.textContent = "the world's weight is on";
      setVerdict("the world's weight is on — watch the body settle into stillness.", 'accent');
    } else {
      gb.disabled = false;
      gb.textContent = "wake the world's weight";
    }
  });

  var verdictEl = $('verdict');
  var handEl = $('hand-state');
  var bloodEl = $('blood');
  var linkEl = $('link-state');
  var forceEl = $('force');
  var forceLabel = $('force-label');

  function setVerdict(text, tone) {
    verdictEl.textContent = text;
    verdictEl.className = 'verdict' + (tone ? ' ' + tone : '');
    /* H7 (D6): while the unreachable note holds the verdict line, the save
       follows the live verdict -- a judge that speaks through a partial
       starvation is never clobbered by the restore. */
    if (savedVerdict !== null && savedVerdict !== undefined) {
      savedVerdict.text = text;
      savedVerdict.cls = verdictEl.className;
    }
  }
  /* H7 FIX (D5): every lesson passes in its own words. The pack carries a
     per-lesson pass_line now (lessons.json); the page used to speak ONE
     shared release sentence for every then_release lesson, so an unearned
     pass was indistinguishable from an earned one. */
  function passLine(l, fallback) {
    return 'PASSED — ' + (l && l.pass_line ? l.pass_line : fallback);
  }
  function setHand(text) { handEl.textContent = text; }
  var lastLink = null;
  function setLink(text) {
    if (text === lastLink) return;
    lastLink = text;
    linkEl.textContent = text;
  }

  /* RUPTURE_FAILURE: keep the 'try again' control visible only while this
     attempt is locked on a burst cell. Called every judge poll so it stays in
     step with st.ruptured without its own timer. */
  function syncRuptureUI() {
    var w = $('try-again-wrap');
    if (!w) return;
    var l = curLesson();
    var rup = !!(l && lessonState[l.id] && lessonState[l.id].ruptured);
    w.style.display = rup ? 'block' : 'none';
  }

  /* RUPTURE_FAILURE RECOVERY: clear this lesson's judge latches (including the
     rupture latch) and any held engine touch so the player can immediately
     re-attempt the SAME lesson. Deliberately does NOT move the card or re-POST
     poses — it only un-latches, like a trimmed startLesson for one lesson. */
  function retryLesson() {
    clearTouch();   // end any held press + send /api/touch_clear (retry-backed)
    var l = curLesson();
    if (!l) return;
    var st = curState();
    st.ruptured = false; st.rupturedCell = -1;
    st.goalMet = false; st.phase = 'goal';
    st.pairOk = {}; st.wokenSet = {}; st.gravityArmed = false;
    st.primaryMet = false; st.alsoMet = false; st.halfNote = false;
    st.pairNote = false; st.forceNote = false; st.hintShown = false;
    pressedCell = -1; pressedNoteShown = false;
    lessonShownAt = Date.now();
    setVerdict('the creature waits.', '');
  }

  function postJSON(url, body) {
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
  }

  /* ================= shaders ================= */
  /* Creature: one directional light + a faint rim. uCam feeds the rim's view dir. */
  /* W2 THE VISIBLE DENT: the vertex shader renders the page's own press
     kernel — the engine's exact linear-membrane law (delta = F/(4 pi sigma),
     Gaussian falloff) — as a REPLACEMENT, not an addition: per vertex the
     pre-press rest position is displaced once by the law at a display-
     sized regularization radius. Diagnosis
     (docs/evidence/agent_fleet/SHIP/W2_DIMPLE_VISIBLE/): the streamed
     /verts ALREADY carries the engine's dent (measured 0.3979 m at 20 kN —
     the law, exactly) and the page uploads it faithfully — but the
     engine's kernel radius (3 cm) is below this mesh's own vertex spacing
     (~3.7 cm near the belly), so the answer renders as a 7x27 px hairline
     slit: technically present, invisible to every buyer (the engine's own
     /frame of the same press renders it as ONE pixel). Adding a second
     kernel on top DOUBLES the center displacement (measured at 50 kN:
     server 1 m + page 1 m = 2 m — the cup floor pierced the body), so the
     page displaces the REST surface by the law ONCE: the rendered dent is
     exactly the law's amplitude — the same number the HUD reports.
     The streamed buffer is untouched (RG.verts stays a faithful mirror of
     /api/verts — the H16 bit-parity still holds and the pick still
     raycasts the true streamed surface); the kernel lives in this shader
     plus the rest snapshot only.
     THE PATCH GATE: a wide kernel on a body with limbs also reaches
     vertices on OTHER parts (the far side of a hip, the thigh beside the
     belly) — measured, an ungated 0.4 m kernel sucked the whole groin
     region inward. The gate restricts the kernel to the same-facing
     surface patch: full weight while the vertex normal stays within 60
     degrees of the press-point normal, zero past perpendicular — the
     same surface a finger deforms, no more. */
  var VSH = [
    '#version 300 es',
    'in vec3 aPos;',
    'in vec3 aNormal;',
    'in vec3 aColor;',
    'in vec3 aRestPos;',
    'in vec3 aRestN;',
    'uniform mat4 uVP;',
    'uniform vec3 uHit;',
    'uniform vec3 uHitN;',
    'uniform float uAmp;',
    'uniform float uRad;',
    'uniform float uReplace;',
    'out vec3 vNormal;',
    'out vec3 vColor;',
    'out vec3 vWorld;',
    'void main() {',
    '  vec3 p = aPos;',
    '  vec3 n = aNormal;',
    '  if (uAmp > 0.0) {',
    '    vec3 p0 = mix(aPos, aRestPos, uReplace);',
    '    vec3 n0 = normalize(mix(aNormal, aRestN, uReplace));',
    '    float gate = dot(uHitN, uHitN) < 0.5 ? 1.0',
    '                                        : smoothstep(0.0, 0.5, dot(n0, uHitN));',
    '    vec3 dv = p0 - uHit;',
    '    float d = length(dv);',
    '    float q = d / uRad;',
    '    float off = uAmp * exp(-q * q) * gate;',
    '    p = p0 - n0 * off;',
    '    vec3 tang = dv - n0 * dot(dv, n0);',
    '    float ut = length(tang);',
    '    if (d > 1e-5 && ut > 1e-5) {',
    '      float slope = 2.0 * off * d / (uRad * uRad);',  // |d(off)/dd|, exp included
    '      n = normalize(n0 - (tang / ut) * slope);',  // normals lean into the cup
    '    } else {',
    '      n = n0;',
    '    }',
    '  }',
    '  vNormal = n;',
    '  vColor = aColor;',
    '  vWorld = p;',
    '  gl_Position = uVP * vec4(p, 1.0);',
    '}'
  ].join('\n');

  var FSH = [
    '#version 300 es',
    'precision highp float;',
    'in vec3 vNormal;',
    'in vec3 vColor;',
    'in vec3 vWorld;',
    'uniform vec3 uCam;',
    'out vec4 outColor;',
    'void main() {',
    '  vec3 n = normalize(vNormal);',
    '  vec3 l = normalize(vec3(0.4, 0.8, 0.3));',
    '  vec3 col = vColor * (0.35 + 0.65 * max(dot(n, l), 0.0));',
    '  vec3 v = normalize(uCam - vWorld);',
    '  float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0) * 0.15;',
    '  outColor = vec4(col + rim, 1.0);',
    '}'
  ].join('\n');

  /* Grid: unlit, one flat color, position only. */
  var GRID_VSH = [
    '#version 300 es',
    'in vec3 aPos;',
    'uniform mat4 uVP;',
    'void main() { gl_Position = uVP * vec4(aPos, 1.0); }'
  ].join('\n');

  var GRID_FSH = [
    '#version 300 es',
    'precision mediump float;',
    'uniform vec3 uColor;',
    'out vec4 outColor;',
    'void main() { outColor = vec4(uColor, 1.0); }'
  ].join('\n');

  /* ================= renderer ================= */
  var canvas = $('gl');
  var gl = null;
  try { gl = canvas.getContext('webgl2', { antialias: true }); } catch (e) { gl = null; }

  /* CONTEXT-LOSS SAFETY NET. Reassigning canvas.width/height recreates the GL
     context and fires CONTEXT_LOST_WEBGL, and this page has no other restore
     path — so a resize would otherwise blank the screen forever (that was the
     headless-canvas bug). oncontextlost pauses the render loop; oncontextrestored
     rebuilds programs/buffers/VAOs via initRenderer(), re-pushes the stored mesh
     into the freshly-created buffers, and resumes. The backing store is still
     set exactly once (see frame) so this recovers at most one time per resize. */
  var ctxLive = true;
  if (gl) {
    gl.oncontextlost = function (e) { e.preventDefault(); ctxLive = false; return false; };
    gl.oncontextrestored = function () {
      ctxLive = true;
      try { RG = initRenderer(); reuploadMesh(); requestAnimationFrame(frame); } catch (e) {}
    };
  }

  /* Re-push the stored topology + verts into freshly-rebuilt buffers after a
     context restore. loadTopology / pollVerts keep RG.idx / RG.verts in memory;
     this moves them into the new GL handles that initRenderer just recreated. */
  function reuploadMesh() {
    if (!RG) return;
    if (RG.idx && RG.triCount) {
      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, RG.ibo);
      gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, RG.idx.byteLength, gl.STATIC_DRAW);
      gl.bufferSubData(gl.ELEMENT_ARRAY_BUFFER, 0, RG.idx);
    }
    if (RG.verts) {
      gl.bindBuffer(gl.ARRAY_BUFFER, RG.vbo);
      gl.bufferData(gl.ARRAY_BUFFER, RG.verts.byteLength, gl.DYNAMIC_DRAW);
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, RG.verts);
    }
  }

  var RG = null;   // renderer state, null when WebGL2 is unavailable
  var sizeInitialized = false;   // backing store set exactly once (see frame)
  var UP = [0, 1, 0];

  function initRenderer() {
    function sh(type, src) {
      var s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        throw new Error(gl.getShaderInfoLog(s) || 'shader compile failed');
      }
      return s;
    }
    function prog(vsSrc, fsSrc) {
      var p = gl.createProgram();
      gl.attachShader(p, sh(gl.VERTEX_SHADER, vsSrc));
      gl.attachShader(p, sh(gl.FRAGMENT_SHADER, fsSrc));
      gl.linkProgram(p);
      if (!gl.getProgramParameter(p, gl.LINK_STATUS)) {
        throw new Error(gl.getProgramInfoLog(p) || 'program link failed');
      }
      return p;
    }

    // THE SHADOW (same planar projection as the engine's fix): the creature
    // projected straight down onto the floor, alpha falling with height.
    var SHADOW_VSH = [
      '#version 300 es',
      'layout(location=0) in vec3 aPos;',
      'uniform mat4 uVP;',
      'uniform float uFloorY;',
      'uniform float uH0;',
      'out float vA;',
      'void main(){',
      '  float h = max(aPos.y - uFloorY, 0.0);',
      '  vA = 0.38 / (1.0 + h / max(uH0, 0.001));',
      '  gl_Position = uVP * vec4(aPos.x, uFloorY, aPos.z, 1.0);',
      '}'].join('\n');
    var SHADOW_FSH = [
      '#version 300 es',
      'precision highp float;',
      'in float vA;',
      'out vec4 o;',
      'void main(){ o = vec4(0.02, 0.03, 0.05, vA); }'].join('\n');
    var r = {
      prog: prog(VSH, FSH),
      gridProg: prog(GRID_VSH, GRID_FSH),
      shadowProg: prog(SHADOW_VSH, SHADOW_FSH),
      vbo: gl.createBuffer(),
      ibo: gl.createBuffer(),
      restVbo: gl.createBuffer(),   // W2: the pre-press rest surface (pos+nrm)
      vao: gl.createVertexArray(),
      shadowVao: gl.createVertexArray(),
      gridVbo: gl.createBuffer(),
      gridVao: gl.createVertexArray(),
      gridCount: 0,
      triCount: 0,
      vertCount: 0,
      vboSized: false,
      restSized: false,
      restDirty: false,
      idx: null,     // local Uint32Array copy of the triangle indices
      verts: null    // interleaved Float32Array: [pos3, normal3, color3] per vertex
    };
    r.uVP = gl.getUniformLocation(r.prog, 'uVP');
    r.uCam = gl.getUniformLocation(r.prog, 'uCam');
    r.uHit = gl.getUniformLocation(r.prog, 'uHit');   // W2: the press kernel
    r.uHitN = gl.getUniformLocation(r.prog, 'uHitN');
    r.uAmp = gl.getUniformLocation(r.prog, 'uAmp');
    r.uRad = gl.getUniformLocation(r.prog, 'uRad');
    r.uReplace = gl.getUniformLocation(r.prog, 'uReplace');
    r.aRestPos = gl.getAttribLocation(r.prog, 'aRestPos');
    r.aRestN = gl.getAttribLocation(r.prog, 'aRestN');
    r.aPos = gl.getAttribLocation(r.prog, 'aPos');
    r.aNormal = gl.getAttribLocation(r.prog, 'aNormal');
    r.aColor = gl.getAttribLocation(r.prog, 'aColor');
    r.sVP = gl.getUniformLocation(r.shadowProg, 'uVP');
    r.sFloor = gl.getUniformLocation(r.shadowProg, 'uFloorY');
    r.sH0 = gl.getUniformLocation(r.shadowProg, 'uH0');
    r.gVP = gl.getUniformLocation(r.gridProg, 'uVP');
    r.gColor = gl.getUniformLocation(r.gridProg, 'uColor');
    r.gPos = gl.getAttribLocation(r.gridProg, 'aPos');

    /* shadow VAO: same buffers, positions only */
    gl.bindVertexArray(r.shadowVao);
    gl.bindBuffer(gl.ARRAY_BUFFER, r.vbo);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, r.ibo);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 36, 0);

    /* creature VAO: one interleaved VBO, stride 36 bytes (offsets 0 / 12 / 24) */
    gl.bindVertexArray(r.vao);
    gl.bindBuffer(gl.ARRAY_BUFFER, r.vbo);
    gl.enableVertexAttribArray(r.aPos);
    gl.vertexAttribPointer(r.aPos, 3, gl.FLOAT, false, 36, 0);
    gl.enableVertexAttribArray(r.aNormal);
    gl.vertexAttribPointer(r.aNormal, 3, gl.FLOAT, false, 36, 12);
    gl.enableVertexAttribArray(r.aColor);
    gl.vertexAttribPointer(r.aColor, 3, gl.FLOAT, false, 36, 24);
    /* W2: the rest surface rides its own VBO, [pos3, normal3] per vertex */
    gl.bindBuffer(gl.ARRAY_BUFFER, r.restVbo);
    gl.enableVertexAttribArray(r.aRestPos);
    gl.vertexAttribPointer(r.aRestPos, 3, gl.FLOAT, false, 24, 0);
    gl.enableVertexAttribArray(r.aRestN);
    gl.vertexAttribPointer(r.aRestN, 3, gl.FLOAT, false, 24, 12);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, r.ibo);
    gl.bindVertexArray(null);

    /* ground grid: 41 lines each way = a 40x40 grid on [-20, 20] at y = 0 */
    var g = [];
    for (var i = -20; i <= 20; i++) {
      g.push(i, 0, -20, i, 0, 20);   // line running along z
      g.push(-20, 0, i, 20, 0, i);   // line running along x
    }
    var gridVerts = new Float32Array(g);
    r.gridCount = gridVerts.length / 3;
    gl.bindVertexArray(r.gridVao);
    gl.bindBuffer(gl.ARRAY_BUFFER, r.gridVbo);
    gl.bufferData(gl.ARRAY_BUFFER, gridVerts, gl.STATIC_DRAW);
    gl.enableVertexAttribArray(r.gPos);
    gl.vertexAttribPointer(r.gPos, 3, gl.FLOAT, false, 0, 0);
    gl.bindVertexArray(null);

    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
    gl.clearColor(0x0b / 255, 0x0d / 255, 0x10 / 255, 1);
    return r;
  }

  /* ================= camera ================= */
  var cam = {
    r: 26, theta: -0.55, phi: 0.42,
    target: [0, 4.5, 0],
    fov: 45 * Math.PI / 180, near: 0.1, far: 1000
  };

  function camEye(out) {
    var ch = Math.cos(cam.phi);
    out[0] = cam.target[0] + cam.r * ch * Math.sin(cam.theta);
    out[1] = cam.target[1] + cam.r * Math.sin(cam.phi);
    out[2] = cam.target[2] + cam.r * ch * Math.cos(cam.theta);
    return out;
  }

  /* column-major mat4 helpers */
  function perspective(out, fovy, aspect, near, far) {
    var f = 1 / Math.tan(fovy / 2), nf = 1 / (near - far);
    out[0] = f / aspect; out[1] = 0; out[2] = 0; out[3] = 0;
    out[4] = 0; out[5] = f; out[6] = 0; out[7] = 0;
    out[8] = 0; out[9] = 0; out[10] = (far + near) * nf; out[11] = -1;
    out[12] = 0; out[13] = 0; out[14] = 2 * far * near * nf; out[15] = 0;
  }
  function lookAt(out, eye, center, up) {
    var zx = eye[0] - center[0], zy = eye[1] - center[1], zz = eye[2] - center[2];
    var len = 1 / (Math.hypot(zx, zy, zz) || 1);
    zx *= len; zy *= len; zz *= len;
    var xx = up[1] * zz - up[2] * zy, xy = up[2] * zx - up[0] * zz, xz = up[0] * zy - up[1] * zx;
    len = 1 / (Math.hypot(xx, xy, xz) || 1);
    xx *= len; xy *= len; xz *= len;
    var yx = zy * xz - zz * xy, yy = zz * xx - zx * xz, yz = zx * xy - zy * xx;
    out[0] = xx; out[1] = yx; out[2] = zx; out[3] = 0;
    out[4] = xy; out[5] = yy; out[6] = zy; out[7] = 0;
    out[8] = xz; out[9] = yz; out[10] = zz; out[11] = 0;
    out[12] = -(xx * eye[0] + xy * eye[1] + xz * eye[2]);
    out[13] = -(yx * eye[0] + yy * eye[1] + yz * eye[2]);
    out[14] = -(zx * eye[0] + zy * eye[1] + zz * eye[2]);
    out[15] = 1;
  }
  function mul(out, a, b) {
    for (var c = 0; c < 4; c++) {
      var b0 = b[c * 4], b1 = b[c * 4 + 1], b2 = b[c * 4 + 2], b3 = b[c * 4 + 3];
      out[c * 4 + 0] = a[0] * b0 + a[4] * b1 + a[8] * b2 + a[12] * b3;
      out[c * 4 + 1] = a[1] * b0 + a[5] * b1 + a[9] * b2 + a[13] * b3;
      out[c * 4 + 2] = a[2] * b0 + a[6] * b1 + a[10] * b2 + a[14] * b3;
      out[c * 4 + 3] = a[3] * b0 + a[7] * b1 + a[11] * b2 + a[15] * b3;
    }
  }

  var mProj = new Float32Array(16);
  var mView = new Float32Array(16);
  var mVP = new Float32Array(16);
  var eyeScratch = [0, 0, 0];

  /* W2 THE VISIBLE DENT — the press kernel's state. One press at a time,
     exactly the engine's model (touch_press_at replaces the point). The
     constants are the ENGINE'S OWN named law, not page taste: sigma_n =
     4000 N/m (skin working tension, membrane_tick.hpp) sets the amplitude,
     tau_relax = 0.5 s sets the release decay, and the 0.1 mm cutoff clears
     the kernel — the same deterministic rest the engine reaches. The
     regularization radius rides the amplitude (rad = amp), which is a
     shape law, not a tuned size: cup depth equals cup radius, so the
     response always reads as a dimple at any force the slider can send. */
  var nativeBodySurface = false; // negotiated from engine state; one geometry owner
  var pressKernel = { hit: null, n: null, delta: 0, radMax: 0,
                      holding: false, tClear: 0 };
  var W2_SIGMA = 4000;          // N/m  — engine sigma_n_
  var W2_TAU = 0.5;             // s    — engine tau_relax_
  var W2_CUTOFF = 1e-4;         // m    — engine's 0.1 mm deterministic rest
  var meshRest = null;          // W2: pre-press rest surface [pos3, nrm3] per vertex
  /* The rest snapshot mirrors the stream ONLY outside the live kernel's
     reach: inside it, the streamed surface is dented and must never leak
     into the rest reference. Outside it the mirror tracks poses and idle
     motion exactly. The GL upload (restVbo) happens only while NO kernel
     lives, so during a press the shader sees the pre-press surface. */
  function w2UpdateRest() {
    if (!RG || !RG.verts || !RG.vertCount) return;
    var n = RG.vertCount;
    if (!meshRest || meshRest.length !== n * 6) meshRest = new Float32Array(n * 6);
    var hit = pressKernel.hit;
    var freeze2 = 0;
    if (hit) { var rr = 3 * (pressKernel.radMax || pressKernel.delta); freeze2 = rr * rr; }
    for (var v = 0; v < n; v++) {
      if (freeze2 > 0) {
        var dx = meshRest[v * 6] - hit[0], dy = meshRest[v * 6 + 1] - hit[1],
            dz = meshRest[v * 6 + 2] - hit[2];
        if (dx * dx + dy * dy + dz * dz < freeze2) continue;   // frozen: pre-press
      }
      meshRest[v * 6]     = RG.verts[v * 9];
      meshRest[v * 6 + 1] = RG.verts[v * 9 + 1];
      meshRest[v * 6 + 2] = RG.verts[v * 9 + 2];
      meshRest[v * 6 + 3] = RG.verts[v * 9 + 3];
      meshRest[v * 6 + 4] = RG.verts[v * 9 + 4];
      meshRest[v * 6 + 5] = RG.verts[v * 9 + 5];
    }
    RG.restDirty = true;
  }
  function pressKernelStart(hit, force) {
    if (nativeBodySurface) return;
    pressKernel.hit = [hit[0], hit[1], hit[2]];
    pressKernel.delta = force / (4 * Math.PI * W2_SIGMA);
    pressKernel.radMax = pressKernel.delta;   // the rest snapshot's freeze reach
    /* the patch gate's reference normal: the streamed normal of the vertex
       nearest the hit (the same snap the POST used) */
    pressKernel.n = null;
    if (meshPos && RG && RG.verts) {
      var best = -1, bd = Infinity;
      for (var i = 0, n = meshPos.length / 3; i < n; i++) {
        var dx = meshPos[i * 3] - hit[0], dy = meshPos[i * 3 + 1] - hit[1],
            dz = meshPos[i * 3 + 2] - hit[2];
        var d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < bd) { bd = d2; best = i; }
      }
      if (best >= 0)
        pressKernel.n = [RG.verts[best * 9 + 3], RG.verts[best * 9 + 4],
                         RG.verts[best * 9 + 5]];
    }
    pressKernel.holding = true;
  }
  function pressKernelRelease() {
    if (!pressKernel.holding) return;
    pressKernel.holding = false;
    pressKernel.tClear = performance.now();
  }
  function pressKernelTick() {
    if (!RG) return;
    if (nativeBodySurface) {
      pressKernel.hit = null; pressKernel.holding = false;
      gl.useProgram(RG.prog);
      gl.uniform1f(RG.uAmp, 0); gl.uniform1f(RG.uReplace, 0);
      return; // render the same surface used for picking and native pressures
    }
    /* the rest surface reaches the GPU only while NO kernel lives — during
       a press (and its tau decay) the shader displaces the frozen
       pre-press snapshot, so the law is applied ONCE, not doubled */
    if (RG.restDirty && !pressKernel.hit && meshRest) {
      gl.bindBuffer(gl.ARRAY_BUFFER, RG.restVbo);
      if (!RG.restSized) {
        gl.bufferData(gl.ARRAY_BUFFER, meshRest.byteLength, gl.DYNAMIC_DRAW);
        RG.restSized = true;
      }
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, meshRest);
      RG.restDirty = false;
    }
    var amp = 0, hit = pressKernel.hit;
    if (hit) {
      amp = pressKernel.delta;
      if (!pressKernel.holding) {
        amp *= Math.exp(-(performance.now() - pressKernel.tClear) / 1000 / W2_TAU);
        if (amp < W2_CUTOFF) { pressKernel.hit = null; amp = 0; }   // deterministic rest
      }
    }
    gl.useProgram(RG.prog);
    if (hit && amp > 0) {
      gl.uniform3f(RG.uHit, hit[0], hit[1], hit[2]);
      var kn = pressKernel.n;
      if (kn) gl.uniform3f(RG.uHitN, kn[0], kn[1], kn[2]);
      else gl.uniform3f(RG.uHitN, 0, 0, 0);       // no reference: gate disabled
      gl.uniform1f(RG.uAmp, amp);
      gl.uniform1f(RG.uRad, amp);       // the cup law: falloff radius = depth
      gl.uniform1f(RG.uReplace, 1.0);   // displace the REST surface, not the dented stream
    } else {
      gl.uniform1f(RG.uAmp, 0.0);
      gl.uniform1f(RG.uRad, 1.0);
    }
  }

  /* ================= frame loop (pure local math, 60 fps) ================= */
  function frame() {
    if (!ctxLive) return;          // paused while the GL context is lost; restore resumes
    requestAnimationFrame(frame);
    pollGamepad(1/60);
    if (!RG) return;
    var w = canvas.clientWidth, h = canvas.clientHeight;
    if (!w || !h) return;   // still hidden behind the start screen

    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var pw = Math.max(1, Math.round(w * dpr)), ph = Math.max(1, Math.round(h * dpr));

    /* The backing store is set EXACTLY ONCE (first visible size). Reassigning
       canvas.width/height recreates the WebGL context (fires CONTEXT_LOST_WEBGL);
       a safety net at the renderer top (oncontextlost/oncontextrestored) recovers
       from that single loss by rebuilding resources, so we never resize again.
       Thereafter only gl.viewport() tracks logical changes, which does NOT
       recreate the context. */
    if (!sizeInitialized) {
      canvas.width = pw; canvas.height = ph;
      sizeInitialized = true;
    }
    gl.viewport(0, 0, pw, ph);

    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
    camEye(eyeScratch);
    perspective(mProj, cam.fov, pw / ph, cam.near, cam.far);
    lookAt(mView, eyeScratch, cam.target, UP);
    mul(mVP, mProj, mView);

    /* grid first as a floor reference, but depth-write OFF so it never
       occludes the creature: the opaque body draws after and wins every
       pixel it covers (no depth tie at the floor), exactly like the engine's
       stencil-occluded scene grid. Grid lines read only on bare floor. */
    gl.useProgram(RG.gridProg);
    gl.uniformMatrix4fv(RG.gVP, false, mVP);
    gl.uniform3f(RG.gColor, 0x22 / 255, 0x30 / 255, 0x3a / 255);
    gl.depthMask(false);
    gl.bindVertexArray(RG.gridVao);
    if (!anatomyScene) gl.drawArrays(gl.LINES, 0, RG.gridCount);

    /* THE SHADOW: the creature flattened onto the floor (same planar
       projection the engine now uses), drawn under the body */
    if (RG.triCount > 0 && RG.verts) {
      gl.useProgram(RG.shadowProg);
      gl.uniformMatrix4fv(RG.sVP, false, mVP);
      gl.uniform1f(RG.sFloor, 0.0);
      gl.uniform1f(RG.sH0, 5.0);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA);
      gl.depthMask(false);
      gl.bindVertexArray(RG.shadowVao);
      gl.drawElements(gl.TRIANGLES, RG.triCount * 3, gl.UNSIGNED_INT, 0);
      gl.depthMask(true);
      gl.disable(gl.BLEND);
    }

    /* the creature, streamed as positions+normals+colors — never pictures */
    if (RG.triCount > 0 && RG.verts) {
      gl.useProgram(RG.prog);
      gl.uniformMatrix4fv(RG.uVP, false, mVP);
      gl.uniform3f(RG.uCam, eyeScratch[0], eyeScratch[1], eyeScratch[2]);
      pressKernelTick();               // W2: the visible dent rides the same draw
      gl.bindVertexArray(RG.vao);
      gl.drawElements(gl.TRIANGLES, RG.triCount * 3, gl.UNSIGNED_INT, 0);
    }
    gl.bindVertexArray(null);
  }

  /* ================= streaming ================= */
  async function loadTopology() {
    try {
      var res = await fetch(API.topology);
      if (!res.ok) throw new Error('http ' + res.status);
      var buf = await res.arrayBuffer();
      if (buf.byteLength < 4) throw new Error('short topology payload');
      var dv = new DataView(buf);                       // little-endian u32 count
      var n = dv.getUint32(0, true);
      if (buf.byteLength < 4 + n * 12) throw new Error('truncated topology payload');
      RG.triCount = n;
      RG.idx = new Uint32Array(buf, 4, n * 3).slice();  // local copy of the indices
      if (RG) {                                         // GL buffers when GL exists
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, RG.ibo);
        gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, n * 3 * 4, gl.STATIC_DRAW);
        gl.bufferSubData(gl.ELEMENT_ARRAY_BUFFER, 0, RG.idx);
      }
      pollVerts();
    } catch (err) {
      setLink('the world is silent — retrying…');
      setTimeout(loadTopology, 2000);
    }
  }

  var vertsBusy = false;
  async function pollVerts() {
    if (vertsBusy) return;
    vertsBusy = true;

    /* C3 — THE KERNEL STREAM. pollVerts asks for ?delta=1 (changed runs,
       [u32 start][u32 count][f32*9*count] under a 16-byte header) and
       applies them into the persistent Float32Array. Constraints: the
       page must NEVER freeze and NEVER show a torn frame — every frame
       is validated by an exact-length walk BEFORE one byte of state is
       touched, and any failed or suspicious frame costs one ?delta=key
       pull (a forced keyframe that also re-heads the seq chain), never
       a broken screen. The GL upload below is the pre-C3 path, byte
       for byte. This function is the ONLY page change; the chain seq
       lives on the function object because it must outlive one call. */
    if (pollVerts.kernelSeq === undefined) pollVerts.kernelSeq = null;

    /* the pre-C3 full-frame apply + GL upload, unchanged in behavior
       (meshPos is reused when the vertex count is unchanged — the delta
       path needs a persistent target anyway) */
    function uploadFrame(f, n) {
      RG.vertCount = n;
      var pos = (meshPos && meshPos.length === n * 3) ? meshPos : new Float32Array(n * 3);
      for (var vi = 0; vi < n; vi++) {
        pos[vi * 3] = f[vi * 9]; pos[vi * 3 + 1] = f[vi * 9 + 1];
        pos[vi * 3 + 2] = f[vi * 9 + 2];
      }
      meshPos = pos;
      if (!meshReady) {
        meshReady = true;
        if (curLesson()) syncTouchTarget();   // re-snap the standing lesson
      }
      if (RG) {
        if (!RG.verts || RG.verts.length !== n * 9) RG.verts = new Float32Array(n * 9);
        RG.verts.set(f);
        gl.bindBuffer(gl.ARRAY_BUFFER, RG.vbo);
        if (!RG.vboSized) {
          gl.bufferData(gl.ARRAY_BUFFER, RG.verts.byteLength, gl.DYNAMIC_DRAW);
          RG.vboSized = true;
        }
        gl.bufferSubData(gl.ARRAY_BUFFER, 0, RG.verts);
      }
    }

    /* legacy framing [u32 n][f32*9n] — the answer of a pre-C3 engine or
       of the front door with the query stripped */
    function decodeLegacy(buf) {
      if (buf.byteLength < 4) throw new Error('short verts payload');
      var n = new DataView(buf).getUint32(0, true);
      if (buf.byteLength < 4 + n * 36) throw new Error('truncated verts payload');
      return { f: new Float32Array(buf, 4, n * 9), n: n };
    }

    /* kernel framing: [u8 magic 0xD1][u8 flags][u16 rsvd]
                      [u32 n][u32 seq][u32 runs]
       flags 0 = keyframe (f32*9n payload at 16); flags 1 = runs.
       Returns null for a legacy frame; THROWS on any torn or
       out-of-range frame — validation completes before any state is
       touched (the C3 falsifier: a torn frame must keep the last
       full state on screen). */
    function decodeKernel(buf) {
      if (buf.byteLength < 4) throw new Error('short verts payload');
      var dv = new DataView(buf);
      if (dv.getUint8(0) !== 0xD1) return null;
      if (buf.byteLength < 16) throw new Error('short kernel frame');
      var flags = dv.getUint8(1);
      if (dv.getUint16(2, true) !== 0) throw new Error('bad kernel header');
      var n = dv.getUint32(4, true), seq = dv.getUint32(8, true);
      var runs = dv.getUint32(12, true);
      if (flags > 1) throw new Error('bad kernel flags');
      var plan = { flags: flags, n: n, seq: seq, runs: [] };
      if (flags === 0) {
        if (runs !== 0) throw new Error('keyframe with runs');
        if (buf.byteLength !== 16 + n * 36) throw new Error('truncated keyframe');
        return plan;
      }
      var off = 16;
      for (var r = 0; r < runs; r++) {
        if (off + 8 > buf.byteLength) throw new Error('truncated run header');
        var start = dv.getUint32(off, true), count = dv.getUint32(off + 4, true);
        off += 8;
        if (count === 0 || start + count > n) throw new Error('run out of range');
        if (off + count * 36 > buf.byteLength) throw new Error('truncated run body');
        plan.runs.push({ start: start, count: count, off: off });
        off += count * 36;
      }
      if (off !== buf.byteLength) throw new Error('trailing kernel bytes');
      return plan;
    }

    /* apply VALIDATED runs into the persistent arrays — no payload
       allocation; requires RG.verts already sized to plan.n (guaranteed:
       runs are only applied when plan.n === RG.vertCount) */
    function applyRuns(plan, buf) {
      var dv = new DataView(buf);
      for (var r = 0; r < plan.runs.length; r++) {
        var run = plan.runs[r];
        for (var vi = 0; vi < run.count; vi++) {
          var v = run.start + vi, s = run.off + vi * 36;
          for (var k = 0; k < 9; k++)
            RG.verts[v * 9 + k] = dv.getFloat32(s + k * 4, true);
          if (meshPos && meshPos.length === plan.n * 3) {
            meshPos[v * 3] = RG.verts[v * 9];
            meshPos[v * 3 + 1] = RG.verts[v * 9 + 1];
            meshPos[v * 3 + 2] = RG.verts[v * 9 + 2];
          }
        }
      }
      if (!meshPos || meshPos.length !== plan.n * 3) {
        meshPos = new Float32Array(plan.n * 3);
        for (var v2 = 0; v2 < plan.n; v2++) {
          meshPos[v2 * 3] = RG.verts[v2 * 9];
          meshPos[v2 * 3 + 1] = RG.verts[v2 * 9 + 1];
          meshPos[v2 * 3 + 2] = RG.verts[v2 * 9 + 2];
        }
      }
      gl.bindBuffer(gl.ARRAY_BUFFER, RG.vbo);
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, RG.verts);
    }

    /* the resync: one forced keyframe (?delta=key), applied whole or
       not at all; re-heads the seq chain */
    async function pullKey() {
      var res = await fetch(API.verts + '?delta=key');
      if (!res.ok) throw new Error('http ' + res.status);
      var buf = await res.arrayBuffer();
      var plan = decodeKernel(buf);
      if (plan === null || plan.flags !== 0) throw new Error('keyframe refused');
      uploadFrame(new Float32Array(buf, 16, plan.n * 9), plan.n);
      pollVerts.kernelSeq = plan.seq;
    }

    try {
      var res = await fetch(API.verts + '?delta=1');
      if (!res.ok) throw new Error('http ' + res.status);
      var buf = await res.arrayBuffer();
      var plan = decodeKernel(buf);              // throws when torn
      if (plan === null) {
        // legacy answer: old engine build, or the front door stripped
        // the query — decode as the pre-C3 page did
        var dec = decodeLegacy(buf);
        uploadFrame(dec.f, dec.n);
        pollVerts.kernelSeq = null;
      } else if (plan.flags === 0) {
        // keyframe in kernel framing: adopt whole
        uploadFrame(new Float32Array(buf, 16, plan.n * 9), plan.n);
        pollVerts.kernelSeq = plan.seq;
      } else if (pollVerts.kernelSeq === null ||
                 plan.seq !== ((pollVerts.kernelSeq + 1) >>> 0) ||
                 plan.n !== RG.vertCount) {
        // unchained, dropped poll (seq gap), or topology change:
        // NEVER apply runs onto unknown state — one resync pull
        await pullKey();
      } else {
        applyRuns(plan, buf);
        pollVerts.kernelSeq = plan.seq;
      }
      w2UpdateRest();               // W2: mirror the idle surface for the kernel
      setLink('');
      return true;
    } catch (err) {
      /* H7 FIX (D6): torn or unreachable -- the last full state stays on
         screen (never a partial frame) and the poll FAILS this beat. The
         old catch fired an IMMEDIATE ?delta=key resync here: under 429s
         that doubled the request rate with zero backoff and the page
         DDoSed its own shell (1362 errors / 17 min in the H5 dry-run).
         Now the failure just propagates to the poll loop, which backs
         off; the next successful delta that arrives unchained resyncs
         through the normal pullKey path above. */
      return false;
    } finally {
      vertsBusy = false;
    }
  }

  /* ================= state: the creature's blood + the lesson judge ================= */
  var stateBusy = false;
  async function pollState() {
    if (stateBusy) return;               // skipped, not failed
    stateBusy = true;
    try {
      var res = await fetch(API.state);
      if (!res.ok) throw new Error('http ' + res.status);
      var s = await res.json();
      nativeBodySurface = s.body_model === "JNT3_hierarchical";
      canvas.dataset.surfaceOwner = nativeBodySurface ? "native" : "legacy_preview";
      if (anatomyScene) return true;
      renderBlood(s);
      judgeState(s);
      renderJudgeDebug();     // runs on the setInterval poll, so the judge
                              // line stays live even with no WebGL frame
                              // loop (headless walkers depend on this)
      return true;
    } catch (err) {
      /* keep the last readout; the poll loop backs off (H7 D6) */
      return false;
    } finally {
      stateBusy = false;
    }
  }

  function fmt(x) {
    x = Number(x);
    if (!isFinite(x)) x = 0;
    return x.toFixed(3);
  }

  /* L1 BY-HAND FIX: the hand NAMES the part it is pressing. The page keeps
     the per-cell pressures it last rendered; when a held press lifts one
     cell clearly above where the press started, the hand line says the
     BODY PART (judge 2: "the four blood cells are never labeled"). */
  var lastCellsP = null;      // the P vector as of the last renderBlood
  var pressedCell = -1;       // the cell the live press has visibly woken
  var pressBaseP = null;      // the P vector when the live press landed
  var pressedNoteShown = false;  // the wrong-part hint fires once per press
  function pressingText(force, tail) {
    return 'pressing' + (pressedCell >= 0 ? ' the ' + cellPart(pressedCell) : '') +
      ' — ' + force + ' N' + (tail || '');
  }

  function renderBlood(s) {
    var cells = (s && s.cells) || [];
    if (!cells.length) { bloodEl.textContent = 'no cells reported.'; return; }
    var psNow = [];
    var html = '';
    for (var i = 0; i < cells.length; i++) {
      var c = cells[i];
      psNow.push(isFinite(Number(c.P)) ? Number(c.P) : 0);
      /* H7 FIX (D7): a zero-volume cell is the engine's garbage -- measured,
         cell4 read V=0.000000 with P=1622.780 MPa (and -0.009 MPa negatives
         elsewhere). The page used to print that number as if it were blood
         pressure; a buyer steering by it was being lied to. A cell with no
         water is shown as sealed solid, pressure dashes. */
      if (brokenCell(c)) {
        html += cellPart(i) + ' (cell ' + i + '): V=' + fmt(Number(c.V) || 0) +
          ' m3  P=---  sealed solid (no water)\n';
        continue;
      }
      var rawP = Number(c.P);
      if (!isFinite(rawP)) {
        html += cellPart(i) + ' (cell ' + i + '): V=' + fmt(Number(c.V)) + ' m3  P=---\n';
        continue;
      }
      var p = rawP;
      var awake = Math.abs(p) >= 2e5;
      html += cellPart(i) + ' (cell ' + i + '): V=' + fmt(c.V) + ' m3  P=' +
        (awake ? '<span class="awake">' : '') + fmt(p / 1e6) + (awake ? '</span>' : '') +
        ' MPa\n';
    }
    if (s.conserve_pct != null) {
      html += '\nconserve: ' + Number(s.conserve_pct).toFixed(2) + ' %';
    }
    /* RUPTURE_FAILURE: the blood panel names a burst cell so the player sees
       the physical consequence in the water readout, not only the verdict. */
    var lR = curLesson();
    if (lR && lessonState[lR.id] && lessonState[lR.id].ruptured) {
      html += '\n!! ' + cellPart(lessonState[lR.id].rupturedCell) +
        ' has RUPTURED — the creature went still.';
    }
    /* only numbers and our own span go in here — no external text */
    bloodEl.innerHTML = html;
    lastCellsP = psNow;
    /* the pressed-part readout: the first cell the live press lifts >= 20 kPa
       above where the press found it owns the hand line */
    if (holding && pressBaseP && psNow.length === pressBaseP.length) {
      var bestC = -1, bestD = 20000;
      for (var pi = 0; pi < psNow.length; pi++) {
        var d = psNow[pi] - pressBaseP[pi];
        if (d > bestD) { bestD = d; bestC = pi; }
      }
      if (bestC >= 0 && bestC !== pressedCell) {
        pressedCell = bestC;
        if (pressSource === 'space') setHand(pressingText(lastTouchForce, ' (space)'));
        else if (pressSource === 'gamepad') setHand(pressingText(lastTouchForce, ' (gamepad)'));
        else if (holding) setHand(pressingText(lastTouchForce));
      }
    }
  }

  function judgeState(s) {
    var l = curLesson();
    if (!l) return;
    /* W1 hold guard (SPEC §9): a lesson whose goal.type this page has not
       implemented HOLDS -- it can neither crash the judge nor pass. */
    if (KNOWN_GOAL_TYPES.indexOf(l.goal.type) < 0) return;
    var st = curState();
    syncRuptureUI();                 // RUPTURE_FAILURE: keep try-again in step
    if (st.passed) return;
    /* L1 BY-HAND FIX (SPEC §4's HINT_AFTER_MS, now real): when the GOAL
       phase stalls 25 s, the lesson's own hint speaks once. Both judges sat
       on "the creature waits." with the pack's hints never shown. */
    if (!st.goalMet && st.phase === 'goal' && !st.hintShown && l.hint &&
        Date.now() - lessonShownAt > 25000) {
      st.hintShown = true;
      setVerdict(l.hint, 'warn');
    }
    /* pose lessons (pose_reach AND pose_pair) judge on the POSTED intent
       (observePose), never on the poll */
    if (l.goal.type === 'pose_reach' || l.goal.type === 'pose_pair') return;
    var cells = (s && s.cells) || [];
    if (!cells.length) return;
    if (s.n_cells && cells.length < s.n_cells) return;   // W1: partial read -- hold

    var pa = Number(l.goal.threshold_pa) || 0;
    var cellWanted = l.goal.cell;
    // SIGNED (dyad fix 3): pressure_above means SQUEEZED — expansion
    // (negative P) must never pre-latch a goal, or stuck residuals
    // (e.g. -31.9 MPa held by a pose) count as "the player did it".
    var signedP = function (c) { return Number(c.P) || 0; };
    var peakHere = function (c) { return Math.abs(signedP(c)); };

    /* RUPTURE_FAILURE (SPEC new): while the hand STILL holds a press, if any
       real cell's gauge pressure has climbed past RUPTURE_PA the touched cell
       has burst — the lesson FAILS and this attempt is locked until recovery.
       A real physical consequence (the creature went still), not a soft miss:
       broken zero-volume cells are skipped so engine garbage never bursts it,
       and it only fires while holding, so pose/gravity lessons are untouched. */
    if (holding && !st.ruptured) {
      for (var ru = 0; ru < cells.length; ru++) {
        var rc = cells[ru];
        if (!brokenCell(rc) && signedP(rc) >= RUPTURE_PA) { st.ruptured = true; st.rupturedCell = ru; break; }
      }
    }
    if (st.ruptured) {
      setVerdict('the cell ruptured — the creature went still.', 'bad');
      syncRuptureUI();
      return;          // stop counting this attempt; locked until recovery
    }

    /* W4: the wake WHOOSH -- one per false->true crossing of a cell's wake
       bar (WOKEN_PA, squeeze only), memo'd per cell so a held press cannot
       re-trigger it on every poll; the memo resets when the cell falls
       back asleep, so a later wake whooshes again. The whoosh marks the
       CROSSING; cellWake keeps the goal-met LATCH.
       H9 AUDIO FIX (lesson-switch double-fire): the memo used to live on
       the LESSON state, and showLesson resets lesson state -- so switching
       lessons re-whooshed a cell the player's hand woke long before
       (live-measured 1 -> 2). The memo is WORLD-scoped now: one crossing,
       one whoosh, for the whole world, across every lesson switch. */
    var memo = worldWokeMemo;
    for (var wv = 0; wv < cells.length; wv++) {
      var wk = 'cell' + wv, wokeNow = !brokenCell(cells[wv]) &&
        signedP(cells[wv]) >= WOKEN_PA;
      if (wokeNow && !memo[wk]) { memo[wk] = true; snd('wakeWhoosh'); }
      else if (!wokeNow && memo[wk]) memo[wk] = false;
    }

    if (st.phase === 'goal' && !st.goalMet) {
      /* L1 BY-HAND FIX: the wrong-part coaching. A held press that visibly
         woke a cell the lesson did not ask for now SAYS so -- judge 2
         pressed a leg to 14.8 MPa and the page kept saying "the creature
         waits." with no hint that the shins were the wish. Once per press. */
      if (holding && pressedCell >= 0 && !pressedNoteShown &&
          (l.goal.type === 'pressure_above' || l.goal.type === 'pressure_isolation') &&
          l.goal.cell !== 'any') {
        var wanted = l.goal.cell;
        var quietCells = (l.goal.quiet_cells || []);
        if (pressedCell !== wanted) {
          pressedNoteShown = true;
          if (l.goal.type === 'pressure_isolation' && quietCells.indexOf(pressedCell) >= 0) {
            setVerdict('you are pressing the ' + cellPart(pressedCell) + ' — this lesson reads the ' +
              cellPart(wanted) + ' alone. let go and let the ' + cellPart(pressedCell) + ' heal first.', 'warn');
          } else if (l.goal.also &&
                     (pressedCell === l.goal.also.cell)) {
            /* a room the lesson DOES want: the pair note below owns this */
          } else {
            setVerdict('you are pressing the ' + cellPart(pressedCell) + ' — this lesson waits for the ' +
              cellPart(wanted) + '.', 'warn');
          }
        }
      }
      if (l.goal.type === 'pressure_isolation') {
        var tgt = Number(l.goal.threshold_pa) || 0;
        var quiet = (l.goal.quiet_cells || []).every(function (qc) {
          var c = cells[qc];
          // H7 (D7): a zero-volume cell is engine garbage, not a leak
          if (!c || brokenCell(c)) return true;
          return Math.abs(Number(c.P) || 0) < (Number(l.goal.quiet_max_pa) || 100);
        });
        var pc = cells[cellWanted];
        // H7 (D5): the target cell may only latch while the player's hand
        // is actually on the body (pressFresh) -- never on residual or
        // phantom pressure the lesson's input never caused.
        if (pc && !brokenCell(pc) && pressFresh() &&
            (Number(pc.P) || 0) >= tgt && quiet) st.goalMet = true;
      } else if (l.goal.type === 'cells_woken') {
        var woken = 0;
        for (var ci = 0; ci < cells.length; ci++)
          if (!brokenCell(cells[ci]) && pressFresh() &&
              (Number(cells[ci].P) || 0) >= 20000) woken++;
        if (woken >= (Number(l.goal.count) || 3)) st.goalMet = true;
      }
      if (l.goal.type === 'pressure_above' || l.goal.type === 'pressure_below') {
        var cap = Number(l.goal.max_force_n) || 0;
        // H7 FIX (D5): the force cap now demands a REAL recorded press.
        // It used to read `!lastTouchForce` as force-ok -- and the mouse
        // path never set lastTouchForce at all, so a lesson whose
        // qualifying press never happened passed on any cell spike.
        var forceOk = !cap || (lastTouchForce > 0 && lastTouchForce <= cap);
        // G2 (SPEC §5 cellCondition): each condition is judged at ITS OWN
        // threshold_pa. `woke` used to close over the MAIN threshold, so
        // the_whole_body's 'also' bar (shins 5000 Pa) was judged at the
        // torso's 15000 Pa -- a silently tripled goal.
        var woke = function (idx, thr) {
          var t = (thr === undefined) ? pa : thr;
          if (idx === 'any') return cells.some(function (c) {
            return !brokenCell(c) && signedP(c) >= t; });
          var c = cells[idx];
          return !!c && !brokenCell(c) && signedP(c) >= t;
        };
        if (!forceOk) {
          // L1 BY-HAND FIX (honest refusal, by-hand audit (d)): an
          // over-force press that DID wake the cell used to be refused in
          // silence -- the player never learned the hand was too strong.
          if (!st.forceNote && lastTouchForce > cap && woke(cellWanted, pa)) {
            st.forceNote = true;
            setVerdict('the ' + cellPart(cellWanted) + ' woke — but the hand pressed at ' +
              lastTouchForce + ' N. this lesson wants under ' + cap + ' N.', 'warn');
          }
          return;          // an over-force press can never latch a capped lesson
        }
        // H7 (D5): the crossing must happen under the hand (pressFresh) --
        // a goal earned by decay timing, injection, or a leftover phantom
        // press is not the lesson's input.
        if (!pressFresh()) return;
        if (l.goal.also) {             // two compartments, each latched over time
          if (woke(l.goal.cell)) st.primaryMet = true;
          var alsoThr = Number(l.goal.also.threshold_pa);   // G2: its own bar,
          if (!isFinite(alsoThr)) alsoThr = pa;             // G2: malformed falls to the main bar
          if (woke(l.goal.also.cell, alsoThr)) st.alsoMet = true;
          if (st.primaryMet && st.alsoMet) st.goalMet = true;
          /* L1 BY-HAND FIX: the old "one compartment is awake" note sat
             behind the goalMet flag, so it fired on the SAME poll the
             release verdict replaced it (dead code), and with ONE room
             awake the verdict kept saying "the creature waits." -- judge 2
             sat on that line with a leg at 14.8 MPa. Now each room, when
             it latches alone, names what is awake and what still waits. */
          else if (st.primaryMet && !st.pairNote) {
            st.pairNote = true;
            setVerdict(cellIs(l.goal.cell) + ' awake — the lesson still waits for the ' +
              cellPart(l.goal.also.cell) + '.', 'accent');
          } else if (st.alsoMet && !st.pairNote) {
            st.pairNote = true;
            setVerdict(cellIs(l.goal.also.cell) + ' awake — the lesson still waits for the ' +
              cellPart(l.goal.cell) + '.', 'accent');
          }
        } else if (woke(cellWanted)) {
          st.goalMet = true;
        }
      } else if (l.goal.type === 'gravity_on') {
        /* W1 (SPEC §10): settled = the page's own enable resolved AND the
           root has left its authored rest AND is no longer moving. root_y
           is exactly 0 at the authored rest, so neither condition can fire
           before the fall; measured settle ~9.5 mm (tools/gravity_test.py). */
        if (st.gravityArmed &&
            Math.abs(Number(s.root_vy) || 0) <= ROOT_VY_SETTLE &&
            Math.abs(Number(s.root_y) || 0) > ROOT_SETTLE_M) st.goalMet = true;
      } else if (l.goal.type === 'cells_woken') {
        /* W1 (SPEC §11): squeeze only (negative P never wakes), a sticky
           cumulative set of DISTINCT cell indices; completes at g.count. */
        for (var wi = 0; wi < cells.length; wi++)
          if (signedP(cells[wi]) >= WOKEN_PA) st.wokenSet[wi] = true;
        if (Object.keys(st.wokenSet).length >= (Number(l.goal.count) || 0))
          st.goalMet = true;
      }
      if (st.goalMet) {
        snd('cellWake');
        if (l.then_release) {
          st.phase = 'release';
          setVerdict('the goal is met — now LET GO, and let the body heal.', 'accent');
        } else {
          st.passed = true;
          snd('passed');
          setVerdict(passLine(l, 'the lesson is yours.'), 'good');
        }
      }
    } else if (st.phase === 'release' && st.goalMet && !st.passed) {
      // THE RELEASE (LESSON_JUDGE_SPEC §4): pass on the first poll where
      // every cell is calm. A duplicated empty branch used to swallow this
      // one, so the calm check was dead code and no release lesson could
      // ever pass — the phases latched, then sat in release forever.
      // H7 (D1/D7): a zero-volume cell is the engine's garbage, not water
      // waiting to heal -- measured, cell4 sat at V=0 with P=1.62 GPa and
      // blocked the calm check forever (the walker's the_heavy_hand and
      // the_graduation FAILed as phase=release goalMet=true). Broken
      // cells are skipped; the display calls them "sealed solid".
      var calm = cells.every(function (c) {
        return brokenCell(c) || peakHere(c) < 1000; });
      if (calm) {
        st.passed = true;
        snd('healShimmer');   // W4: the release-phase heal completed -- the quiet reward
        snd('passed');
        setVerdict(passLine(l, 'you felt the water. it was always there.'), 'good');
      }
    }
  }

  /* the judge's own line: one honest string a headless walker can read.
     Lives on pollState's timer (never inside the WebGL frame loop —
     headless Chrome does not run that loop, and the line went dead).
     H7 FIX (D7, H5 dry-run S8): internal telemetry ("judge: phase=
     ... touchTarget=...") is dev jargon in a buyer's face -- it renders
     ONLY with ?debug=1 in the URL now; walkers and probes pass it,
     players never see it. The format itself never changes. */
  function debugOn() { return window.location.search.indexOf('debug=1') >= 0; }
  function renderJudgeDebug() {
    var dbg = $('judge-debug');
    if (!dbg) return;
    if (!debugOn()) { dbg.textContent = ''; return; }
    var l = curLesson();
    if (!l) { dbg.textContent = 'no lesson'; return; }
    var st = curState();
    var extra = '';
    // W1: the new latches, visible (the walker regex reads the first four
    // fields, so the prefix format never changes)
    if (l.goal.type === 'cells_woken')
      extra += ' woken=' + Object.keys(st.wokenSet || {}).length + '/' +
               (Number(l.goal.count) || 0);
    if (l.goal.type === 'gravity_on') extra += ' armed=' + !!(st.gravityArmed);
    if (l.goal.type === 'pose_pair') {
      var names = [], i;
      for (i = 0; l.goal.joints && i < l.goal.joints.length; i++)
        names.push(l.goal.joints[i].joint + '=' +
                   !!(st.pairOk || {})[l.goal.joints[i].joint]);
      extra += ' pair[' + names.join(' ') + ']';
    }
    dbg.textContent = 'judge: ' + l.id + ' phase=' + st.phase +
      ' goalMet=' + st.goalMet + ' passed=' + st.passed +
      ' touchTarget=' + (touchTarget ? 'set' : 'null') +
      ' lastTouchForce=' + lastTouchForce +
      ' holding=' + holding + extra;
    /* H9 AUDIO FIX: the sound lane's failures ride the same debug line
       (snd() itself never console-spits -- see snd). Only with ?debug=1,
       which this whole line already is behind. */
    var fails = window.__sndFailures || {}, fk = [], fk2;
    for (fk2 in fails) if (fails[fk2] > 0) fk.push(fk2 + 'x' + fails[fk2]);
    if (fk.length) dbg.textContent += '\nsnd-fail: ' + fk.join(' ');
  }

  /* ================= KEYBOARD + GAMEPAD (AI + accessibility) =================
     Keyboard (play screen): 1-9,0 lessons · [ ] prev/next · SPACE hold = press
     the lesson's target · - / = force down/up · P post pose wishes (pose
     lessons) · R stand at rest · S save · ESC let go.
     Gamepad: left stick = orbit · A (held) = press the lesson target ·
     B = release · LB/RB = lesson prev/next · RT analog = force while A. */
  var touchTarget = null;       // world point the keyboard/gamepad presses
  var touchTargetList = [];     // lessons may cycle several targets
  var touchTargetIdx = 0;
  /* THE TOUCH KERNEL TRUTH (measured 2026-09-13, engine membrane_tick):
     the press is a 3 cm Gaussian around the world point (delta = F/(4*pi*
     sigma), falloff press_r0 = 0.03 m). A target between mesh vertices
     presses NOTHING — the pack's belly point's nearest skin vertex is
     0.355 m away and the POST answers ok:true with zero pressure in every
     cell (a silent lie). The same spot pressed AT its nearest vertex reads
     2.14 MPa on the torso at 50 kN. So every touch target is snapped to
     the nearest mesh vertex: the kernel's response is maximal exactly
     there, the compartment is unchanged, and no threshold moves. */
  var meshPos = null;           // skin vertex positions, independent of WebGL
  var meshReady = false;
  function snapToVertex(pt) {
    if (!meshPos || !pt) return pt;
    var best = -1, bd = Infinity;
    for (var i = 0, n = meshPos.length / 3; i < n; i++) {
      var dx = meshPos[i * 3] - pt[0], dy = meshPos[i * 3 + 1] - pt[1],
          dz = meshPos[i * 3 + 2] - pt[2];
      var d2 = dx * dx + dy * dy + dz * dz;
      if (d2 < bd) { bd = d2; best = i; }
    }
    if (best < 0) return pt;
    return [meshPos[best * 3], meshPos[best * 3 + 1], meshPos[best * 3 + 2]];
  }
  function syncTouchTarget() {
    var l = curLesson();
    touchTargetList = (l && l.touch_targets && l.touch_targets.length)
      ? l.touch_targets : ((l && l.touch_target) ? [l.touch_target] : []);
    touchTargetList = touchTargetList.map(snapToVertex);
    touchTargetIdx = 0;
    touchTarget = touchTargetList[0] || null;
  }
  /* H7: each fresh SPACE press takes the NEXT target in the lesson's
     rotation (whole_body: belly -> shin; graduation: five spots). The
     advance happens AFTER the press is initiated, so the first press is
     always touch_targets[0]; the old cycle ran while HOLDING and then
     re-posted the moved target on the same keydown. */
  function cycleTouchTargetAfter() {
    if (touchTargetList.length > 1) {
      touchTargetIdx = (touchTargetIdx + 1) % touchTargetList.length;
      touchTarget = touchTargetList[touchTargetIdx];
    }
  }
  window.addEventListener('keydown', function (e) {
    if (anatomyScene || !$('screen-play').classList.contains('on') || E4overlayOpen()) return;   // E4: an overlay owns the keyboard while up
    /* H7 (D4): only TEXT typing owns the keyboard. The old guard skipped
       every INPUT, so once the force slider had focus, SPACE / - / = died
       and the creature went untouched; the slider keeps its native arrows
       because none of the page's handlers want them. */
    var tgt = e.target;
    if (tgt && (tgt.tagName === 'TEXTAREA' ||
        (tgt.tagName === 'INPUT' && tgt.type !== 'range'))) return;
    var k = e.key;
    /* L1 BY-HAND FIX: the pack has TEN lessons and the keyboard mapped
       only 1-5 (judge 2: "only the keyboard 1-5 works"). 1-9 and 0 (the
       tenth) reach every lesson; [ ] and the arrows cover the rest. */
    if ((k >= '1' && k <= '9') || k === '0') {
      showLesson(k === '0' ? 9 : (+k - 1)); e.preventDefault(); return;
    }
    if (k === '[') { showLesson(lessonIdx - 1); e.preventDefault(); return; }
    if (k === ']') { showLesson(lessonIdx + 1); e.preventDefault(); return; }
    if (k === ' ') {
      e.preventDefault();                // also stops a focused button firing
      if (e.repeat) return;              // hold = one press, not a machine gun
      if (!touchTarget) return;
      spaceClearOnLand = false;          // a fresh press may outlive its keyup: end then
      pressSpaceTarget();                // the hand presses the rotation's CURRENT target
      cycleTouchTargetAfter();           // and the NEXT press takes the next one
      return;
    }
    if (k === 'Escape') { clearTouch(); return; }
    if (k === 'p') {                     // post every pending wish at its slider value
      var posts = document.querySelectorAll('#pose-btn-wrap .pose-post');
      for (var pk = 0; pk < posts.length; pk++) {
        var prow = posts[pk].closest('.pose-row');
        if (prow && prow.classList.contains('latched')) continue;
        posts[pk].click();
      }
      return;
    }
    if (k === 'r') { (function () { $('rest-btn').click(); })(); return; }
    if (k === 's') { $('save-btn').click(); return; }
    if (k === '-') { forceEl.value = Math.max(500, +forceEl.value - 2000); forceEl.dispatchEvent(new Event('input')); return; }
    if (k === '=' || k === '+') { forceEl.value = Math.min(50000, +forceEl.value + 2000); forceEl.dispatchEvent(new Event('input')); return; }
  });
  /* H7 FIX (D3): SPACE keyup ENDS the press. The old page had no keyup
     handler at all -- a scripted keydown held the world's hand forever
     (the walker's presses only ever ended through Escape), and a held
     press leaked its pressures into the next lesson. */
  window.addEventListener('keyup', function (e) {
    if (e.key !== ' ' || pressSource !== 'space') return;
    if (spacePressInFlight) spaceClearOnLand = true;   // end the moment it lands
    else if (holding) clearTouch();
  });

  var gamepadWasA = false, gamepadRB = false, gamepadLB = false;
  function pollGamepad(dtSec) {
    if (!navigator.getGamepads) return;
    var pads = navigator.getGamepads();
    var gp = null;
    for (var i = 0; i < pads.length; i++) if (pads[i]) { gp = pads[i]; break; }
    if (!gp) return;
    var ax = gp.axes || [];
    var dead = function (v) { return Math.abs(v) < 0.15 ? 0 : v; };
    var lx = dead(ax[0] || 0), ly = dead(ax[1] || 0);
    if (lx || ly) {                       // left stick = orbit (local, free)
      cam.theta -= lx * 2.2 * dtSec;
      cam.phi = Math.max(-1.45, Math.min(1.45, cam.phi - ly * 1.6 * dtSec));
    }
    var rt = gp.buttons[7] ? gp.buttons[7].value : 0;   // right trigger = force
    var aHeld = gp.buttons[0] && gp.buttons[0].pressed;
    if (aHeld && touchTarget) {           // A held: press the lesson target
      var f = 500 + rt * 49500;
      if (!holding || Math.abs(f - lastTouchForce) > 800) {
        postJSON(API.touchHit, { hit: touchTarget, force_n: f });
        holding = true; $('letgo-btn').classList.add('hot');
        pressSource = 'gamepad';          // H7: whose press is this (keyup/up fairness)
        lastTouchForce = Math.round(f); lastTouchAt = Date.now();
        pressKernelStart(touchTarget, f); // W2: the gamepad hand shows the dent too
        setHand(pressingText(Math.round(f), ' (gamepad)'));
        snd('press', f, touchTarget);
      }
    } else if (holding && !aHeld && gamepadWasA) {
      clearTouch();
    }
    gamepadWasA = aHeld;
    var rb = gp.buttons[5] && gp.buttons[5].pressed;
    if (rb && !gamepadRB) showLesson(lessonIdx + 1);
    gamepadRB = rb;
    var lb2 = gp.buttons[4] && gp.buttons[4].pressed;
    if (lb2 && !gamepadLB) showLesson(lessonIdx - 1);
    gamepadLB = lb2;
  }

  /* ================= picking: browser-side ray-cast -> world-space hit ================= */
  function sub3(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function cross3(a, b) {
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
  }
  function norm3(a) {
    var l = Math.hypot(a[0], a[1], a[2]) || 1;
    return [a[0] / l, a[1] / l, a[2] / l];
  }

  /* Moller-Trumbore; P is the interleaved array, b* are per-vertex float offsets */
  function rayTri(ox, oy, oz, dx, dy, dz, P, b0, b1, b2) {
    var ax = P[b0], ay = P[b0 + 1], az = P[b0 + 2];
    var e1x = P[b1] - ax, e1y = P[b1 + 1] - ay, e1z = P[b1 + 2] - az;
    var e2x = P[b2] - ax, e2y = P[b2 + 1] - ay, e2z = P[b2 + 2] - az;
    var px = dy * e2z - dz * e2y, py = dz * e2x - dx * e2z, pz = dx * e2y - dy * e2x;
    var det = e1x * px + e1y * py + e1z * pz;
    if (det > -1e-8 && det < 1e-8) return -1;
    var inv = 1 / det;
    var sx = ox - ax, sy = oy - ay, sz = oz - az;
    var u = (sx * px + sy * py + sz * pz) * inv;
    if (u < 0 || u > 1) return -1;
    var qx = sy * e1z - sz * e1y, qy = sz * e1x - sx * e1z, qz = sx * e1y - sy * e1x;
    var v = (dx * qx + dy * qy + dz * qz) * inv;
    if (v < 0 || u + v > 1) return -1;
    var t = (e2x * qx + e2y * qy + e2z * qz) * inv;
    return t > 1e-6 ? t : -1;
  }

  /* unproject the click through the same orbit camera: basis rays, no matrix inverse */
  function pickWorld(clientX, clientY) {
    if (!RG || !RG.verts || !RG.idx || RG.triCount <= 0) return null;
    var rect = canvas.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return null;
    var ndcX = ((clientX - rect.left) / rect.width) * 2 - 1;
    var ndcY = 1 - ((clientY - rect.top) / rect.height) * 2;
    var eye = camEye([0, 0, 0]);
    var fwd = norm3(sub3(cam.target, eye));
    var right = norm3(cross3(fwd, UP));
    var upv = cross3(right, fwd);
    var tanF = Math.tan(cam.fov / 2);
    var aspect = rect.width / rect.height;
    var kx = ndcX * tanF * aspect, ky = ndcY * tanF;
    var dir = norm3([
      fwd[0] + right[0] * kx + upv[0] * ky,
      fwd[1] + right[1] * kx + upv[1] * ky,
      fwd[2] + right[2] * kx + upv[2] * ky
    ]);
    var P = RG.verts, idx = RG.idx;
    var best = -1;
    for (var i = 0; i < RG.triCount; i++) {
      var b0 = idx[i * 3] * 9, b1 = idx[i * 3 + 1] * 9, b2 = idx[i * 3 + 2] * 9;
      var t = rayTri(eye[0], eye[1], eye[2], dir[0], dir[1], dir[2], P, b0, b1, b2);
      if (t > 0 && (best < 0 || t < best)) best = t;
    }
    if (best < 0) return null;
    return [eye[0] + dir[0] * best, eye[1] + dir[1] * best, eye[2] + dir[2] * best];
  }

  /* L1 BY-HAND FIX: the ~14 px grace around a missed click. Projects every
     skin vertex with the same camera the pick used; candidates within
     PICK_NEAR_PX of the cursor are taken nearest-to-camera (the visible
     surface), and only when the cursor is within PICK_NEAR_M of the
     surface at all -- a click on open water stays water. */
  var PICK_NEAR_PX = 14;
  var PICK_NEAR_M = 0.75;
  function pickNearMiss(cx, cy) {
    if (!meshPos || !RG || !RG.idx || RG.triCount <= 0) return null;
    var rect = canvas.getBoundingClientRect();
    if (rect.width < 1 || rect.height < 1) return null;
    var eye = camEye([0, 0, 0]);
    var fwd = norm3(sub3(cam.target, eye));
    var right = norm3(cross3(fwd, UP));
    var upv = cross3(right, fwd);
    var tanF = Math.tan(cam.fov / 2);
    var aspect = rect.width / rect.height;
    var bestV = -1, bestPx = Infinity, bestDepth = Infinity;
    for (var i = 0, n = meshPos.length / 3; i < n; i++) {
      var dx = meshPos[i * 3] - eye[0], dy = meshPos[i * 3 + 1] - eye[1],
          dz = meshPos[i * 3 + 2] - eye[2];
      var depth = dx * fwd[0] + dy * fwd[1] + dz * fwd[2];
      if (depth <= 0.1) continue;
      var px = (dx * right[0] + dy * right[1] + dz * right[2]) / (depth * tanF * aspect);
      var py = (dx * upv[0] + dy * upv[1] + dz * upv[2]) / (depth * tanF);
      var sx = rect.left + (px + 1) / 2 * rect.width;
      var sy = rect.top + (1 - py) / 2 * rect.height;
      var dd = Math.hypot(sx - cx, sy - cy);
      if (dd > PICK_NEAR_PX) continue;
      // lexicographic pick: clearly-closer pixel wins; inside a 1 px band
      // the vertex nearest the camera wins (the surface the player sees)
      if (bestV < 0 || dd < bestPx - 0.5 ||
          (dd <= bestPx + 0.5 && depth < bestDepth)) {
        bestPx = bestV < 0 ? dd : Math.min(bestPx, dd);
        bestDepth = depth;
        bestV = i;
      }
    }
    if (bestV < 0) return null;
    // the world distance from the RAY decides "water or flesh": reject a
    // candidate whose perpendicular distance from the cursor ray is huge
    var ox = eye[0], oy = eye[1], oz = eye[2];
    var wx = meshPos[bestV * 3], wy = meshPos[bestV * 3 + 1], wz = meshPos[bestV * 3 + 2];
    var rx = wx - ox, ry = wy - oy, rz = wz - oz;
    var t = rx * fwd[0] + ry * fwd[1] + rz * fwd[2];
    var px2 = rx - fwd[0] * t, py2 = ry - fwd[1] * t, pz2 = rz - fwd[2] * t;
    if (Math.hypot(px2, py2, pz2) > PICK_NEAR_M) return null;
    return [wx, wy, wz];
  }

  /* H7 (D2): a touch post must ANSWER. The old code read only the HTTP
     ok flag -- a rate-limit 429 or a network blip silently dropped the
     press (the H5 dry-run's "presses die after the first": 52x429 burst,
     holding stayed false, no retry, no report), and an engine refusal
     came back 200 {ok:false} and was still treated as a press (the
     phantom). postTouchRetry rides the answer through backoff + jitter
     and resolves to the response BODY; null means the retries are spent. */
  function sleepTouch(ms) {
    return new Promise(function (r) { setTimeout(r, ms); });
  }
  async function postTouchRetry(payload) {
    for (var attempt = 0; attempt < 3; attempt++) {
      if (attempt) await sleepTouch(400 * attempt * (0.7 + 0.6 * Math.random()));
      try {
        var res = await fetch(API.touchHit, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (res.status === 429 || res.status >= 500) continue;   // retryable
        var j = null;
        try { j = await res.json(); } catch (err2) { j = null; }
        return res.ok ? j : { ok: false, error: (j && j.error) || ('http ' + res.status) };
      } catch (err) { /* network silence: retry */ }
    }
    return null;
  }
  /* H7: whose press is live -- 'mouse' | 'space' | 'gamepad' | null -- so
     each modality's OWN release ends it (D3). */
  var pressSource = null;

  function applyTouch(body, force, hitHint) {
    if (body && body.ok === true) {
      holding = true;
      lastTouchForce = force;             // the judge's force cap sees every path now
      lastTouchAt = Date.now();           // the judge's "under the hand" window
      pressedCell = -1;                   // a new press: name the part afresh
      pressedNoteShown = false;
      pressBaseP = lastCellsP ? lastCellsP.slice() : null;
      if (hitHint) pressKernelStart(hitHint, force);   // W2: the hand shows the dent
      $('letgo-btn').classList.add('hot');
      setHand(pressingText(force));
      snd('press', force, hitHint);
      return true;
    }
    setHand((body && body.error) || waterMissText());
    return false;
  }

  /* L1 BY-HAND FIX (judge 2's stall 6: "'you touched only water.' shown
     while visibly touching a limb, cryptic"): a miss now says WHY and what
     to aim for -- the current lesson's own target part. */
  function waterMissText() {
    var l = curLesson();
    var aim = null;
    if (l && (l.goal.type === 'pressure_above' || l.goal.type === 'pressure_isolation')) {
      if (l.goal.cell === 'any') aim = 'any part of the creature';
      else if (!l.goal.also) aim = 'the ' + cellPart(l.goal.cell);
      else aim = (touchTargetIdx === 0) ? 'the ' + cellPart(l.goal.cell)
                                        : 'the ' + cellPart(l.goal.also.cell);
    }
    return 'your hand touched only water — nothing of the creature. aim for ' +
      (aim || "the creature's body") + ', then hold.';
  }

  async function tryTouch(cx, cy) {
    if (anatomyScene) return false;
    if (holding) return false;            // one press at a time
    var force = Number(forceEl.value);
    // H16 TOUCH-SIDE FIX: the click's contact enters through the surface
    // the player SEES. The old path posted this page's orbit camera +
    // click pixel and let the engine's pick_cam resolve the hit -- but
    // the engine rebuilds the eye with a Z-sign flip vs this page's
    // camEye (engine.cpp pick_cam: target.z - r*c*cos(theta) vs the
    // page's target.z + r*cos(phi)*cos(theta)), so its ray cast from
    // BEHIND the body: measured live, a click on the seen torso dented
    // the BLIND half 2.65 cm and the engine's resolved hit sat ~9 m down
    // the mirrored ray (H16_TOUCH_SIDE/falsifier_before.json, 0/7 rows on
    // the seen side). The page already owns a correct first-hit raycast:
    // pickWorld over RG.verts -- the same Float32Array the renderer
    // uploads on every stream poll (the delta path writes it in place;
    // there is no stale copy). So the press now goes out in the engine's
    // ready-world-point form {"hit":[x,y,z],force_n} (touch_press_at),
    // snapped to the nearest mesh vertex like every touch target (the
    // kernel's 3 cm Gaussian responds maximally exactly at a vertex).
    // ONE path, posted once; the camera convention is this page's own,
    // end to end. A ray that misses the skin (sky) touches only water,
    // exactly as the engine's miss answer used to say.
    var hit = pickWorld(cx, cy);
    // L1 BY-HAND FIX (the click rail's ZERO tolerance): the engine's touch
    // is a 3 cm Gaussian in the world, but the page's pick demanded the
    // pixel-exact first hit -- measured in the by-hand audit, a foot is
    // ~12 px wide at the default camera and a human's leg/foot clicks
    // missed the skin entirely ("you touched only water." while touching a
    // leg; judge 2 found one leg hot-zone "by luck -- 10 px mattered").
    // A miss now looks ~14 px around the cursor for the nearest mesh
    // vertex (nearest to the camera wins -- the surface the player SEES),
    // with a hard world cap so open sky far from the body still misses.
    if (!hit) hit = pickNearMiss(cx, cy);
    if (!hit) {
      setHand(waterMissText());
      return false;
    }
    hit = snapToVertex(hit);
    mousePressInFlight = true;
    var body = await postTouchRetry({ hit: hit, force_n: force });
    mousePressInFlight = false;
    if (body === null) {
      setHand('the world is busy — the press did not land. try again.');
      return false;
    }
    var landed = applyTouch(body, force, hit);   // the page's own hit names the region
    if (landed && mouseClearOnLand) clearTouch();     // the pointer ended mid-POST: end at once
    return landed;
  }

  /* H7: in-flight races. A press POST can still be in the air when its
     pointer or SPACE key ends (retry backoff makes seconds-long posts
     possible). Without these flags the press would land AFTER the
     release and phantom-stick -- exactly the H5 S1 class. */
  var mousePressInFlight = false, mouseClearOnLand = false;
  var spacePressInFlight = false, spaceClearOnLand = false;

  async function pressSpaceTarget() {
    if (holding || !touchTarget) return;
    var force = Number(forceEl.value);
    spacePressInFlight = true;
    var body = await postTouchRetry({ hit: touchTarget, force_n: force });
    spacePressInFlight = false;
    if (body === null) {
      setHand('the world is busy — the press did not land. try again.');
      return;
    }
    if (applyTouch(body, force, touchTarget)) {
      setHand(pressingText(force, ' (space)'));
      pressSource = 'space';
      if (spaceClearOnLand) { clearTouch(); return; }
    }
  }

  /* H7 (D3): the tap pulse. A quick tap's press outlives the pointer by
     ~900 ms -- long enough for the engine to apply the dent and the judge
     to see it -- then the hand opens by itself. A held press ends the
     moment its pointer ends. touchPulseTimer is cancelled by any new
     press, clearTouch, or a lesson switch. */
  var touchPulseTimer = null;
  function armTapPulse() {
    if (touchPulseTimer) clearTimeout(touchPulseTimer);
    setHand(handEl.textContent + ' (tap)');
    touchPulseTimer = setTimeout(function () {
      touchPulseTimer = null;
      clearTouch();
    }, 900);
  }

  function clearTouch() {
    if (touchPulseTimer) { clearTimeout(touchPulseTimer); touchPulseTimer = null; }
    if (!holding) return;
    holding = false;
    pressSource = null;
    pressKernelRelease();               // W2: the dent decays with tau, not with a snap
    $('letgo-btn').classList.remove('hot');
    setHand('hand open');
    /* H9 AUDIO FIX (ship-blocker 1): the press voice ENDS when the hand
       opens. pressEnd had ZERO call sites since W4 shipped (grep 0) --
       the first press started a tone that never stopped for the whole
       session and every release was mute (H9's live run: pressVActive
       still true after ESC). clearTouch is the single release funnel --
       ESC, let-go, rest, pointerup, pointercancel, blur, tab-hide, the
       tap pulse, the lesson switch -- so one call here covers them all.
       Fires only past the !holding guard: no press, no voice, no end. */
    snd('pressEnd');
    clearTouchSend();
  }
  /* H10-WALKER FIX (the sticky phantom): the release used to be ONE
     fire-and-forget POST -- a 429'd touch_clear was dropped without
     retry and the engine kept pressing a press the page believed over
     (measured live: exactly 1 clear call during release under a 429, no
     retry, no report). The clear now rides the same backoff as the
     press; the engine's clear is idempotent, so a retried release is
     free. Retries spent -> the link line says the release did not land. */
  async function clearTouchSend() {
    for (var attempt = 0; attempt < 3; attempt++) {
      if (attempt) await sleepTouch(400 * attempt * (0.7 + 0.6 * Math.random()));
      try {
        var res = await fetch(API.touchClear, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: '{}' });
        if (res.status === 429 || res.status >= 500) continue;
        return;                       // the world took the release
      } catch (err) { /* network: retry */ }
    }
    setLink('the world is busy — the release did not land; touch again to re-send.');
  }

  /* ================= input: click vs orbit vs zoom =================
     H7 MODEL (D2/D3): the hand is DOWN while the pointer is down.
     pointerdown (still 130 ms) starts the press; moving past 6 px turns
     the gesture into an orbit and ends the press; pointerup ends a HELD
     press immediately and lets a TAP's press pulse (~900 ms); pointer
     cancel, window blur, and tab hide all end the press. The old model
     started the press at pointerUP and had no keyup/blur handling at
     all, so every release left the HUD "pressing" (the phantom press,
     3/3 in the H5 dry-run) and half of a player's clicks did nothing. */
  var pressed = false, orbiting = false, downX = 0, downY = 0, lastX = 0, lastY = 0,
      downT = 0, touchArmTimer = null;

  canvas.addEventListener('pointerdown', function (e) {
    if (e.button !== 0 || pressed) return;
    pressed = true;
    orbiting = false;
    downX = lastX = e.clientX;
    downY = lastY = e.clientY;
    downT = Date.now();
    mousePressInFlight = false;          // a fresh gesture owns the race flags
    mouseClearOnLand = false;
    if (touchPulseTimer) { clearTimeout(touchPulseTimer); touchPulseTimer = null; }  // the hand stays on
    try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
    // the stillness guard: a press only ARMOS after 130 ms in one place,
    // so an orbit drag never dents the body on its way past
    if (touchArmTimer) clearTimeout(touchArmTimer);
    touchArmTimer = setTimeout(function () {
      touchArmTimer = null;
      if (pressed && !orbiting && !holding) {
        pressSource = 'mouse';
        tryTouch(downX, downY);
      }
    }, 130);
  });

  window.addEventListener('pointermove', function (e) {
    if (!pressed) return;
    var dx = e.clientX - lastX, dy = e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    if (!orbiting) {
      if (Math.hypot(e.clientX - downX, e.clientY - downY) <= 6) return;
      orbiting = true;                       // past 6 px this gesture is an orbit
      canvas.classList.add('dragging');
      if (touchArmTimer) { clearTimeout(touchArmTimer); touchArmTimer = null; }
      if (holding && pressSource === 'mouse') clearTouch();   // a drag opens the hand
    }
    cam.theta -= dx * 0.005;
    cam.phi = Math.max(-1.45, Math.min(1.45, cam.phi - dy * 0.003));
  });

  function endPress() {
    if (!pressed) return;
    pressed = false;
    canvas.classList.remove('dragging');
    var pending = !!touchArmTimer;
    if (touchArmTimer) { clearTimeout(touchArmTimer); touchArmTimer = null; }
    // the press POST is still in the air: end the press the moment it lands
    if (mousePressInFlight) { mouseClearOnLand = true; return; }
    // a faster-than-the-arm-guard still click is still a touch: fire it now
    if (pending && !orbiting && !holding) {
      pressSource = 'mouse';
      tryTouch(downX, downY).then(function (landed) {
        if (landed && Date.now() - downT < 250) armTapPulse();
      });
      return;
    }
    if (!holding || pressSource !== 'mouse') return;
    if (Date.now() - downT < 250) {
      armTapPulse();                         // a tap's press pulses, then opens
    } else {
      clearTouch();                          // mouseup ENDS a held press
    }
  }
  window.addEventListener('pointerup', function () { endPress(); });
  window.addEventListener('pointercancel', function () {
    pressed = false;
    canvas.classList.remove('dragging');
    if (touchArmTimer) { clearTimeout(touchArmTimer); touchArmTimer = null; }
    if (mousePressInFlight) mouseClearOnLand = true;
    else if (holding && pressSource === 'mouse') clearTouch();
  });
  /* H7 (D3): losing the window ends the press -- alt-tab mid-hold must
     never leave a phantom hand on the body (H5's S1). */
  window.addEventListener('blur', function () {
    pressed = false;
    canvas.classList.remove('dragging');
    if (touchArmTimer) { clearTimeout(touchArmTimer); touchArmTimer = null; }
    if (mousePressInFlight) mouseClearOnLand = true;
    else clearTouch();
  });
  document.addEventListener('visibilitychange', function () {
    if (document.hidden) {
      pressed = false;
      canvas.classList.remove('dragging');
      if (touchArmTimer) { clearTimeout(touchArmTimer); touchArmTimer = null; }
      if (mousePressInFlight) mouseClearOnLand = true;
      else clearTouch();
    }
  });

  /* wheel: pure local zoom, zero network */
  canvas.addEventListener('wheel', function (e) {
    e.preventDefault();
    cam.r *= Math.exp(e.deltaY * 0.001);
    cam.r = Math.max(anatomyScene ? .08 : 3, Math.min(60, cam.r));
  }, { passive: false });

  /* ================= hand, save, screens ================= */
  forceEl.addEventListener('input', function () {
    forceLabel.textContent = forceEl.value + ' N';
    if (holding) {
      setHand(pressingText(forceEl.value));
      snd('press', Number(forceEl.value));   // W4: the held voice follows the force live (press() never stacks)
    }
  });

  $('letgo-btn').addEventListener('click', clearTouch);
  /* RUPTURE_FAILURE: 'try again' — recover the locked attempt and re-attempt
     the SAME lesson. */
  $('try-again-btn').addEventListener('click', retryLesson);
  /* restart this lesson — reset only the current lesson's judge state, keep
     progress; recovery is a trimmed startLesson for one lesson. */
  $('restart-lesson-btn').addEventListener('click', function () {
    var l = curLesson();
    if (!l) return;
    clearTouch();
    showLesson(lessonIdx);   // resets this lesson's judge (and hides try-again)
    setVerdict('this lesson restarted — the creature waits.', '');
  });
  /* start over — destructive: clears THIS player's saved progress file, then
     reloads fresh. Guarded by confirm() so a stray click cannot wipe a save. */
  $('start-over-btn').addEventListener('click', async function () {
    if (!confirm('Start over? This erases ' + playerName + '\'s saved lesson progress on this device. You can still press \'save progress\' afterwards.')) return;
    try {
      await fetch(API.progress + '?name=' + encodeURIComponent(playerName) + '&_erase=1', { method: 'DELETE' });
    } catch (err) { /* a missing file is already fresh */ }
    lessonsKnown = {};
    for (var id in lessonState) delete lessonState[id];
    seenIntro = false;
    showLesson(0);
    setVerdict('progress cleared — the creature waits, fresh.', '');
  });
  $('rest-btn').addEventListener('click', async function () {
    clearTouch();
    /* L1 BY-HAND FIX: "stand at rest" now means the AUTHORED rest -- the
       page also lays the world's weight back down. The old button left
       gravity on, so after the_stand a player (and the by-hand audit) had
       no page-surfaced way back to the state every pressure lesson's calm
       bar assumes. The engine's off is exact: root_y = root_vy = 0. */
    try { await postJSON('/api/gravity', { on: false }); } catch (err) { /* the world keeps its weight */ }
    await resetPose();
    setHand('standing at rest — the world back at its authored rest');
  });

  $('save-btn').addEventListener('click', async function () {
    var btn = $('save-btn');
    btn.disabled = true;
    try {
      var lessons = {}, k;
      for (k in lessonsKnown) lessons[k] = lessonsKnown[k];
      for (var id in lessonState)
        if (lessonState[id].passed)
          lessons[id] = { passed: true, at: new Date().toISOString() };
      var res = await postJSON(API.progress, { name: playerName, lessons: lessons,
        seen_intro: !!seenIntro });   // E4: a manual save must never wipe the greeting flag
      if (!res.ok) throw new Error('http ' + res.status);
      lessonsKnown = lessons;
      snd('saved');
      setVerdict('saved. the world remembers you, ' + playerName + '.', 'good');
    } catch (err) {
      setVerdict('the world did not answer — nothing was saved.', 'warn');
    } finally {
      btn.disabled = false;
    }
  });

  var anatomyScene = null;
  var anatomyReady = fetch('/api/scene').then(function(r){ return r.json(); }).then(function(s){
    if(s.mode !== 'anatomy') return;
    anatomyScene=s;
    document.querySelector('#screen-start .subtitle').textContent='Macaque anatomy from published bone geometry. Explore its joints at real scale.';
    document.querySelector('#screen-start .fineprint').textContent='An anatomical assembly in progress: seven bone meshes, with distinct tissue layers to follow.';
    $('play-btn').textContent='EXPLORE ANATOMY';
  }).catch(function(){});
  function showAnatomy() {
    $('save-btn').style.display='none';
    document.title='Chimera — macaque anatomy';
    cam.target=anatomyScene.camera.target;cam.r=anatomyScene.camera.radius;cam.near=.002;
    document.querySelectorAll('#sidebar > .card').forEach(function(e){e.style.display='none';});
    var side=$('sidebar');var panel=document.createElement('section');panel.className='card';side.appendChild(panel);
    function line(tag,text){var e=document.createElement(tag);e.textContent=text;panel.appendChild(e);return e;}
    line('h2','MACAQUE • BONE ASSEMBLY');
    line('p','Published arm geometry, in metres. Move a joint to see its bones move together. Drag to orbit; scroll to zoom.');
    line('p','Kinematic reference. Muscle forces and soft-tissue layers are not active yet.');
    var notice=line('p','Rest configuration from the source model.');notice.setAttribute('aria-live','polite');
    var controls=[];
    anatomyScene.joints.slice(1).forEach(function(j){
      var label=document.createElement('label');label.style.display='block';label.style.marginTop='14px';
      label.textContent=j.name.replace(/_/g,' ');panel.appendChild(label);
      var input=document.createElement('input');input.type='range';input.min=j.limits_deg[0];input.max=j.limits_deg[1];input.step=.5;input.value=0;input.style.width='100%';input.setAttribute('aria-label',j.name.replace(/_/g,' '));label.appendChild(input);
      var value=document.createElement('span');label.appendChild(value);
      function update(){var angle=Number(input.value)+j.source_default_rad*180/Math.PI;value.textContent=(Math.abs(angle)<.05?0:angle).toFixed(1)+'°';}
      update();controls.push({input:input,joint:j,update:update});
      input.addEventListener('input',update);
      input.addEventListener('change',async function(){
        try{var r=await postJSON('/api/pose',{joint:j.name,deg:Number(input.value)});var result=await r.json();notice.textContent=result.ok?'Pose applied by the native engine.':'Pose refused: '+result.error;}
        catch(e){notice.textContent='The native engine did not answer.';}
      });
    });
    var reset=line('button','Restore source pose');reset.className='btn';reset.style.marginTop='16px';
    reset.addEventListener('click',async function(){
      try {
        for(var c of controls){var r=await postJSON('/api/pose',{joint:c.joint.name,deg:0});var reply=await r.json();if(!reply.ok)throw new Error(reply.error||'pose refused');c.input.value=0;c.update();}
        notice.textContent='Source pose restored.';
      } catch(e) {notice.textContent='Restore failed: '+e.message;}
    });
    line('h2','SOURCE COVERAGE').style.marginTop='24px';
    anatomyScene.bones.forEach(function(b){var d=b.metrics.bounds_m;var mm=d[1].map(function(v,i){return ((v-d[0][i])*1000).toFixed(1);});line('p',b.body+': '+mm.join(' × ')+' mm'+(b.metrics.edges_not_shared_twice?' · boundary repair needed':''));});
    line('p',anatomyScene.muscle_records+' muscle records retained; '+anatomyScene.muscles_with_wrapping+' require paths around bone.');
    var link=line('a','Source and license: Limblab monkeyArmModel');link.href='https://github.com/limblab/monkeyArmModel';link.target='_blank';link.rel='noopener';
  }
  async function enterPlay() {
    playerName = $('name-input').value.trim() || 'wanderer';
    $('cam-name').textContent = playerName;
    $('screen-start').classList.remove('on');
    $('screen-play').classList.add('on');
    W2alignForceNote();   // W2: the tick needs the VISIBLE layout (0 while hidden)
    /* W4: the AudioContext must be created (or resumed) INSIDE a user
       gesture or the browser keeps it suspended -- the PLAY click (or its
       Enter key) is the page's first. snd() is a silent no-op when
       sound.js never loaded. */
    snd('init');
    snd('ambient', true);   // the session-start swell: the bed fades in under the greeting
    await anatomyReady;
    if (anatomyScene) { showAnatomy(); return; }
    await loadKnownProgress();
    await loadLessons();
    if (!seenIntro) E4showIntro();   // E4: the first-run greeting, once per name
  }
  $('play-btn').addEventListener('click', enterPlay);
  $('name-input').addEventListener('keydown', function (e) {
    if (e.key === 'Enter') enterPlay();
  });

  async function loadKnownProgress() {
    try {
      var res = await fetch(API.progress + '?name=' + encodeURIComponent(playerName));
      if (!res.ok) return;
      var d = await res.json();
      lessonsKnown = (d && d.lessons) || {};
      seenIntro = !!(d && d.seen_intro);   // E4: the greeting shows once per name
      for (var id in lessonsKnown)
        if (lessonsKnown[id] && lessonsKnown[id].passed) {
          if (!lessonState[id]) lessonState[id] = { goalMet: true, passed: true, phase: 'done' };
          lessonState[id].passed = true;
        }
    } catch (err) {
      /* a silent world is not an error worth surfacing here */
    }
  }

  /* ================= E4: first-run intro + progression + payoff =================
     Intro: shows once per name (seen_intro in progress/<name>.json), Enter
     begins. Progression: 5 dots under the lesson nav, filled per passed
     lesson; when ALL 5 pass with at least one pass made THIS session, the
     payoff flourish plays once. A 400 ms watcher owns all of it so it stays
     independent of the judge and of any other agent's functions. */
  var seenIntro = false;       // persisted in the progress file as seen_intro
  var payoffShown = false;     // the flourish fires once per session, never on load
  var dotsBuilt = false;
  var E4armed = false;         // first sight of the pack seeds, never fires
  var E4knownPassed = {};      // lesson ids already passed as of the last tick
  var E4sessionPassed = {};    // lesson ids that flipped to passed THIS session

  function E4overlayOpen() {
    return !$('intro-overlay').classList.contains('hidden') ||
           !$('payoff-overlay').classList.contains('hidden');
  }

  /* the merged lesson map the progress POST carries (same shape as the
     save button's) — used when the intro dismissal stores seen_intro */
  function E4mergedLessons() {
    var lessons = {}, k;
    for (k in lessonsKnown) lessons[k] = lessonsKnown[k];
    for (var id in lessonState)
      if (lessonState[id].passed)
        lessons[id] = { passed: true, at: new Date().toISOString() };
    return lessons;
  }

  /* ---- the progression strip ---- */
  function E4buildDots() {
    if (dotsBuilt || !LESSONS.length) return;
    dotsBuilt = true;
    var strip = $('progress-strip');
    LESSONS.forEach(function (l) {
      var d = document.createElement('span');
      d.className = 'dot';
      d.setAttribute('role', 'listitem');
      d.id = 'dot-' + l.id;
      strip.appendChild(d);
    });
  }
  function E4syncDots() {
    E4buildDots();
    for (var i = 0; i < LESSONS.length; i++) {
      var l = LESSONS[i], d = $('dot-' + l.id);
      if (!d) continue;
      var passed = !!(lessonState[l.id] && lessonState[l.id].passed);
      d.classList.toggle('passed', passed);
      d.setAttribute('aria-label', 'Lesson ' + (i + 1) + ' — ' + l.title +
        (passed ? ': passed' : ': not passed yet'));
    }
  }

  /* ---- the payoff trigger: dots, fresh passes, the fifth pass ---- */
  function E4checkProgression() {
    E4syncDots();
    if (!LESSONS.length || payoffShown) return;
    if (!E4armed) {
      /* seed from disk-progressed lessons without firing: a returning
         player who already passed everything must not be congratulated
         for merely loading the page */
      E4armed = true;
      for (var j = 0; j < LESSONS.length; j++) {
        var id0 = LESSONS[j].id;
        E4knownPassed[id0] = !!(lessonState[id0] && lessonState[id0].passed);
      }
      return;
    }
    var passedCount = 0, fresh = false;
    for (var i = 0; i < LESSONS.length; i++) {
      var id = LESSONS[i].id, st = lessonState[id];
      if (st && st.passed) {
        passedCount++;
        if (!E4knownPassed[id]) { E4sessionPassed[id] = true; fresh = true; }
      }
      E4knownPassed[id] = !!(st && st.passed);
    }
    if (fresh && passedCount === LESSONS.length &&
        $('screen-play').classList.contains('on')) {
      payoffShown = true;
      E4showPayoff();
    }
  }

  /* E4V2: the pass count spoken, not digits — "Ten lessons." */
  var E4NUMWORDS = ['zero', 'one', 'two', 'three', 'four', 'five', 'six',
    'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve', 'thirteen',
    'fourteen', 'fifteen', 'sixteen', 'seventeen', 'eighteen', 'nineteen',
    'twenty'];
  function E4countPhrase(n) {
    var w = E4NUMWORDS[n] || String(n);
    return w.charAt(0).toUpperCase() + w.slice(1) + (n === 1 ? ' lesson.' : ' lessons.');
  }
  function E4showPayoff() {
    clearTouch();                          // the ceremony asks for an open hand
    $('payoff-name').textContent = playerName;
    $('payoff-addressee').textContent = playerName;                  // E4V2: name the camera in the flourish
    $('payoff-count').textContent = E4countPhrase(LESSONS.length);   // E4V2: count the passes
    $('payoff-overlay').classList.remove('hidden');
    $('payoff-actions').classList.remove('show');
    setTimeout(function () {               // the flourish holds three seconds,
      if ($('payoff-overlay').classList.contains('hidden')) return;
      $('payoff-actions').classList.add('show');
      $('payoff-continue').focus();
    }, 3000);
  }
  function E4dismissPayoff() {
    $('payoff-overlay').classList.add('hidden');
  }
  $('payoff-save').addEventListener('click', function () {
    E4dismissPayoff();
    $('save-btn').click();                 // the one real save flow reports itself
  });
  $('payoff-continue').addEventListener('click', E4dismissPayoff);

  /* ---- the intro ---- */
  /* E4V2: the intro card's one-line key hint for the CURRENT lesson — the
     phrase is pulled from the lesson's body when it names SPACE, else the
     generic "to touch". enterPlay loads the lessons before greeting, so
     curLesson() is real here. */
  function E4setIntroKeyHint() {
    var el = $('intro-key-hint-text');
    if (!el) return;
    var phrase = 'to touch';
    var l = curLesson();
    if (l && typeof l.body === 'string' && /SPACE/i.test(l.body)) {
      var m = l.body.match(/[^.!?]*SPACE[^.!?]*/i);
      if (m) {
        var said = m[0].replace(/\s+/g, ' ').trim();
        var at = said.toUpperCase().indexOf('SPACE');
        var tail = said.slice(at + 5).replace(/^[\s,:;\u2014\u2013-]+/, '').trim();
        if (tail) phrase = tail.charAt(0).toLowerCase() + tail.slice(1);
      }
    }
    el.textContent = phrase;
  }
  function E4showIntro() {
    E4setIntroKeyHint();                   // E4V2: the lesson's SPACE hint
    $('intro-overlay').classList.remove('hidden');
    $('intro-begin').focus();
  }
  function E4dismissIntro() {
    if ($('intro-overlay').classList.contains('hidden')) return;   // re-entrancy guard
    $('intro-overlay').classList.add('hidden');
    seenIntro = true;
    // store the flag at once: the world remembers this camera was greeted
    postJSON(API.progress, { name: playerName, lessons: E4mergedLessons(),
                             seen_intro: true }).catch(function () {});
  }
  $('intro-begin').addEventListener('click', E4dismissIntro);

  /* ---- overlays own the keyboard while up ---- */
  window.addEventListener('keydown', function (e) {
    if (!E4overlayOpen()) return;
    var k = e.key;
    if (!$('intro-overlay').classList.contains('hidden')) {
      if (k === 'Enter' || k === ' ' || k === 'Escape') {
        e.preventDefault();
        E4dismissIntro();
      }
      return;
    }
    if (k === 's' || k === 'S') {          // save the memory, then free play
      e.preventDefault();
      E4dismissPayoff();
      $('save-btn').click();
      return;
    }
    if (k === 'Enter' || k === ' ' || k === 'Escape') {
      e.preventDefault();
      E4dismissPayoff();
    }
  });

  /* ---- the hand-strength control (the - / = keys dispatch 'input') ---- */
  /* W2: the fill + tick now live on the input's own track (--fill /
     --tick-x); the impostor meter is gone, so what is drawn is what hits. */
  var W2_TICK_FRAC = 0.1515;               // the gentle threshold, as drawn
  function E4syncForceMeter() {
    var lo = Number(forceEl.min), hi = Number(forceEl.max);
    var pct = (Number(forceEl.value) - lo) / ((hi - lo) || 1) * 100;
    forceEl.style.setProperty('--fill', pct + '%');
  }
  /* the note's "gentle ≤" label rides the input's OWN tick x -- the note
     spans the whole card, the input does not, so a bare % would lie about
     where the threshold sits (the old 15.15%-of-295px vs 15.15%-of-197px
     mismatch was half of the impostor's trick) */
  function W2alignForceNote() {
    var note = $('force-meter-note');
    var gn = note && note.querySelector('.gentle-note');
    if (!gn) return;
    var ir = forceEl.getBoundingClientRect(), nr = note.getBoundingClientRect();
    if (ir.width < 1) return;   // hidden screen: layout not real yet (retry on show)
    gn.style.left = (ir.left - nr.left + W2_TICK_FRAC * ir.width) + 'px';
    forceEl.style.setProperty('--tick-x', (W2_TICK_FRAC * ir.width) + 'px');
  }
  forceEl.addEventListener('input', E4syncForceMeter);
  window.addEventListener('resize', W2alignForceNote);
  E4syncForceMeter();
  W2alignForceNote();

  setInterval(E4checkProgression, 400);    // E4: dots + the payoff trigger

  /* ================= boot ================= */
  forceLabel.textContent = forceEl.value + ' N';
  $('name-input').focus();

  loadTopology();                       // THE WORLD attaches on any machine —
                                        // only the DRAWING needs WebGL2
  if (gl) {
    try {
      RG = initRenderer();
      requestAnimationFrame(frame);
    } catch (err) {
      RG = null;
      $('gl-error').classList.remove('hidden');
    }
  } else {
    $('gl-error').classList.remove('hidden');
  }

  /* H7 FIX (D6 -- the 429 storm). The old fixed timers (333 ms verts /
     700 ms state) retried at full speed forever, and pollVerts added an
     IMMEDIATE ?delta=key pull on every failure -- measured on a starved
     page: 443 req/min until the shell's own budget 429s it (1362 console
     errors in 17 min in the H5 dry-run). Now: every FAILED poll backs off
     exponentially (2^n beats, capped) with +/-20% jitter; any success
     restores the base pace. And a starved world reads as an honest HOLD:
     the verdict line says the world is unreachable and asks nothing of
     the player; it restores itself when the water answers again. */
  var vertFailStreak = 0, stateFailStreak = 0, savedVerdict = null;
  var UNREACHABLE_MSG = 'the world is unreachable — the lesson holds for the ' +
    'world, not for you. nothing is being asked; this line clears on its own.';
  function pollLoop(fn, baseMs, maxMs, onResult) {
    (async function run() {
      for (;;) {
        var r;
        try { r = await fn(); } catch (e) { r = false; }
        var ok = (r !== false);
        onResult(ok);
        var jitter = 0.8 + 0.4 * Math.random();          // +/- 20 %
        var beat = ok ? baseMs
          : Math.min(maxMs, baseMs * Math.pow(2, worldStreakMax())) * jitter;
        await sleepShell(beat);
      }
    })();
  }
  function worldStreakMax() {
    return Math.min(Math.max(vertFailStreak, stateFailStreak), 6);
  }
  function sleepShell(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  function syncUnreachable() {
    var any = worldStreakMax() >= 3;
    var both = vertFailStreak >= 3 && stateFailStreak >= 3;
    if (both) {
      if (savedVerdict === null)
        savedVerdict = { text: verdictEl.textContent, cls: verdictEl.className };
      setLink('the world is unreachable — retrying gently (backoff).');
      /* direct DOM write: setVerdict() follows the save (below), so the
         unreachable note must not go through it */
      verdictEl.textContent = UNREACHABLE_MSG;
      verdictEl.className = 'verdict warn';
    } else if (any) {
      setLink('part of the world is unreachable — retrying gently (backoff).');
    } else if (savedVerdict !== null) {
      setLink('');
      verdictEl.textContent = savedVerdict.text;
      verdictEl.className = savedVerdict.cls;
      savedVerdict = null;
    } else if (lastLink) {
      setLink('');
    }
  }
  pollLoop(pollVerts, 333, 15000, function (ok) {
    vertFailStreak = ok ? 0 : vertFailStreak + 1; syncUnreachable();
  });
  pollLoop(pollState, 700, 10000, function (ok) {
    stateFailStreak = ok ? 0 : stateFailStreak + 1; syncUnreachable();
  });

  /* H16 TOUCH-SIDE: a ?debug=1 pick probe -- the EXACT functions the press
     uses (camEye, pickWorld) plus a checksum of RG.verts, so a headless
     probe can prove the pick reads the same buffer the renderer draws and
     compare the page's raw pick against its own replicated math, without
     reaching into this IIFE. Exports NOTHING without the flag (same gate
     as the judge telemetry line). */
  if (/[?&]debug=1/.test(location.search)) {
    window.__h16pickProbe = function (x, y) {
      var rect = canvas.getBoundingClientRect();
      var eye = camEye([0, 0, 0]);
      var fwd = norm3(sub3(cam.target, eye));
      var right = norm3(cross3(fwd, UP));
      var upv = cross3(right, fwd);
      var tanF = Math.tan(cam.fov / 2);
      var aspect = rect.width / rect.height;
      var ndcX = ((x - rect.left) / rect.width) * 2 - 1;
      var ndcY = 1 - ((y - rect.top) / rect.height) * 2;
      var kx = ndcX * tanF * aspect, ky = ndcY * tanF;
      var dir = norm3([
        fwd[0] + right[0] * kx + upv[0] * ky,
        fwd[1] + right[1] * kx + upv[1] * ky,
        fwd[2] + right[2] * kx + upv[2] * ky
      ]);
      var raw = pickWorld(x, y);
      var s1 = 0, s2 = 0, n = 0;
      if (RG && RG.verts) {
        for (var i = 0; i < RG.verts.length; i += 3) {
          s1 += RG.verts[i] + RG.verts[i + 1] + RG.verts[i + 2];
          s2 += RG.verts[i] * RG.verts[i] + RG.verts[i + 1] * RG.verts[i + 1] +
                RG.verts[i + 2] * RG.verts[i + 2];
          n++;
        }
      }
      return { raw: raw, eye: [eye[0], eye[1], eye[2]],
               fwd: fwd, right: right, upv: upv, dir: dir,
               ndcX: ndcX, ndcY: ndcY, kx: kx, ky: ky,
               rectW: rect.width, rectH: rect.height, tanF: tanF,
               triCount: RG ? RG.triCount : 0,
               vertCount: n, sum1: s1, sum2: s2 };
    };
  }
})();
