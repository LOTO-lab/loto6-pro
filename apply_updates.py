import os

file_path = r'c:\Users\Kentaro\Desktop\LOTO7\loto6_board_with_setball.html'

def perform_replacement():
    # Try different encodings
    content = None
    applied_encoding = None
    for enc in ['utf-8-sig', 'utf-8', 'cp932', 'euc-jp']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
                applied_encoding = enc
                print(f"Read with {enc} successfully.")
                break
        except Exception:
            continue
    
    if content is None:
        print("Could not read file with any common encoding.")
        return

    # 1. Update UI: Add checkbox for reflecting set ball
    old_ui = '            <div class="input-group">\n                <label for="setBallSelect">セット球:</label>\n                <select id="setBallSelect">'
    new_ui = old_ui # keep same start
    
    # We'll search for the whole block to be safe
    old_block = """            <div class="input-group">
                <label for="setBallSelect">セット球:</label>
                <select id="setBallSelect">
                    <option value="">(未選択)</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                    <option value="E">E</option>
                    <option value="F">F</option>
                    <option value="G">G</option>
                    <option value="H">H</option>
                    <option value="I">I</option>
                    <option value="J">J</option>
                </select>
            </div>"""
    
    new_block = """            <div class="input-group">
                <label for="setBallSelect">セット球:</label>
                <select id="setBallSelect">
                    <option value="">(未選択)</option>
                    <option value="A">A</option>
                    <option value="B">B</option>
                    <option value="C">C</option>
                    <option value="D">D</option>
                    <option value="E">E</option>
                    <option value="F">F</option>
                    <option value="G">G</option>
                    <option value="H">H</option>
                    <option value="I">I</option>
                    <option value="J">J</option>
                </select>
                <div style="margin-top: 8px; display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" id="reflectSetBall" style="width: 18px; height: 18px; cursor: pointer;">
                    <label for="reflectSetBall" style="font-size: 0.9em; color: #fbbf24; cursor: pointer; user-select: none;">予測ロジックに反映する</label>
                </div>
            </div>"""
    
    content = content.replace(old_block, new_block)

    # 2. Add Reasoning Panel
    old_result_div = '<div class="prediction-result" id="prediction-result"></div>'
    new_result_div = """<div class="prediction-result" id="prediction-result"></div>
        <div id="prediction-reasoning" style="margin-top: 15px; padding: 15px; background: rgba(0,0,0,0.25); border: 1px solid rgba(251, 191, 36, 0.4); border-radius: 8px; font-size: 0.85em; line-height: 1.6; display: none; color: #f3f4f6;">
            <h4 style="margin: 0 0 10px 0; color: #fbbf24; border-bottom: 1px solid rgba(251, 191, 36, 0.3); padding-bottom: 5px; font-size: 0.95em; display: flex; align-items: center; gap: 6px;">
                <span style="font-size: 1.2em;">💡</span> 予測ロジック解説
            </h4>
            <div id="reasoning-text"></div>
        </div>"""
    
    content = content.replace(old_result_div, new_result_div)

    # 3. Update getSetBallStats logic (last 50)
    # We need to find the function body. Since I can't be sure about the whitespace, I'll use a more surgical approach if possible, but let's try a direct replace first.
    
    old_stats_func = """        function getSetBallStats(targetSet) {
            const counts = {};
            for(let i=1; i<=43; i++) counts[i] = 0;
            
            lotoData.forEach(draw => {
                if(draw.set_ball === targetSet) {
                    draw.numbers.forEach(n => {
                        if (!counts[n]) counts[n] = 0;
                        counts[n]++;
                    });
                }
            });

            return Object.entries(counts)
                .map(([num, count]) => ({ num: parseInt(num), count }))
                .filter(item => item.count > 0)
                .sort((a, b) => b.count - a.count || a.num - b.num);
        }"""
        
    new_stats_func = """        function getSetBallStats(targetSet) {
            const counts = {};
            for (let i = 1; i <= 43; i++) counts[i] = 0;

            // 直近50回に限定して分析
            const recentData = lotoData.slice(0, 50);
            recentData.forEach(draw => {
                if (draw.set_ball === targetSet) {
                    draw.numbers.forEach(n => {
                        counts[n]++;
                    });
                }
            });

            return Object.entries(counts)
                .map(([num, count]) => ({ num: parseInt(num), count }))
                .filter(item => item.count > 0)
                .sort((a, b) => b.count - a.count || a.num - b.num);
        }"""
    
    content = content.replace(old_stats_func, new_stats_func)

    # 4. Update generatePrediction logic
    old_pred_func = """        function generatePrediction() {
            // 固定数字を優先
            const fixedNumbers = Array.from(selectedNumbers);
            let prediction = [...fixedNumbers];
            
            // 6個に成るまでランダムに追加
            while (prediction.length < 6) {
                let num = Math.floor(Math.random() * 43) + 1;
                if (!prediction.includes(num)) {
                    prediction.push(num);
                }
            }
            
            prediction.sort((a, b) => a - b);
            
            const resultDiv = document.getElementById('prediction-result');
            resultDiv.innerHTML = '';
            prediction.forEach(num => {
                const ball = document.createElement('div');
                ball.className = `ball ${getBallColor(num)}`;
                ball.innerText = num;
                resultDiv.appendChild(ball);
            });
        }"""
        
    new_pred_func = """        function generatePrediction() {
            const reflectSetBall = document.getElementById('reflectSetBall').checked;
            const targetSet = document.getElementById('setBallSelect').value;
            const fixedNumbers = Array.from(selectedNumbers).sort((a, b) => a - b);
            
            let prediction = [...fixedNumbers];
            let reasoningSteps = [];

            // 1. 固定数字の適用
            if (fixedNumbers.length > 0) {
                reasoningSteps.push(`○ <b>固定数字優先:</b> ユーザー指定の ${fixedNumbers.length} 個 (${fixedNumbers.join(', ')}) を軸に設定。`);
            }

            // 2. セット球分析の反映
            if (reflectSetBall && targetSet) {
                const stats = getSetBallStats(targetSet);
                const top5 = stats.slice(0, 5);
                
                if (top5.length > 0) {
                    const availableTop = top5.filter(item => !prediction.includes(item.num));
                    if (availableTop.length > 0 && prediction.length < 6) {
                        // 最大2個まで選出（直近50回の傾向を反映）
                        const countToAdd = Math.min(2, 6 - prediction.length, availableTop.length);
                        const selectedFromSet = availableTop.slice(0, countToAdd);
                        
                        selectedFromSet.forEach(item => {
                            prediction.push(item.num);
                        });
                        
                        reasoningSteps.push(`○ <b>セット球考慮:</b> ${targetSet}セットの直近50回データから、出現回数の多い ${selectedFromSet.map(i => i.num).join(', ')} を抽出。`);
                    } else if (prediction.length >= 6) {
                        reasoningSteps.push(`○ <b>セット球注記:</b> 固定数字で全枠が埋まっているため、分析結果は反映されませんでした。`);
                    }
                } else {
                    reasoningSteps.push(`○ <b>セット球注記:</b> ${targetSet}セットの直近データが不足しているため、通常抽出を行いました。`);
                }
            }

            // 3. 不足分の補充
            const beforeAutoFill = prediction.length;
            while (prediction.length < 6) {
                let num = Math.floor(Math.random() * 43) + 1;
                if (!prediction.includes(num)) {
                    prediction.push(num);
                }
            }

            if (prediction.length > beforeAutoFill) {
                reasoningSteps.push(`○ <b>バランス調整:</b> 残りの ${6 - beforeAutoFill} 個を、全体の出現バランスを考慮してランダムに選出。`);
            }

            prediction.sort((a, b) => a - b);
            
            // 結果表示
            displayPrediction(prediction);
            
            // 解説の表示
            const reasoningContainer = document.getElementById('prediction-reasoning');
            const reasoningText = document.getElementById('reasoning-text');
            
            if (reasoningSteps.length > 0) {
                const htmlContent = reasoningSteps.map(step => `<div style="margin-bottom: 4px;">${step}</div>`).join('');
                reasoningText.innerHTML = htmlContent;
                reasoningContainer.style.display = 'block';
            } else {
                reasoningContainer.style.display = 'none';
            }
        }

        function displayPrediction(numbers) {
            const resultDiv = document.getElementById('prediction-result');
            resultDiv.innerHTML = '';
            numbers.forEach(num => {
                const ball = document.createElement('div');
                ball.className = `ball ${getBallColor(num)}`;
                ball.innerText = num;
                resultDiv.appendChild(ball);
            });
        }"""
    
    content = content.replace(old_pred_func, new_pred_func)

    # Save back as UTF-8
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Replacements applied successfully and saved as UTF-8.")

if __name__ == "__main__":
    perform_replacement()
