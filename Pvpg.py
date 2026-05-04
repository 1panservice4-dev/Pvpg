import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="SYNC ARENA Final", layout="centered")

st.title("⚔️ SYNC ARENA: Ultimate Fix")
st.info("같은 Room ID를 입력하고 'START'를 눌러주세요. 모바일은 가로 모드를 권장합니다.")

FIREBASE_CONFIG = {
    "apiKey": "AIzaSyByXhG3mytCcapT0o260PU1RUYwltQGg94",
    "databaseURL": "https://pvpg-6f280-default-rtdb.firebaseio.com/",
    "projectId": "pvpg-6f280",
}

game_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <script type="module">
        import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
        import {{ getDatabase, ref, set, onValue, onDisconnect, update, get }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

        const app = initializeApp({json.dumps(FIREBASE_CONFIG)});
        const db = getDatabase(app);

        let ph=100, eh=100, pu=0, px=80, ex=80, pb=0, eb=0, inv=false, bsy=false, end=false, started=false;
        let myRole = "", enemyRole = "", roomId = "", hero = 'W', vY=0, animId;
        const cfg = {{ W: {{h:100, r:120, d:12}}, A: {{h:70, r:90, d:18}}, S: {{h:90, r:100, d:10}} }};
        const keys = {{}};
        let moveLeft = false, moveRight = false, touchStartY = 0;

        window.go = async () => {{
            const val = document.getElementById('room-input').value;
            if(!val) return alert("Room ID를 입력하세요!");
            roomId = val;
            joinRoom(roomId);
        }};

        function joinRoom(id) {{
            const roomRef = ref(db, 'rooms/' + id);
            
            onValue(roomRef, (snapshot) => {{
                const data = snapshot.val();
                
                if (!myRole) {{
                    if (!data || !data.p1) {{ myRole = "p1"; enemyRole = "p2"; }}
                    else if (!data.p2) {{ myRole = "p2"; enemyRole = "p1"; }}
                    else {{ alert("방이 꽉 찼습니다!"); return; }}
                    
                    ph = cfg[hero].h;
                    const myRef = ref(db, `rooms/${{id}}/${{myRole}}`);
                    onDisconnect(myRef).remove();
                    set(myRef, {{ x:px, y:pb, hp:ph, act:0, hero:hero, atkId: 0 }});
                    startGame();
                }}

                if (data) {{
                    if (data.winner && !end) {{
                        end = true;
                        showResult(data.winner === myRole ? "VICTORY" : "GAME OVER");
                    }}
                    if (data[enemyRole]) {{
                        const ed = data[enemyRole];
                        ex = 600 - ed.x - 40; eb = ed.y; eh = ed.hp;
                        if(ed.act === 1 && window.lastAtkId !== ed.atkId) {{
                            window.lastAtkId = ed.atkId;
                            triggerEnemyAttack(cfg[ed.hero].r);
                            checkHit(ed.x, cfg[ed.hero].r, cfg[ed.hero].d);
                        }}
                    }}
                }}
            }});
        }}

        function checkHit(enemyX, range, damage) {{
            if (inv || pb > 80 || end) return;
            let dist = Math.abs(px - enemyX);
            if (dist < range) {{
                ph = Math.max(0, ph - damage);
                sync(0);
                if (ph <= 0) update(ref(db, 'rooms/' + roomId), {{ winner: enemyRole }});
            }}
        }}

        function sync(act = 0) {{
            if(!myRole || end) return;
            update(ref(db, `rooms/${{roomId}}/${{myRole}}`), {{ 
                x:px, y:pb, hp:ph, act:act, atkId: window.myAtkId || 0 
            }});
        }}

        const attack = () => {{
            if(bsy || end || !started) return;
            bsy = true; window.myAtkId = Date.now(); sync(1);
            const w = document.getElementById('p-w');
            w.style.width = cfg[hero].r + 'px'; w.style.opacity = 1;
            setTimeout(() => {{ w.style.width = 0; w.style.opacity = 0; bsy = false; sync(0); }}, 150);
        }};

        const jump = () => {{ if(pb === 0 && !end && started) vY = 22; }};
        const dodge = () => {{
            if(inv || end || !started) return;
            inv = true; sync(2);
            document.getElementById('p').classList.add('spinning');
            px = Math.max(0, Math.min(540, px + (px < 300 ? 120 : -120)));
            setTimeout(() => {{ document.getElementById('p').classList.remove('spinning'); inv = false; sync(0); }}, 400);
        }};

        // 터치 핸들러: started 일 때만 작동
        window.addEventListener('touchstart', (e) => {{
            if(!started || end) return;
            const t = e.touches;
            touchStartY = t[0].clientY;
            if (t.length === 1) {{
                if (t[0].clientX < window.innerWidth / 2) moveLeft = true;
                else moveRight = true;
            }} else if (t.length === 2) attack();
        }}, {{passive: false}});

        window.addEventListener('touchend', (e) => {{
            if(!started || end) return;
            moveLeft = false; moveRight = false;
            const diffY = touchStartY - e.changedTouches[0].clientY;
            if (diffY > 60) jump();
            else if (diffY < -60) dodge();
        }});

        function startGame() {{
            started = true;
            document.getElementById('lby').style.display = 'none';
            document.getElementById('btl').style.display = 'block';
            gameLoop();
        }}

        function showResult(msg) {{
            document.getElementById('res-msg').innerText = msg;
            document.getElementById('res-ui').style.display = 'flex';
            cancelAnimationFrame(animId);
        }}

        function gameLoop() {{
            if(!end && started) {{
                if(!inv && !bsy) {{
                    if(keys['ArrowLeft'] || moveLeft) px = Math.max(0, px - 8);
                    if(keys['ArrowRight'] || moveRight) px = Math.min(540, px + 8);
                }}
                if(pb > 0 || vY !== 0) {{ vY -= 1.3; pb += vY; if(pb <= 0) {{ pb = 0; vY = 0; }} }}
                sync(inv ? 2 : (bsy ? 1 : 0));
            }}
            document.getElementById('p').style.left = px + 'px';
            document.getElementById('p').style.bottom = pb + 'px';
            document.getElementById('e').style.right = (600 - ex - 40) + 'px';
            document.getElementById('e').style.bottom = eb + 'px';
            document.getElementById('p-h').style.width = (ph/cfg[hero].h*100)+'%';
            document.getElementById('e-h').style.width = (eh/100*100) + '%';
            animId = requestAnimationFrame(gameLoop);
        }}

        window.sel = (t, el) => {{ hero=t; document.querySelectorAll('.c-btn').forEach(b=>b.classList.remove('on')); el.classList.add('on'); }};
        window.addEventListener('keydown', e => {{ 
            keys[e.code]=true; 
            if(e.code==='Space') attack(); 
            if(e.code==='ArrowDown') dodge(); 
            if(e.code==='ArrowUp') jump(); 
        }});
        window.addEventListener('keyup', e => keys[e.code]=false);
        function triggerEnemyAttack(r) {{ const ew=document.getElementById('e-w'); ew.style.width=r+'px'; ew.style.opacity=1; setTimeout(()=>{{ew.style.width=0;ew.style.opacity=0;}},150); }}
    </script>
    <style>
        body {{ margin: 0; background: #000; touch-action: none; overflow: hidden; font-family: -apple-system, sans-serif; }}
        #g-area {{ width: 100vw; height: 350px; background: #050505; position: relative; border-bottom: 2px solid #444; }}
        #lby {{ position: absolute; inset: 0; background: #111; z-index: 200; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }}
        #btl {{ display: none; width: 100%; height: 100%; position: relative; }}
        #p, #e {{ position: absolute; width: 40px; height: 80px; border: 1px solid white; }}
        #p {{ background-color: #4d79ff; }} #e {{ background-color: #ff4d4d; }}
        .wpn {{ position: absolute; top: 30px; height: 8px; background: white; opacity: 0; }}
        #p-w {{ left: 40px; }} #e-w {{ right: 40px; }}
        .hp-b {{ width: 120px; height: 12px; background: #222; border: 1px solid white; }}
        .hp-f {{ height: 100%; transition: 0.1s; }}
        .c-btn {{ padding: 12px; margin: 5px; background: #222; border: 1px solid #fff; color: white; border-radius: 8px; cursor: pointer; }}
        .c-btn.on {{ background: #4d79ff; border-color: #4d79ff; }}
        #res-ui {{ position: absolute; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 300; color: white; }}
        .spinning {{ transform: rotate(360deg); transition: 0.4s; }}
        input {{ padding: 12px; text-align: center; border-radius: 8px; border: none; font-size: 16px; margin: 10px; width: 200px; }}
        .start-btn {{ padding: 12px 60px; background: #b00; color: white; border: none; font-weight: bold; border-radius: 30px; font-size: 18px; cursor: pointer; margin-top: 20px; }}
    </style>
</head>
<body>
    <div id="g-area">
        <div id="lby">
            <h2 style="margin-bottom: 20px;">SYNC ARENA</h2>
            <div style="margin-bottom: 15px;">
                <button class="c-btn on" onclick="sel('W', this)">WARRIOR</button>
                <button class="c-btn" onclick="sel('A', this)">ASSASSIN</button>
                <button class="c-btn" onclick="sel('S', this)">SPIN</button>
            </div>
            <input type="text" id="room-input" placeholder="Room ID 입력" autofocus>
            <button class="start-btn" onclick="go()">START BATTLE</button>
        </div>
        <div id="btl">
            <div id="res-ui">
                <h2 id="res-msg"></h2>
                <button onclick="window.parent.location.reload()" style="padding: 10px 30px; border-radius: 5px; cursor: pointer;">RELOAD</button>
            </div>
            <div style="padding: 15px; display: flex; justify-content: space-between;">
                <div class="hp-b"><div id="p-h" class="hp-f" style="background:#4d79ff"></div></div>
                <div class="hp-b"><div id="e-h" class="hp-f" style="background:#ff4d4d"></div></div>
            </div>
            <div id="p"><div id="p-w" class="wpn"></div></div>
            <div id="e"><div id="e-w" class="wpn"></div></div>
        </div>
    </div>
    <div style="color: #666; font-size: 12px; text-align: center; padding: 15px;">
        [Mobile] Tap Left/Right: Move | 2-Finger: Attack | Swipe Up: Jump<br>
        [PC] Arrows: Move/Jump | Space: Attack
    </div>
</body>
</html>
"""

components.html(game_html, height=550)
