import streamlit as st
import streamlit.components.v1 as components
import json

# 1. 페이지 설정
st.set_page_config(page_title="SYNC ARENA Online", layout="centered")

# 2. 제목 및 설명
st.title("⚔️ SYNC ARENA: Multiplayer")
st.write("방 번호(Room ID)를 맞춰서 친구와 접속하세요!")

# 3. 게임 설정 (필요시 여기서 이미지 URL을 넣으세요)
FIREBASE_CONFIG = {
    "apiKey": "AIzaSyByXhG3mytCcapT0o260PU1RUYwltQGg94",
    "databaseURL": "https://pvpg-6f280-default-rtdb.firebaseio.com/",
    "projectId": "pvpg-6f280",
}

USER_CONFIG = {
    "PLAYER_IMAGE": "",
    "WEAPON_IMAGE": "",
    "ENEMY_IMAGE": ""
}

# 스타일 변수 및 초기화값 준비
p_img = f"url('{USER_CONFIG['PLAYER_IMAGE']}')" if USER_CONFIG['PLAYER_IMAGE'] else "none"
e_img = f"url('{USER_CONFIG['ENEMY_IMAGE']}')" if USER_CONFIG['ENEMY_IMAGE'] else "none"
w_img_val = f"url('{USER_CONFIG['WEAPON_IMAGE']}')" if USER_CONFIG['WEAPON_IMAGE'] else "#fff"
w_bg_reset = "transparent" if USER_CONFIG['WEAPON_IMAGE'] else "#fff"

# 4. 전체 게임 HTML 코드
game_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <script type="module">
        import {{ initializeApp }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
        import {{ getDatabase, ref, set, onValue, onDisconnect, update }} from "https://www.gstatic.com/firebasejs/10.7.1/firebase-database.js";

        const app = initializeApp({json.dumps(FIREBASE_CONFIG)});
        const db = getDatabase(app);

        let ph, eh=100, pu=0, px=80, ex=80, pb=0, eb=0, inv=false, bsy=false, isUlt=false, end=false;
        let myRole = "", enemyRole = "", roomId = "", hero = 'W', vY=0, animId;
        const cfg = {{ 
            W: {{h:100, r:120, d:12, type:'n'}}, 
            A: {{h:70, r:90, d:18, type:'n'}}, 
            S: {{h:90, r:100, d:10, type:'s'}} 
        }};
        const keys = {{}};

        window.go = () => {{
            roomId = document.getElementById('room-input').value || "room_1";
            joinRoom(roomId);
        }};

        function joinRoom(id) {{
            const roomRef = ref(db, 'rooms/' + id);
            onValue(roomRef, (snapshot) => {{
                const data = snapshot.val();
                if (!myRole) {{
                    if (!data || !data.p1) {{ myRole = "p1"; enemyRole = "p2"; }}
                    else if (!data.p2) {{ myRole = "p2"; enemyRole = "p1"; }}
                    else {{ alert("Full!"); return; }}

                    const myRef = ref(db, `rooms/${{id}}/${{myRole}}`);
                    onDisconnect(myRef).remove();
                    set(myRef, {{ x:80, y:0, hp:cfg[hero].h, act:0, hero:hero, pu:0 }});
                    startGame();
                }}

                if (data && data[enemyRole]) {{
                    const ed = data[enemyRole];
                    ex = 600 - ed.x - 40;
                    eb = ed.y;
                    eh = ed.hp;
                    if(ed.act === 1) triggerEnemyAttack(cfg[ed.hero].r);
                    if(ed.act === 2) triggerEnemyDodge();
                    if(ed.act === 3) triggerEnemyUlt(ed.hero);
                }}
            }});
        }}

        function sync(act = 0) {{
            if(!myRole || end) return;
            update(ref(db, `rooms/${{roomId}}/${{myRole}}`), {{ x:px, y:pb, hp:ph, act:act, pu:pu }});
        }}

        window.sel = (t, el) => {{ 
            hero=t; 
            document.querySelectorAll('.c-btn').forEach(b=>b.classList.remove('on')); 
            el.classList.add('on'); 
        }};

        function attack() {{
            if(bsy || isUlt || end) return;
            bsy = true; sync(1);
            const w = document.getElementById('p-w');
            const range = cfg[hero].r;
            w.style.width = range + 'px'; w.style.opacity = 1;

            let dist = 600 - px - (600 - ex - 40) - 40;
            if(dist < range && dist > -30 && pb < 100) {{
                update(ref(db, `rooms/${{roomId}}/${{enemyRole}}`), {{ hp: Math.max(0, eh - cfg[hero].d) }});
                pu = Math.min(100, pu + 15);
            }}
            setTimeout(() => {{ w.style.width = 0; w.style.opacity = 0; bsy = false; sync(0); }}, 150);
        }}

        function dodge() {{
            if(inv || isUlt || end) return;
            inv = true; sync(2);
            document.getElementById('p').classList.add('spinning');
            px = Math.max(0, Math.min(540, px + (px < 300 ? 150 : -150)));
            setTimeout(() => {{ document.getElementById('p').classList.remove('spinning'); inv = false; sync(0); }}, 450);
        }}

        function ultimate() {{
            if(pu < 100 || bsy || end || inv || isUlt) return;
            pu = 0; isUlt = true; sync(3);
            const cut = document.getElementById('cut');
            cut.style.display = 'flex';
            
            setTimeout(() => {{
                cut.style.display = 'none';
                if(cfg[hero].type === 's') {{
                    const pEl = document.getElementById('p');
                    pEl.classList.add('spinning'); pEl.style.boxShadow = "0 0 30px #ffcc00";
                    let count = 0;
                    let ultInt = setInterval(() => {{
                        if(keys['ArrowLeft']) px = Math.max(0, px - 10);
                        if(keys['ArrowRight']) px = Math.min(540, px + 10);
                        
                        let dist = 600 - px - (600 - ex - 40) - 40;
                        if(Math.abs(dist) < 60 && pb < 100) {{
                            update(ref(db, `rooms/${{roomId}}/${{enemyRole}}`), {{ hp: Math.max(0, eh - 3) }});
                        }}
                        sync(3);
                        count++;
                        if(count > 40) {{
                            clearInterval(ultInt);
                            pEl.classList.remove('spinning'); pEl.style.boxShadow = "none";
                            isUlt = false; sync(0);
                        }}
                    }}, 30);
                }} else {{
                    bsy = true;
                    let r = cfg[hero].r * 2.5;
                    const w = document.getElementById('p-w');
                    w.style.width = r + 'px'; w.style.opacity = 1; w.style.backgroundColor = "#ffcc00";
                    let dist = 600 - px - (600 - ex - 40) - 40;
                    if(dist < r && dist > -20) {{
                        update(ref(db, `rooms/${{roomId}}/${{enemyRole}}`), {{ hp: Math.max(0, eh - 40) }});
                    }}
                    setTimeout(() => {{
                        w.style.width = 0; w.style.opacity = 0; 
                        w.style.backgroundColor = "{w_bg_reset}";
                        bsy = false; isUlt = false; sync(0);
                    }}, 400);
                }}
            }}, 800);
        }}

        function triggerEnemyAttack(range) {{
            const ew = document.getElementById('e-w');
            ew.style.width = range + 'px'; ew.style.opacity = 1;
            setTimeout(() => {{ ew.style.width = 0; ew.style.opacity = 0; }}, 150);
        }}

        function triggerEnemyDodge() {{
            document.getElementById('e').classList.add('spinning');
            setTimeout(() => document.getElementById('e').classList.remove('spinning'), 450);
        }}

        function triggerEnemyUlt(eHero) {{
            if(cfg[eHero].type === 's') {{
                document.getElementById('e').classList.add('spinning');
                setTimeout(()=>document.getElementById('e').classList.remove('spinning'), 1500);
            }} else {{
                const ew = document.getElementById('e-w');
                ew.style.width = (cfg[eHero].r * 2.5) + 'px'; ew.style.opacity = 1; ew.style.backgroundColor = "#ffcc00";
                setTimeout(()=> {{ ew.style.width = 0; ew.style.opacity = 0; ew.style.backgroundColor = "#fff"; }}, 400);
            }}
        }}

        function startGame() {{
            ph = cfg[hero].h;
            document.getElementById('lby').style.display = 'none';
            document.getElementById('btl').style.display = 'block';
            document.getElementById('p').style.backgroundImage = "{p_img}";
            document.getElementById('e').style.backgroundImage = "{e_img}";
            gameLoop();
        }}

        function gameLoop() {{
            if(!end && myRole) {{
                if(!inv && !bsy && !isUlt) {{
                    if(keys['ArrowLeft']) px = Math.max(0, px - 8);
                    if(keys['ArrowRight']) px = Math.min(540, px + 8);
                    if(keys['ArrowUp'] && pb === 0) vY = 22;
                }}
                if(pb > 0 || vY !== 0) {{ vY -= 1.3; pb += vY; if(pb <= 0) {{ pb = 0; vY = 0; }} }}
                if(!isUlt) sync(inv ? 2 : (bsy ? 1 : 0));

                if(ph <= 0 || eh <= 0) {{
                    end = true;
                    document.getElementById('res-ui').style.display = 'flex';
                    document.getElementById('res-msg').innerText = ph <= 0 ? "GAME OVER" : "VICTORY";
                }}
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

        window.addEventListener('keydown', e => {{ 
            keys[e.code]=true; 
            if(e.code==='Space') attack(); 
            if(e.code==='ArrowDown') dodge();
            if(e.code==='ShiftLeft' || e.code==='ShiftRight') ultimate();
        }});
        window.addEventListener('keyup', e => keys[e.code]=false);
    </script>
    <style>
        #g-area {{ width: 600px; height: 350px; background: #050505; position: relative; margin: 0 auto; border: 4px solid #444; overflow: hidden; font-family: sans-serif; }}
        #lby {{ position: absolute; inset: 0; background: #111; z-index: 100; display: flex; flex-direction: column; align-items: center; justify-content: center; color: white; }}
        #btl {{ display: none; width: 100%; height: 100%; position: relative; }}
        #p, #e {{ position: absolute; width: 40px; height: 80px; border: 2px solid white; background-size: cover; background-position: center; transition: bottom 0.1s; }}
        #p {{ background-color: #4d79ff; z-index: 10; }}
        #e {{ background-color: #ff4d4d; z-index: 5; }}
        .wpn {{ position: absolute; top: 30px; height: 10px; background: {w_img_val}; opacity: 0; border-radius: 6px; box-shadow: 0 0 10px #fff; }}
        #p-w {{ left: 40px; }} #e-w {{ right: 40px; }}
        .hp-b {{ width: 160px; height: 12px; background: #222; border: 1px solid white; }}
        .hp-f {{ height: 100%; transition: 0.2s; }}
        .ult-b {{ width: 160px; height: 6px; background: #111; border: 1px solid #555; margin-top: 4px; }}
        .ult-f {{ height: 100%; background: #ffcc00; transition: 0.3s; }}
        .spinning {{ transform: rotate(1080deg); border-radius: 50% !important; width: 60px !important; height: 60px !important; }}
        #cut {{ position: absolute; inset: 0; background: rgba(0,0,0,0.8); display: none; align-items: center; justify-content: center; z-index: 200; font-size: 40px; color: #ffcc00; font-weight: bold; }}
        #res-ui {{ position: absolute; inset: 0; background: rgba(0,0,0,0.9); display: none; flex-direction: column; align-items: center; justify-content: center; z-index: 300; color: white; }}
        .c-btn {{ padding: 8px 15px; margin: 5px; background: #222; border: 1px solid #fff; cursor: pointer; color: white; border-radius: 5px; }}
        .c-btn.on {{ background: #4d79ff; border-color: #ffcc00; }}
    </style>
</head>
<body>
    <div id="g-area">
        <div id="lby">
            <h2 style="color: #ffcc00;">SYNC ARENA ONLINE</h2>
            <div style="margin-bottom: 10px;">
                <button class="c-btn on" onclick="sel('W', this)">WARRIOR</button>
                <button class="c-btn" onclick="sel('A', this)">ASSASSIN</button>
                <button class="c-btn" onclick="sel('S', this)">SPIN MASTER</button>
            </div>
            <input type="text" id="room-input" placeholder="Room ID" style="padding: 8px; border-radius: 5px; border: none; width: 150px; text-align: center;">
            <button onclick="go()" style="margin-top: 15px; padding: 10px 40px; background: #b00; color: white; border: none; cursor: pointer; font-weight: bold; border-radius: 20px;">START BATTLE</button>
        </div>
        <div id="btl">
            <div id="cut">ULTIMATE SKILL!!</div>
            <div id="res-ui">
                <div id="res-msg" style="font-size:30px; margin-bottom:20px;"></div>
                <button onclick="window.parent.location.reload()" style="padding:10px 30px; cursor:pointer;">RESTART</button>
            </div>
            <div style="padding: 15px; display: flex; justify-content: space-between;">
                <div>
                    <div class="hp-b"><div id="p-h" class="hp-f" style="background: #4d79ff;"></div></div>
                    <div class="ult-b"><div id="p-u" class="ult-f"></div></div>
                </div>
                <div>
                    <div class="hp-b"><div id="e-h" class="hp-f" style="background: #ff4d4d;"></div></div>
                </div>
            </div>
            <div id="p"><div id="p-w" class="wpn"></div></div>
            <div id="e"><div id="e-w" class="wpn"></div></div>
        </div>
    </div>
</body>
</html>
"""

# 5. 스트림릿에서 실행
components.html(game_html, height=450)
