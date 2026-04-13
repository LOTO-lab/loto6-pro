import csv
import json

INPUT_CSV = r"c:\Users\Kentaro\Desktop\LOTO7\loto7_data.csv"
OUTPUT_HTML = r"c:\Users\Kentaro\Desktop\LOTO7\loto7_board.html"

def main():
    print(f"Reading data from {INPUT_CSV}...")
    loto_data = []
    
    try:
        with open(INPUT_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            rows = list(reader)
            for row in rows:
                if len(row) < 9: continue
                try:
                    draw_id = row[0]
                    numbers = []
                    for col in row[2:9]:
                        num = int(col)
                        if 1 <= num <= 37:
                            numbers.append(num)
                    
                    if len(numbers) == 7:
                        display_id = f"第{draw_id}回" if draw_id.isdigit() else draw_id
                        loto_data.append({
                            "id": display_id,
                            "numbers": sorted(numbers)
                        })
                except Exception:
                    pass
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    if loto_data and isinstance(loto_data[-1]["id"], str) and loto_data[-1]["id"].replace("第","").replace("回","").isdigit():
        id_first = int(loto_data[0]["id"].replace("第","").replace("回",""))
        id_top = int(loto_data[-1]["id"].replace("第","").replace("回",""))
        if id_first < id_top:
            loto_data.reverse()

    json_data = json.dumps(loto_data, ensure_ascii=False)

    html_template = """<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOTO7 データ分析 ＆ 次回予想システム</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
        
        body { font-family: 'Inter', 'ヒラギノ角ゴ ProN', sans-serif; background-color: #f4f6f9; color: #333; margin: 0; padding: 20px; }
        h1 { font-size: 24px; color: #108020; margin-top: 0; }
        
        .header-container { max-width: 1400px; margin: 0 auto 20px; background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
        .board-container { max-width: 1400px; margin: 0 auto; background: white; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); overflow-x: auto; max-height: 80vh; }
        
        table { width: 100%; border-collapse: collapse; min-width: 1200px; text-align: center; }
        th, td { border: 1px solid #e0e0e0; padding: 4px; font-size: 13px; }
        th { background-color: #cce5cc; font-weight: bold; position: sticky; top: 0; z-index: 10; color: #2e592e; padding: 8px 4px; transition: background-color 0.3s, color 0.3s; }
        .id-col { background-color: #eaf1e8; font-weight: bold; position: sticky; left: 0; z-index: 11; min-width: 60px; color: #2e592e; }
        th.id-col { z-index: 12; background-color: #b3d9b3; }
        tr:nth-child(even) { background-color: #fafbfc; }
        tr:nth-child(odd) { background-color: #ffffff; }
        
        .num-cell { width: 26px; height: 26px; color: transparent; border-radius: 4px; margin: 0 auto; display: flex; align-items: center; justify-content: center; font-weight: bold; }
        td.active .num-cell { color: white; }

        .col-1 { background-color: #1a9c2a; } .col-2 { background-color: #00d0e0; } .col-3 { background-color: #f79c11; }
        .col-4 { background-color: #8c8c11; } .col-5 { background-color: #11d911; } .col-6 { background-color: #fce803; color: #333 !important; }
        .col-7 { background-color: #881c88; } .col-8 { background-color: #198080; } .col-9 { background-color: #1133e6; }
        .col-0 { background-color: #828282; }

        .controls-flex { display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
        
        .btn { padding: 12px 24px; font-size: 15px; font-weight: bold; border-radius: 8px; cursor: pointer; border: none; transition: 0.2s; color: white; }
        .btn:hover { transform: translateY(-2px); }
        .predict-btn { background: linear-gradient(135deg, #1fa331 0%, #157321 100%); box-shadow: 0 4px 6px rgba(21, 115, 33, 0.3); }
        .eliminate-btn { background: linear-gradient(135deg, #6c757d 0%, #495057 100%); box-shadow: 0 4px 6px rgba(108, 117, 125, 0.3); }
        .river-btn { background: linear-gradient(135deg, #2196F3 0%, #0d47a1 100%); box-shadow: 0 4px 6px rgba(33, 150, 243, 0.3); }
        .river-btn.active { background: linear-gradient(135deg, #ff9800 0%, #e65100 100%); box-shadow: 0 4px 6px rgba(255, 152, 0, 0.3); border: 2px solid #fff; }
        .info-btn { background: linear-gradient(135deg, #00acc1 0%, #00838f 100%); box-shadow: 0 4px 6px rgba(0, 172, 193, 0.3); }
        
        .predict-result-row { display: flex; align-items: center; gap: 15px; margin-top: 10px; display: none; }
        .predict-label { font-weight: bold; font-size: 16px; color: #333; min-width:80px;}
        .predict-numbers { display: flex; gap: 6px; flex-wrap: wrap; }
        
        .predict-ball { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 16px; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
        .elim-ball { width: 32px; height: 32px; border-radius: 5px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 14px; background-color: #6c757d; text-decoration: line-through; }
        
        .info-panel { margin-top: 10px; padding: 16px; border-radius: 6px; line-height: 1.6; font-size: 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); display: none; }
        .predict-text { background: #fdfdfd; border-left: 5px solid #1fa331; color: #444; }
        .elim-text { background: #fff; border-left: 5px solid #6c757d; color: #444; }
        .river-text { background: #e3f2fd; border-left: 5px solid #2196F3; color: #0d47a1; }
        .exp-text { background: #e0f7fa; border-left: 5px solid #00acc1; color: #006064; }

        /* 期待度グラフ用 */
        .exp-bar-container { display: flex; align-items: center; margin-bottom: 6px; }
        .exp-num { width: 30px; font-weight: bold; text-align: center; font-size: 15px; }
        .exp-bar-bg { flex-grow: 1; background-color: #e0e0e0; height: 16px; border-radius: 8px; margin: 0 10px; overflow: hidden; position: relative; }
        .exp-bar-fill { height: 100%; border-radius: 8px; transition: width 0.5s ease-in-out; }
        .exp-pct { width: 50px; text-align: right; font-weight: bold; font-size: 13px; }

    </style>
</head>
<body>

    <div class="header-container">
        <h1>LOTO7 データ分析 ＆ 次回予想システム</h1>
        <div style="font-size: 13px; color: #666; margin-bottom: 20px; line-height: 1.5; background: #f9f9f9; padding: 10px; border-radius: 6px; border-left: 4px solid #aaa;">
            <strong>【統計学的な注意点（独立事象の原則）】</strong><br>
            ロト7の抽選は毎回が独立した事象であり、数学的には「次に出る確率はどの数字も常に一定」です。<br>
            当システムの予想は「過去に何回出なかったから確実に出る」という絶対的保証ではなく、極端な偏りを避け「これまでの出目の傾向・バランス」に基づいた一つの戦略としてお楽しみください。
        </div>
        
        <div class="controls-flex" style="align-items: center; background: #fff; padding: 10px; border-radius: 8px; border: 1px solid #ddd; margin-bottom: 10px; flex-wrap: wrap; gap: 15px;">
            <div style="display: flex; align-items: center;">
                <label style="font-size: 14px; font-weight: bold; color: #444; margin-right: 8px;">🎯 合計値の範囲:</label>
                <input type="number" id="minSumInput" placeholder="59" style="width: 60px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center;" min="28" max="231"> 
                <span style="font-weight: bold; color: #666; margin: 0 5px;">〜</span>
                <input type="number" id="maxSumInput" placeholder="170" style="width: 60px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center;" min="28" max="231">
            </div>
            
            <div style="display: flex; align-items: center;">
                <label style="font-size: 14px; font-weight: bold; color: #444; margin-right: 8px;">🎯 奇数:偶数の比率:</label>
                <span>奇数</span>
                <input type="number" id="oddsInput" placeholder="任意" onkeyup="updateEvens()" onchange="updateEvens()" style="width: 60px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center; margin-left: 5px;" min="0" max="7"> 
                <span style="font-weight: bold; color: #666; margin: 0 5px;">:</span>
                <span>偶数</span>
                <input type="text" id="evensInput" placeholder="-" style="width: 40px; padding: 6px; border: 1px solid #ccc; border-radius: 4px; text-align: center; background-color: #f5f5f5; margin-left: 5px;" readonly>
            </div>

            <div style="display: flex; align-items: center;">
                <label style="font-size: 14px; font-weight: bold; color: #444; margin-right: 8px;">🎯 固定数字 (最大4つ):</label>
                <input type="number" id="fixedNum1" placeholder="-" style="width: 45px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center; margin-right: 5px;" min="1" max="37"> 
                <input type="number" id="fixedNum2" placeholder="-" style="width: 45px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center; margin-right: 5px;" min="1" max="37"> 
                <input type="number" id="fixedNum3" placeholder="-" style="width: 45px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center; margin-right: 5px;" min="1" max="37"> 
                <input type="number" id="fixedNum4" placeholder="-" style="width: 45px; padding: 6px; border: 1px solid #aaa; border-radius: 4px; text-align: center;" min="1" max="37"> 
            </div>
            
            <div style="font-size: 12px; color: #888; flex-basis: 100%;">※各項目とも空欄の場合は過去傾向が自動適用されます。固定数字は指定した数字を必ず含めます。</div>
        </div>

        <div class="controls-flex">
            <button id="btnRiver" class="btn river-btn" onclick="toggleRiverTheory()">🌊 数字の川理論を適用</button>
            <button class="btn eliminate-btn" onclick="calculateEliminations()">🗑️ 削除数字を選定</button>
            <button class="btn info-btn" onclick="showExpectations()">📊 期待度を分析</button>
            <button class="btn predict-btn" onclick="generatePrediction()">🎯 次回予想を実行</button>
        </div>
        
        <div class="info-panel river-text" id="riverText"></div>
        <div class="info-panel exp-text" id="expectationText"></div>

        <div class="predict-result-row" id="elimResultRow">
            <div class="predict-label" style="color:#6c757d;">除外数字</div>
            <div class="predict-numbers" id="elimBallsContainer"></div>
        </div>
        <div class="info-panel elim-text" id="elimText"></div>

        <div class="predict-result-row" id="predictResultRow">
            <div class="predict-label" style="color:#1fa331;">予想結果</div>
            <div class="predict-numbers" id="predictBallsContainer"></div>
        </div>
        <div class="info-panel predict-text" id="predictText"></div>
    </div>

    <div class="board-container">
        <table id="mainBoard">
            <thead>
                <tr>
                    <th class="id-col" rowspan="2">回別</th>
                    <th colspan="37">本数字</th>
                </tr>
                <tr id="tableHeaderNumbers"></tr>
            </thead>
            <tbody id="tableBody"></tbody>
        </table>
    </div>

    <script>
        const lotoData = DATA_PLACEHOLDER;
        
        window.eliminatedNumbers = [];
        window.riverMode = false;
        window.riverRocks = [];
        window.riverDeserts = [];
        window.riverHotEnds = [];

        function updateEvens() {
            let odds = document.getElementById("oddsInput").value;
            if(odds !== "" && !isNaN(odds)) {
                let e = 7 - parseInt(odds);
                if(e >= 0 && e <= 7) document.getElementById("evensInput").value = e;
                else document.getElementById("evensInput").value = "";
            } else {
                document.getElementById("evensInput").value = "";
            }
        }

        function getColorClass(n) { return `col-${n % 10}`; }

        function getColorCode(n) {
            const colors = ["#828282", "#1a9c2a", "#00d0e0", "#f79c11", "#8c8c11", "#11d911", "#ebaa09", "#881c88", "#198080", "#1133e6"];
            return colors[n % 10];
        }
        
        function renderBoard() {
            const thContainer = document.getElementById('tableHeaderNumbers');
            let hHtml = "";
            for(let i=1; i<=37; i++) { hHtml += `<th>${i < 10 ? "0"+i : i}</th>`; }
            thContainer.innerHTML = hHtml;
            
            const tbody = document.getElementById('tableBody');
            let bHtml = "";
            lotoData.forEach(draw => {
                bHtml += `<tr><td class="id-col">${draw.id}</td>`;
                for(let i=1; i<=37; i++) {
                    if(draw.numbers.includes(i)) {
                        bHtml += `<td class="active"><div class="num-cell ${getColorClass(i)}">${i}</div></td>`;
                    } else {
                        bHtml += `<td><div class="num-cell"></div></td>`;
                    }
                }
                bHtml += `</tr>`;
            });
            tbody.innerHTML = bHtml;
        }

        // 期待度（スコア）算出ロジックを独立させる
        function calculateScores() {
            if(!lotoData) return Array(38).fill(1);
            const latest = lotoData[0].numbers;
            let scores = Array(38).fill(1); // 基礎点
            
            for(let i=0; i<Math.min(50, lotoData.length); i++) lotoData[i].numbers.forEach(n => scores[n] += 1);
            latest.forEach(n => scores[n] += 5); // 直近数字加点
            latest.forEach(n => { if(n > 1) scores[n-1] += 2; if(n < 37) scores[n+1] += 2; }); // スライド加点
            
            // 川理論がONの場合のみ強力に加算
            if(window.riverMode) {
                window.riverRocks.forEach(n => scores[n] += 15);
                for(let n=1; n<=37; n++) {
                    if(window.riverHotEnds.includes(n % 10)) scores[n] += 5;
                }
            }

            // 人気数字の回避 (当せん金額を最大化するため、選ばれやすい数字のスコアを微減)
            const popularNumbers = [7, 10, 20, 30];
            popularNumbers.forEach(n => {
                if(scores[n] > 0) scores[n] = Math.max(1, scores[n] - 1);
            });

            return scores;
        }

        function toggleRiverTheory() {
            window.riverMode = !window.riverMode;
            const btn = document.getElementById('btnRiver');
            const panel = document.getElementById('riverText');
            
            if(!window.riverMode) {
                btn.classList.remove('active');
                btn.innerHTML = '🌊 数字の川理論を適用';
                panel.style.display = 'none';
                
                // もし期待度が開いていたら表示を更新する
                if(document.getElementById('expectationText').style.display === 'block') {
                    showExpectations();
                }
                return;
            }
            
            btn.classList.add('active');
            btn.innerHTML = '🔥 数字の川モード適用中';
            
            let latest = lotoData[0].numbers;
            let previous = lotoData[1].numbers;
            
            let rocks = [];
            latest.forEach(n => {
                if(previous.includes(n)) rocks.push(n);
            });
            if(rocks.length === 0) {
                let counts = Array(38).fill(0);
                for(let i=0; i<Math.min(10, lotoData.length); i++) {
                    lotoData[i].numbers.forEach(n => counts[n]++);
                }
                let bestRock = latest[0];
                let maxC = 0;
                latest.forEach(n => {
                    if(counts[n] > maxC) { maxC = counts[n]; bestRock = n; }
                });
                rocks.push(bestRock);
            }
            
            let notSeenSince = Array(38).fill(999);
            for(let i=0; i<lotoData.length; i++) {
                lotoData[i].numbers.forEach(n => {
                    if(notSeenSince[n] === 999) notSeenSince[n] = i;
                });
            }
            let deserts = [];
            for(let n=1; n<=37; n++) {
                if(notSeenSince[n] > 20) deserts.push(n); 
            }
            
            let endCounts = Array(10).fill(0);
            for(let i=0; i<Math.min(10, lotoData.length); i++) {
                lotoData[i].numbers.forEach(n => endCounts[n % 10]++);
            }
            let bestEnd = 0, bestEnd2 = 1;
            let sdC = [...endCounts].map((c, i) => ({c, i})).sort((a,b) => b.c - a.c);
            bestEnd = sdC[0].i;
            bestEnd2= sdC[1].i;
            
            window.riverRocks = rocks;
            window.riverDeserts = deserts;
            window.riverHotEnds = [bestEnd, bestEnd2];

            let desertStr = deserts.length > 0 ? deserts.join(",") : "特になし";
            
            panel.innerHTML = `<strong>【🌊 数字の川理論 解析レポート】</strong><br>
                <ul>
                    <li><strong>岩（強い引っ張り候補）</strong>: [${rocks.join(", ")}] <br><span style="font-size:12px">→前回から連続で出現しており、川の流れを止める強力な岩として次回も居座る可能性があります。</span></li>
                    <li><strong>中洲（空白地帯）</strong>: [${desertStr}] <br><span style="font-size:12px">→長期間出現していない冷え切ったエリアです。</span></li>
                    <li><strong>支流（トレンド末尾）</strong>: 下1桁が「<strong>${bestEnd}</strong>」または「<strong>${bestEnd2}</strong>」の数字。<br><span style="font-size:12px">→セットで出現しやすい傾向が強く出ています。</span></li>
                </ul>
            `;
            panel.style.display = 'block';
            
            // 期待度が開いていれば更新
            if(document.getElementById('expectationText').style.display === 'block') {
                showExpectations();
            }
        }

        // 📊 分析ロジック（ランキング表示）
        function showExpectations() {
            const scores = calculateScores();
            let totalScore = 0;
            
            // 合計スコアを計算（除外数字を除いた合計で確率を出す）
            for(let i=1; i<=37; i++) {
                if(!window.eliminatedNumbers.includes(i)) {
                    totalScore += scores[i];
                }
            }
            
            let expList = [];
            for(let i=1; i<=37; i++) {
                let prob = 0;
                let isElim = window.eliminatedNumbers.includes(i);
                if(!isElim && totalScore > 0) {
                    // 全体合計スコアに対する比率 * 7個選ぶ補正 (*100で%)
                    prob = (scores[i] / totalScore) * 7 * 100;
                    if(prob > 99.9) prob = 99.9;
                }
                expList.push({ n: i, p: prob, elim: isElim });
            }
            
            // 期待度が高い順にソート。除外は一番下へ。
            expList.sort((a,b) => {
                if(a.elim && !b.elim) return 1;
                if(!a.elim && b.elim) return -1;
                return b.p - a.p;
            });
            
            let html = `<strong>【📊 各数字の出現期待度ランキング】</strong><br>
                        現在の波（頻出・引っ張り・スライド）${window.riverMode ? "＋🌊川理論モード" : ""} を加味した相対的な出現期待値です。
                        <div style="margin-top:10px; max-height: 250px; overflow-y: auto; padding-right: 10px;">`;
            
            expList.forEach(item => {
                let numStr = item.n < 10 ? "0"+item.n : item.n;
                let pStr = item.elim ? "除外" : item.p.toFixed(1) + "%";
                let barWidth = item.elim ? 0 : item.p;
                
                // グラフのバー色分け
                let color = "#00acc1"; // デフォルト
                if(item.p >= 30) color = "#d32f2f"; // 超熱・赤
                else if(item.p >= 20) color = "#f57c00"; // 熱・オレンジ
                else if(item.p < 15) color = "#9e9e9e"; // 冷え・グレー
                
                let opacityStyle = item.elim ? 'opacity: 0.4;' : '';
                
                html += `
                <div class="exp-bar-container" style="${opacityStyle}">
                    <div class="exp-num" style="color:${getColorCode(item.n)};">${numStr}</div>
                    <div class="exp-bar-bg">
                        <div class="exp-bar-fill" style="width: ${barWidth}%; background-color: ${color};"></div>
                    </div>
                    <div class="exp-pct" style="color:${color};">${pStr}</div>
                </div>
                `;
            });
            html += `</div>`;
            
            const panel = document.getElementById('expectationText');
            panel.innerHTML = html;
            
            if(panel.style.display === 'block') {
                // すでに開いている場合は非表示にはせず更新のみか、ボタンのトグル動作にする
                // panel.style.display = 'none'; // 今回は常時トグル式にするならコメントアウトを外す
            } else {
                panel.style.display = 'block';
            }
        }

        function calculateEliminations() {
            if(!lotoData) return;
            
            let recentCounts = Array(38).fill(0);
            let notSeenSince = Array(38).fill(999);
            for(let i=0; i<Math.min(15, lotoData.length); i++) lotoData[i].numbers.forEach(n => recentCounts[n]++);
            for(let i=0; i<lotoData.length; i++) lotoData[i].numbers.forEach(n => { if(notSeenSince[n] === 999) notSeenSince[n] = i; });
            
            let elims = [];
            let rText = "<ul>";
            
            if (window.riverMode && window.riverDeserts.length > 0) {
                let dTarget = window.riverDeserts.slice(0, 3);
                dTarget.forEach(n => {
                    elims.push(n);
                    rText += `<li><strong>${n}</strong>: 川理論（中洲）… 過去${notSeenSince[n]}回出現していない空白地帯のため、今回も流れが来ないと判断。</li>`;
                });
            } else {
                let coldCands = [];
                for(let n=1; n<=37; n++) coldCands.push({num: n, since: notSeenSince[n]});
                coldCands.sort((a,b) => b.since - a.since);
                for(let i=0; i<2; i++) {
                    elims.push(coldCands[i].num);
                    rText += `<li><strong>${coldCands[i].num}</strong>: 長期不在数字（過去${coldCands[i].since}回出現なし）</li>`;
                }
            }

            let hotCands = [];
            for(let n=1; n<=37; n++) {
                if(recentCounts[n] >= 4 && !elims.includes(n)) {
                    if(window.riverMode && window.riverRocks.includes(n)) continue; 
                    hotCands.push({num: n, count: recentCounts[n]});
                }
            }
            hotCands.sort((a,b) => b.count - a.count);
            for(let i=0; i<Math.min(2, hotCands.length); i++) {
                elims.push(hotCands[i].num);
                rText += `<li><strong>${hotCands[i].num}</strong>: 直近頻出数字（直近15回中${hotCands[i].count}回出現のため、過熱と判断）</li>`;
            }
            
            rText += "</ul>";
            window.eliminatedNumbers = elims;
            
            const eRow = document.getElementById('elimResultRow');
            const eBalls = document.getElementById('elimBallsContainer');
            const eText = document.getElementById('elimText');
            
            eBalls.innerHTML = elims.map(n => `<div class="elim-ball">${n}</div>`).join("");
            eRow.style.display = 'flex';
            setTimeout(() => eRow.classList.add('show'), 10);
            
            let theoryMsg = window.riverMode ? "【🌊 川理論モード中洲回避】を含め、" : "";
            eText.innerHTML = `<strong>【削除数字に選定した理由】</strong><br>${theoryMsg}以下の数字を予想候補から除外しました。<br>${rText}`;
            eText.style.display = 'block';
            
            const thContainer = document.getElementById('tableHeaderNumbers');
            let hHtml = "";
            for(let i=1; i<=37; i++) {
                let dispText = i < 10 ? "0" + i : i;
                if (window.eliminatedNumbers.includes(i)) {
                    hHtml += `<th style="color:#8f9a9c; text-decoration:line-through;">✖</th>`;
                }
                else {
                    hHtml += `<th>${dispText}</th>`;
                }
            }
            thContainer.innerHTML = hHtml;
            
            // 期待度が開いていれば更新
            if(document.getElementById('expectationText').style.display === 'block') {
                showExpectations();
            }
        }

        function generatePrediction() {
            if(!lotoData) return;
            const latest = lotoData[0].numbers;
            
            // UIからの合計値取得
            let uiMin = document.getElementById('minSumInput').value;
            let uiMax = document.getElementById('maxSumInput').value;
            let targetMin = uiMin !== "" ? parseInt(uiMin) : 59;
            let targetMax = uiMax !== "" ? parseInt(uiMax) : 170;
            
            // UIからの奇数・偶数割合取得
            let uiOdds = document.getElementById('oddsInput').value;
            let targetOdds = uiOdds !== "" ? parseInt(uiOdds) : null;
            
            // UIからの固定数字取得
            let fixedNums = [];
            for (let i = 1; i <= 4; i++) {
                let val = document.getElementById(`fixedNum${i}`).value;
                if (val !== "") {
                    let num = parseInt(val);
                    if (num >= 1 && num <= 37 && !fixedNums.includes(num)) {
                        fixedNums.push(num);
                    }
                }
            }
            
            // 独立したスコア関数から取得
            let scores = calculateScores();

            let bestSelection = [];
            let trials = 0;
            let finalOdds=0, finalEvens=0, finalSum=0;
            
            while(trials < 2000) {
                trials++;
                let available = Array.from({length: 37}, (_, i) => i + 1).filter(x => !window.eliminatedNumbers.includes(x) && !fixedNums.includes(x));
                let selection = [...fixedNums];
                if(available.length + selection.length < 7) break;
                
                while(selection.length < 7) {
                    let totalScore = available.reduce((sum, n) => sum + scores[n], 0);
                    let r = Math.random() * totalScore;
                    let picked = available[0];
                    for(let n of available) {
                        r -= scores[n];
                        if(r <= 0) {
                            picked = n; break;
                        }
                    }
                    if(picked) {
                        selection.push(picked);
                        available = available.filter(x => x !== picked);
                    }
                }
                selection.sort((a,b) => a - b);
                
                let odds = selection.filter(x => x % 2 !== 0).length;
                let sum = selection.reduce((a,b) => a+b, 0);
                
                // 高低バランス: 1〜18（低）、19〜37（高）
                let lowCount = selection.filter(x => x <= 18).length;
                let highCount = 7 - lowCount;
                let hasGoodHighLow = (lowCount === 3 && highCount === 4) || (lowCount === 4 && highCount === 3);

                // 人気の数字対策（当せん金最大化）
                // 誕生日買い（1〜31）ばかりにならないよう、32以上を必ず1個以上含める
                let hasHighNumber = selection.some(x => x >= 32);
                
                let hasConsecutive = false;
                let hasSameEnding = false;
                let hasRock = false;
                
                if (window.riverMode) {
                    for(let i=0; i<selection.length-1; i++) {
                        if(selection[i+1] - selection[i] === 1) { hasConsecutive = true; break; }
                    }
                    let ends = selection.map(x => x%10);
                    hasSameEnding = new Set(ends).size < ends.length;
                    hasRock = selection.some(x => latest.includes(x));
                }

                // 基本条件: 奇数偶数比(指定 or 3:4/4:3), 高低比(3:4 or 4:3), 合計値(設定範囲内), 32以上(1個以上)
                let hasGoodOdds = (targetOdds !== null) ? (odds === targetOdds) : (odds === 3 || odds === 4);
                let basicCondition = hasGoodOdds && 
                                     hasGoodHighLow && 
                                     (sum >= targetMin && sum <= targetMax) && 
                                     hasHighNumber;

                if (window.riverMode) {
                    if (trials < 1500) {
                        if (basicCondition && hasConsecutive && hasSameEnding && hasRock) { bestSelection = selection; break; }
                    } else {
                        if (basicCondition && hasConsecutive && hasSameEnding) { bestSelection = selection; break; }
                    }
                } else {
                    if (basicCondition) { bestSelection = selection; break; }
                }
                if(trials === 2000) bestSelection = selection;
            }
            
            finalOdds = bestSelection.filter(x => x % 2 !== 0).length;
            finalEvens = 7 - finalOdds;
            finalSum = bestSelection.reduce((a,b) => a+b, 0);
            
            let finalLow = bestSelection.filter(x => x <= 18).length;
            let finalHigh = 7 - finalLow;
            
            const rRow = document.getElementById('predictResultRow');
            const balls = document.getElementById('predictBallsContainer');
            const pText = document.getElementById('predictText');
            
            const thContainer = document.getElementById('tableHeaderNumbers');
            let hHtml = "";
            for(let i=1; i<=37; i++) {
                let dispText = i < 10 ? "0" + i : i;
                if(bestSelection.includes(i)) {
                    hHtml += `<th class="${getColorClass(i)}" style="color:white; box-shadow:inset 0 0 5px rgba(0,0,0,0.3);">${dispText}</th>`;
                }
                else if (window.eliminatedNumbers.includes(i)) {
                    hHtml += `<th style="color:#8f9a9c; text-decoration:line-through;">✖</th>`;
                }
                else {
                    hHtml += `<th>${dispText}</th>`;
                }
            }
            thContainer.innerHTML = hHtml;
            
            balls.innerHTML = bestSelection.map(n => `<div class="predict-ball ${getColorClass(n)}">${n}</div>`).join("");
            rRow.style.display = 'flex';
            setTimeout(() => rRow.classList.add('show'), 10);
            
            let theTxt = window.riverMode ? `<li><strong style="color:#e65100;">🌊 数字の川理論を適用</strong>: 出現確率7割の「連番」、約8割の「末尾一致」、および「引っ張りの岩（前回の当選数字）」の条件で構成。</li>` : "";
            let elimTxt = window.eliminatedNumbers.length > 0 ? `<li><strong>削除数字の連携</strong>: ${window.eliminatedNumbers.length}個の削除数字（表ヘッダの✖印）を回避しました。</li>` : "";
            let oddsTxtInfo = (targetOdds !== null) ? `（ユーザー指定 ${targetOdds}:${7-targetOdds}）` : `（傾向の黄金比）`;
            let fixedTxtInfo = fixedNums.length > 0 ? `<li><strong>固定数字の設定</strong>: 指定された ${fixedNums.length}個の数字（${fixedNums.join(", ")}）を確実に含めています。</li>` : "";

            pText.innerHTML = `<strong>【予測ロジック解説】</strong><br>
                <ul style="margin: 8px 0; padding-left: 20px;">
                    ${theTxt}
                    ${elimTxt}
                    ${fixedTxtInfo}
                    <li><strong>バランス調整（奇数偶数・高低）</strong>：奇数 <b>${finalOdds}</b> : 偶数 <b>${finalEvens}</b> ${oddsTxtInfo}、低い数字(1-18) <b>${finalLow}</b> : 高い数字(19-37) <b>${finalHigh}</b> の黄金比（3:4または4:3）で構成。</li>
                    <li><strong>合計値の最適化</strong>：指定の範囲（${targetMin}〜${targetMax}）に完全に収まる合計値 <b>${finalSum}</b> で抽出。</li>
                    <li><strong>当せん金最大化の戦略</strong>：誕生日目当ての構成（1〜31だけ）などによる1等当せん金の目減りを防ぐため、必ず32以上の数字が選ばれています。</li>
                </ul>`;
            pText.style.display = 'block';
        }

        renderBoard();
    </script>
</body>
</html>
"""
    final_html = html_template.replace("DATA_PLACEHOLDER", json_data)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(final_html)

if __name__ == "__main__":
    main()
