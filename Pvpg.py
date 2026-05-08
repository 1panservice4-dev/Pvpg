import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="SYNC ARENA Final", layout="centered")

st.title("⚔️ SYNC ARENA: Damage Fix")
st.write("타격 판정과 HP 동기화를 대폭 강화했습니다. 방을 새로 파서 테스트해 보세요!")

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
        import {{ getDatabase, ref, set, onValue, onDisconnect, update, runTransaction }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

        const app = initializeApp({json.dumps(FIREBASE_CONFIG)});
        const db = getDatabase(app);

        let ph=100, eh=100, px=80, ex=80, pb=0, eb=0, inv=false, bsy=false, end=false, started=false;
        let myRole = "", enemyRole = "", roomId = "", hero = 'W', vY=0, animId;
        // 리치(r)와 데미지(d)를 상향 조정
        const cfg = {{ W: {{h:100, r:150, d:15}}, A: {{h:70, r:120, d:20}}, S: {{h:90, r:130, d:12}} }};
        const keys = {{}};
        let moveLeft = false, moveRight = false, touchStartY = 0;

        window.go = () => {{
            const val = document.getElementById('room-input').value;
            if(!val) return alert("Room ID!");
            roomId = val;
            joinRoom(roomId);
        }};

        function joinRoom(id) {{
            const roomRef = ref(db, 'rooms/' + id);
            onValue(roomRef, (snapshot) => {{
                const data = snapshot.val();
                if (!data) return;

                if (!myRole) {{
                    if (!data.p1) {{ myRole = "p1"; enemyRole = "p2"; }}
                    else if (!data.p2) {{ myRole = "p2"; enemyRole = "p1"; }}
                    else return;
                    ph = cfg[hero].h;
                    const myRef = ref(db, `rooms/${{id}}/${{myRole}}`);
                    onDisconnect(myRef).remove();
                    set(myRef, {{ x:px, y:pb, hp:ph, act:0, hero:hero }});
                    startGame();
                }}

                if (data.winner && !end) {{
                    end = true;
                    showResult(data.winner === myRole ? "VICTORY" : "GAME OVER");
                }}

                if (data[enemyRole]) {{
                    const ed = data[enemyRole];
                    ex = 600 - ed.x - 40; eb = ed.y; eh = ed.hp;
                    const eEl = document.getElementById('e');
                    if(ed.act === 2) eEl.classList.add('spinning');
                    else eEl.classList.remove('spinning');
                    if(ed.act === 1) triggerEnemyAttack(cfg[ed.hero].r);
                }}
                
                // 내 피가 0이 되면 패배 처리
                if (data[myRole] && data[myRole].hp <= 0 && !data.winner) {{
                    update(ref(db, 'rooms/' + roomId), {{ winner: enemyRole }});
                }}
            }});
        }}

        // [핵심] 공격 시 상대방 HP를 직접 깎는 로직
        const attack = () => {{
            if(bsy || end || !started) return;
            bsy = true; 
            sync(1); // 공격 모션 전송
            
            // 거리 체크: 내 화면 기준 상대와의 거리
            let dist = Math.abs(px - (600 - ex - 40));
            if (dist < cfg[hero].r && eb < 80) {{
                // Transaction을 사용하여 동시 수정 오류 방지
                const enemyHpRef = ref(db, `rooms/${{roomId}}/${{enemyRole}}/hp`);
                runTransaction(enemyHpRef, (currentHp) => {{
                    if (currentHp === null) return 0;
                    return Math.max(0, currentHp - cfg[hero].d);
                }});
            }}

            const w = document.getElementById('p-w');
            w.style.width = cfg[hero].r + 'px'; w.style.opacity = 1;
            setTimeout(() => {{ 
                w.style.width = 0; w.style.opacity = 0; bsy = false; 
                sync(0); 
            }}, 200);
        }};

        function sync(act = 0) {{
            if(!myRole || end) return;
            update(ref(db, `rooms/${{roomId}}/${{myRole}}`), {{ x:px, y:pb, act:act }});
        }}

        const jump = () => {{ if(pb === 0 && !end && started) vY = 22; }};
        const dodge = () => {{
            if(inv || end || !started) return;
            inv = true; sync(2);
            document.getElementById('p').classList.add('spinning');
            px = Math.max(0, Math.min(540, px + (px < 300 ? 140 : -140)));
            setTimeout(() => {{ 
                document.getElementById('p').classList.remove('spinning'); 
                inv = false; sync(0); 
            }}, 450);
        }};

        // 터치 제스처 로직
        window.addEventListener('touchstart', (e) => {{
            if(!started || end) return;
            touchStartY = e.touches[0].clientY;
            if (e.touches.length === 1) {{
                if (e.touches[0].clientX < window.innerWidth / 2) moveLeft = true;
                else moveRight = true;
            }} else if (e.touches.length === 2) attack();
        }});
        window.addEventListener('touchend', (e) => {{
            moveLeft = false; moveRight = false;
            if(!started || end) return;
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
        }}

        function gameLoop() {{
            if(!end && started) {{
                if(!inv && !bsy) {{
                    if(keys['ArrowLeft'] || moveLeft) px = Math.max(0, px - 9);
                    if(keys['ArrowRight'] || moveRight) px = Math.min(540, px + 9);
                }}
                if(pb > 0 || vY !== 0) {{ vY -= 1.3; pb += vY; if(pb <= 0) {{ pb = 0; vY = 0; }} }}
                sync(inv ? 2 : (bsy ? 1 : 0));
            }}
            document.getElementById('p').style.left = px + 'px';
            document.getElementById('p').style.bottom = pb + 'px';
            document.getElementById('e').style.right = (600 - ex - 40) + 'px';
            document.getElementById('e').style.bottom = eb + 'px';
            document.getElementById('p-h').style.width = ph + '%';
            document.getElementById('e-h').style.width = eh + '%';
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
        function triggerEnemyAttack(r) {{ 
            const ew=document.getElementById('e-w'); ew.style.width=r+'px'; ew.style.opacity=1; 
            setTimeout(()=>{{ew.style.width=0;ew.style.opacity=0;}},150); 
        }}
    </script>
    <style>
        body {{ margin: 0; background: #000; touch-action: none; overflow: hidden; font-family: sans-serif; }}
        #g-area {{ width: 100vw; height: 320px; background: #080808; position: relative; border-bottom: 2px solid #444; }}
        #lby {{ position: absolute; inset: 0; background: #111; z-index: 200; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }}
        #btl {{ display: none; width: 100%; height: 100%; position: relative; }}
        #p, #e {{ position: absolute; width: 40px; height: 80px; border: 2px solid white; border-radius: 4px; }}
        #p {{ background: linear-gradient(#4d79ff, #002db3); }}
        #e {{ background: linear-gradient(#ff4d4d, #b30000); }}
        .wpn {{ position: absolute; top: 30px; height: 10px; background: #fff; opacity: 0; box-shadow: 0 0 15px #fff; }}
        #p-w {{ left: 40px; }} #e-w {{ right: 40px; }}
        .hp-b {{ width: 130px; height: 15px; background: #222; border: 1px solid white; border-radius: 10px; overflow: hidden; }}
        .hp-f {{ height: 100%; transition: 0.1s; }}
        .c-btn {{ padding: 10px 15px; margin: 5px; background: #222; border: 1px solid #fff; color: white; cursor: pointer; }}
        .c-btn.on {{ background: #4d79ff; border-color: #fff; }}
        #res-ui {{ position: absolute; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 300; color: white; }}
        .spinning {{ animation: spin 0.4s linear infinite; }}
        @keyframes spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
        .start-btn {{ padding: 15px 50px; background: #e60000; color: white; border: none; font-weight: bold; border-radius: 30px; font-size: 20px; cursor: pointer; margin-top: 10px; }}
    </style>
</head>
<body>
    <div id="g-area">
        <div id="lby">
            <h2 style="letter-spacing: 2px;">SYNC ARENA</h2>
            <div style="margin-bottom: 15px;">
                <button class="c-btn on" onclick="sel('W', this)">WARRIOR</button>
                <button class="c-btn" onclick="sel('A', this)">ASSASSIN</button>
            </div>
            <input type="text" id="room-input" placeholder="Room ID" style="padding: 10px; border-radius: 5px; text-align: center;">
            <button class="start-btn" onclick="go()">START</button>
        </div>
        <div id="btl">
            <div id="res-ui">
                <h1 id="res-msg"></h1>
                <button onclick="window.parent.location.reload()" style="padding: 10px 30px;">RELOAD</button>
            </div>
            <div style="padding: 20px; display: flex; justify-content: space-between;">
                <div class="hp-b"><div id="p-h" class="hp-f" style="background:#4d79ff"></div></div>
                <div class="hp-b"><div id="e-h" class="hp-f" style="background:#ff4d4d"></div></div>
            </div>
            <div id="p"><div id="p-w" class="wpn"></div></div>
            <div id="e"><div id="e-w" class="wpn"></div></div>
        </div>
    </div>
</body>
</html>
"""

components.html(game_html, height=500)
