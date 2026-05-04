import streamlit as st
import streamlit.components.v1 as components
import json

st.set_page_config(page_title="SYNC ARENA Online", layout="centered")

st.title("⚔️ SYNC ARENA: Mobile Ready")
st.write("이제 모바일에서도 터치로 플레이할 수 있습니다!")

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
        import {{ getDatabase, ref, set, onValue, onDisconnect, update }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

        const app = initializeApp({json.dumps(FIREBASE_CONFIG)});
        const db = getDatabase(app);

        let ph, eh=100, pu=0, px=80, ex=80, pb=0, eb=0, inv=false, bsy=false, isUlt=false, end=false;
        let myRole = "", enemyRole = "", roomId = "", hero = 'W', vY=0, animId;
        const cfg = {{ W: {{h:100, r:120, d:12, type:'n'}}, A: {{h:70, r:90, d:18, type:'n'}}, S: {{h:90, r:100, d:10, type:'s'}} }};
        const keys = {{}};

        // [네트워크 동기화 및 승패 로직 - 유지]
        window.go = () => {{
            roomId = document.getElementById('room-input').value || "room_1";
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
                    else {{ alert("방이 꽉 찼습니다!"); return; }}
                    const myRef = ref(db, `rooms/${{id}}/${{myRole}}`);
                    onDisconnect(myRef).remove();
                    set(myRef, {{ x:80, y:0, hp:cfg[hero].h, act:0, hero:hero, pu:0 }});
                    startGame();
                }}
                if (data.winner && !end) {{
                    end = true;
                    showResult(data.winner === myRole ? "VICTORY" : "GAME OVER");
                }}
                if (data[enemyRole]) {{
                    const ed = data[enemyRole];
                    ex = 600 - ed.x - 40; eb = ed.y; eh = ed.hp;
                    if(ed.act === 1) triggerEnemyAttack(cfg[ed.hero].r);
                    if(ed.act === 2) triggerEnemyDodge();
                    if(ed.act === 3) triggerEnemyUlt(ed.hero);
                    if (eh <= 0 && !data.winner) update(ref(db, 'rooms/' + roomId), {{ winner: myRole }});
                }}
                if (data[myRole]) {{
                    ph = data[myRole].hp;
                    if (ph <= 0 && !data.winner) update(ref(db, 'rooms/' + roomId), {{ winner: enemyRole }});
                }}
            }});
        }}

        function sync(act = 0) {{
            if(!myRole || end) return;
            update(ref(db, `rooms/${{roomId}}/${{myRole}}`), {{ x:px, y:pb, hp:ph, act:act, pu:pu }});
        }}

        // [액션 함수들]
        window.attack = () => {{
            if(bsy || isUlt || end) return;
            bsy = true; sync(1);
            const range = cfg[hero].r;
            document.getElementById('p-w').style.width = range + 'px';
            document.getElementById('p-w').style.opacity = 1;
            let dist = 600 - px - (600 - ex - 40) - 40;
            if(dist < range && dist > -30 && pb < 100) {{
                update(ref(db, `rooms/${{roomId}}/${{enemyRole}}`), {{ hp: Math.max(0, eh - cfg[hero].d) }});
                pu = Math.min(100, pu + 15);
            }}
            setTimeout(() => {{ document.getElementById('p-w').style.width = 0; document.getElementById('p-w').style.opacity = 0; bsy = false; sync(0); }}, 150);
        }};

        window.dodge = () => {{
            if(inv || isUlt || end) return;
            inv = true; sync(2);
            document.getElementById('p').classList.add('spinning');
            px = Math.max(0, Math.min(540, px + (px < 300 ? 150 : -150)));
            setTimeout(() => {{ document.getElementById('p').classList.remove('spinning'); inv = false; sync(0); }}, 450);
        }};

        window.jump = () => {{
            if(pb === 0 && !isUlt && !end) vY = 22;
        }};

        window.ultimate = () => {{
            if(pu < 100 || bsy || end || inv || isUlt) return;
            pu = 0; isUlt = true; sync(3);
            document.getElementById('cut').style.display = 'flex';
            setTimeout(() => {{
                document.getElementById('cut').style.display = 'none';
                if(cfg[hero].type === 's') {{
                    const pEl = document.getElementById('p');
                    pEl.classList.add('spinning'); pEl.style.boxShadow = "0 0 30px #ffcc00";
                    let count = 0;
                    let ultInt = setInterval(() => {{
                        if(keys['ArrowLeft'] || moveLeft) px = Math.max(0, px - 10);
                        if(keys['ArrowRight'] || moveRight) px = Math.min(540, px + 10);
                        let dist = 600 - px - (600 - ex - 40) - 40;
                        if(Math.abs(dist) < 60 && pb < 100) update(ref(db, `rooms/${{roomId}}/${{enemyRole}}`), {{ hp: Math.max(0, eh - 3) }});
                        sync(3);
                        count++;
                        if(count > 40) {{ clearInterval(ultInt); pEl.classList.remove('spinning'); pEl.style.boxShadow = "none"; isUlt = false; sync(0); }}
                    }}, 30);
                }} else {{
                    bsy = true; let r = cfg[hero].r * 2.5; const w = document.getElementById('p-w');
                    w.style.width = r + 'px'; w.style.opacity = 1; w.style.backgroundColor = "#ffcc00";
                    let dist = 600 - px - (600 - ex - 40) - 40;
                    if(dist < r && dist > -20) update(ref(db, `rooms/${{roomId}}/${{enemyRole}}`), {{ hp: Math.max(0, eh - 40) }});
                    setTimeout(() => {{ w.style.width = 0; w.style.opacity = 0; w.style.backgroundColor = "white"; bsy = false; isUlt = false; sync(0); }}, 400);
                }}
            }}, 800);
        }};

        // [모바일 터치 이동 변수]
        let moveLeft = false, moveRight = false;
        window.setMove = (dir, val) => {{ if(dir === 'L') moveLeft = val; if(dir === 'R') moveRight = val; }};

        function startGame() {{
            ph = cfg[hero].h;
            document.getElementById('lby').style.display = 'none';
            document.getElementById('btl').style.display = 'block';
            document.getElementById('m-ctrl').style.display = 'flex';
            gameLoop();
        }}

        function showResult(msg) {{
            const resUI = document.getElementById('res-ui');
            document.getElementById('res-msg').innerText = msg;
            resUI.style.display = 'flex';
            cancelAnimationFrame(animId);
        }}

        function gameLoop() {{
            if(!end) {{
                if(!inv && !bsy && !isUlt) {{
                    if(keys['ArrowLeft'] || moveLeft) px = Math.max(0, px - 8);
                    if(keys['ArrowRight'] || moveRight) px = Math.min(540, px + 8);
                }}
                if(pb > 0 || vY !== 0) {{ vY -= 1.3; pb += vY; if(pb <= 0) {{ pb = 0; vY = 0; }} }}
                if(!isUlt) sync(inv ? 2 : (bsy ? 1 : 0));
            }}
            document.getElementById('p').style.left = px + 'px';
            document.getElementById('p').style.bottom = pb + 'px';
            document.getElementById('e').style.right = (600 - ex - 40) + 'px';
            document.getElementById('e').style.bottom = eb + 'px';
            document.getElementById('p-h').style.width = (ph/cfg[hero].h*100)+'%';
            document.getElementById('e-h').style.width = eh + '%';
            document.getElementById('p-u').style.width = pu + '%';
            animId = requestAnimationFrame(gameLoop);
        }}

        window.sel = (t, el) => {{ hero=t; document.querySelectorAll('.c-btn').forEach(b=>b.classList.remove('on')); el.classList.add('on'); }};
        window.addEventListener('keydown', e => {{ keys[e.code]=true; if(e.code==='Space') attack(); if(e.code==='ArrowDown') dodge(); if(e.code==='ArrowUp') jump(); if(e.code.includes('Shift')) ultimate(); }});
        window.addEventListener('keyup', e => keys[e.code]=false);
        function triggerEnemyAttack(r) {{ const ew=document.getElementById('e-w'); ew.style.width=r+'px'; ew.style.opacity=1; setTimeout(()=>{{ew.style.width=0;ew.style.opacity=0;}},150); }}
        function triggerEnemyDodge() {{ document.getElementById('e').classList.add('spinning'); setTimeout(()=>document.getElementById('e').classList.remove('spinning'),450); }}
        function triggerEnemyUlt(eHero) {{ /* 연출 생략 */ }}
    </script>
    <style>
        body {{ margin: 0; padding: 0; background: #000; touch-action: manipulation; -webkit-user-select: none; }}
        #g-area {{ width: 600px; height: 320px; background: #050505; position: relative; margin: 0 auto; border: 2px solid #444; overflow: hidden; font-family: sans-serif; }}
        #lby {{ position: absolute; inset: 0; background: #111; z-index: 100; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }}
        #btl {{ display: none; width: 100%; height: 100%; position: relative; }}
        #p, #e {{ position: absolute; width: 40px; height: 80px; border: 1px solid white; }}
        #p {{ background-color: #4d79ff; }} #e {{ background-color: #ff4d4d; }}
        .wpn {{ position: absolute; top: 30px; height: 8px; background: white; opacity: 0; }}
        #p-w {{ left: 40px; }} #e-w {{ right: 40px; }}
        .hp-b {{ width: 140px; height: 10px; background: #222; border: 1px solid white; }}
        .hp-f {{ height: 100%; transition: 0.1s; }}
        .ult-b {{ width: 140px; height: 4px; background: #111; margin-top:2px; }}
        .ult-f {{ height: 100%; background: #ffcc00; }}
        #res-ui {{ position: absolute; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 300; color: white; }}
        
        /* 모바일 컨트롤러 스타일 */
        #m-ctrl {{ display: none; width: 600px; margin: 10px auto; justify-content: space-between; }}
        .m-btn {{ width: 60px; height: 60px; background: #333; border: 2px solid #fff; color: white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 14px; user-select: none; }}
        .m-btn:active {{ background: #666; }}
        .c-btn {{ padding: 5px 15px; margin: 5px; background: #222; border: 1px solid #fff; color: white; }}
        .c-btn.on {{ background: #4d79ff; }}
        .spinning {{ transform: rotate(1080deg); border-radius: 50% !important; }}
        #cut {{ position: absolute; inset: 0; background: rgba(0,0,0,0.8); display: none; align-items: center; justify-content: center; z-index: 200; font-size: 30px; color: #ffcc00; }}
        
        /* 반응형 스케일링 */
        @media screen and (max-width: 600px) {{
            #g-area, #m-ctrl {{ transform: scale(0.6); transform-origin: top center; }}
            #m-ctrl {{ margin-top: -100px; }}
        }}
    </style>
</head>
<body>
    <div id="g-area">
        <div id="lby">
            <h3>SYNC ARENA</h3>
            <div>
                <button class="c-btn on" onclick="sel('W', this)">WARRIOR</button>
                <button class="c-btn" onclick="sel('A', this)">ASSASSIN</button>
            </div>
            <input type="text" id="room-input" placeholder="Room ID" style="margin: 10px; padding: 5px;">
            <button onclick="go()" style="padding: 10px 30px; background: #b00; color: white; border: none;">START</button>
        </div>
        <div id="btl">
            <div id="cut">ULTIMATE!!</div>
            <div id="res-ui">
                <h2 id="res-msg"></h2>
                <button onclick="window.parent.location.reload()">RELOAD</button>
            </div>
            <div style="padding: 10px; display: flex; justify-content: space-between;">
                <div><div class="hp-b"><div id="p-h" class="hp-f" style="background:#4d79ff"></div></div><div class="ult-b"><div id="p-u" class="ult-f"></div></div></div>
                <div><div class="hp-b"><div id="e-h" class="hp-f" style="background:#ff4d4d"></div></div></div>
            </div>
            <div id="p"><div id="p-w" class="wpn"></div></div>
            <div id="e"><div id="e-w" class="wpn"></div></div>
        </div>
    </div>

    <div id="m-ctrl">
        <div style="display: flex; gap: 10px;">
            <div class="m-btn" ontouchstart="setMove('L', true)" ontouchend="setMove('L', false)">◀</div>
            <div class="m-btn" ontouchstart="setMove('R', true)" ontouchend="setMove('R', false)">▶</div>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div class="m-btn" style="background: #b00;" ontouchstart="attack()">ATK</div>
            <div class="m-btn" style="background: #007bff;" ontouchstart="jump()">JMP</div>
            <div class="m-btn" style="background: #28a745;" ontouchstart="dodge()">DGE</div>
            <div class="m-btn" style="background: #ffc107; color: black;" ontouchstart="ultimate()">ULT</div>
        </div>
    </div>
</body>
</html>
"""

components.html(game_html, height=550)
