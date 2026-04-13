
import sys

def update_file():
    filepath = r'c:\Users\Kentaro\Desktop\LOTO7\loto6_board_with_setball.html'
    
    # Try reading as utf-8 then cp932
    content = None
    for enc in ['utf-8', 'cp932', 'shift_jis']:
        try:
            with open(filepath, 'r', encoding=enc) as f:
                content = f.read()
            print(f"Read successfully using {enc}")
            break
        except UnicodeDecodeError:
            continue
    
    if content is None:
        print("Failed to decode the file with utf-8, cp932, or shift_jis")
        return

    # 1. Update UI: Add toggle checkbox
    # We find the location to insert the checkbox
    import re
    
    # Insert checkbox after the select element
    content = re.sub(
        r'(<select id="setBallSelect".*?</select>)',
        r'\1\n                            <label style="display: flex; align-items: center; gap: 5px; font-size: 0.85em; cursor: pointer; white-space: nowrap; margin-right: 10px; color: var(--text-dark);">\n                                <input type="checkbox" id="reflectSetBall" checked style="cursor: pointer;">\n                                予測に反映\n                            </label>',
        content,
        flags=re.DOTALL
    )

    # 2. Rewrite the script block
    # Find the start of the logic section and the end of the script tag
    start_marker = 'function getSetBallStats'
    end_marker = '</script>'
    
    # New script content
    new_script = """function getSetBallStats(sb) {
            if (!sb) return null;
            const stats = {};
            // 直近50回分のみを対象にする
            const recentData = lotoData.slice(0, 50);
            recentData.forEach(draw => {
                if (draw.set_ball === sb) {
                    draw.numbers.forEach(n => {
                        stats[n] = (stats[n] || 0) + 1;
                    });
                }
            });
            return Object.entries(stats)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5);
        }

        function onSetBallChange() {
            const sb = document.getElementById('setBallSelect').value;
            const stats = getSetBallStats(sb);
            const container = document.getElementById('setBallStats');
            if (!sb || !stats) {
                container.innerHTML = '';
                return;
            }
            container.innerHTML = `直近50出現回数TOP5: ${stats.map(s => `${s[0]}(${s[1]}回)`).join(', ')}`;
        }

        let currentReasoning = "";

        function generatePrediction() {
            const reflectSetBall = document.getElementById('reflectSetBall').checked;
            const selectedSetBall = document.getElementById('setBallSelect').value;
            
            let pool = Array.from({length: 43}, (_, i) => i + 1);
            pool = pool.filter(n => !excludedNumbers.has(n));
            
            let prediction = [...selectedNumbers];
            let reasoning = [];

            if (selectedNumbers.size > 0) {
                const sortedSelected = [...selectedNumbers].sort((a,b)=>a-b);
                reasoning.push(`【固定数字】 ユーザー指定の ${sortedSelected.join(', ')} を優先しました。`);
            }

            // セット球ロジックの適用
            if (reflectSetBall && selectedSetBall) {
                const stats = getSetBallStats(selectedSetBall);
                if (stats && stats.length > 0) {
                    // 出現回数TOP5から1〜2個を選択
                    const setBallCandidates = stats.map(s => parseInt(s[0])).filter(n => !prediction.includes(n) && !excludedNumbers.has(n));
                    if (setBallCandidates.length > 0) {
                        const count = Math.floor(Math.random() * 2) + 1; // 1〜2個
                        const picks = setBallCandidates.sort(() => 0.5 - Math.random()).slice(0, Math.min(count, 6 - prediction.length));
                        
                        picks.forEach(p => {
                            prediction.push(p);
                        });
                        
                        if (picks.length > 0) {
                            reasoning.push(`【セット球分析】 ${selectedSetBall}セットの直近50回データを精査し、出現傾向の高い ${picks.sort((a,b)=>a-b).join(', ')} を選択しました。`);
                        }
                    }
                }
            } else if (selectedSetBall) {
                reasoning.push(`【セット球】 ${selectedSetBall}セットが選択されていますが、予測への反映はオフです。`);
            }

            // 残りをランダムで補充
            const remainingCount = 6 - prediction.length;
            if (remainingCount > 0) {
                const availablePool = pool.filter(n => !prediction.includes(n));
                const shuffled = availablePool.sort(() => 0.5 - Math.random());
                const randomPicks = shuffled.slice(0, remainingCount);
                prediction.push(...randomPicks);
                reasoning.push(`【数値補充】 残り${remainingCount}個をランダムに選出しました。`);
            }

            currentReasoning = reasoning.join('<br>');
            return prediction.sort((a, b) => a - b);
        }

        function savePrediction(nums, reasoning) {
            const history = JSON.parse(localStorage.getItem('loto6_history') || '[]');
            const entry = {
                id: Date.now(),
                numbers: nums,
                date: new Date().toLocaleString(),
                memo: document.getElementById('predictionMemo').value || '',
                reasoning: reasoning
            };
            history.unshift(entry);
            localStorage.setItem('loto6_history', JSON.stringify(history.slice(0, 100)));
            updateHistoryUI();
        }

        function updateHistoryUI() {
            const history = JSON.parse(localStorage.getItem('loto6_history') || '[]');
            const container = document.getElementById('historyList');
            if (!container) return;
            container.innerHTML = history.map(entry => `
                <div class="history-item" style="background: var(--glass-bg); padding: 10px; border-radius: 8px; margin-bottom: 5px; border: 1px solid var(--glass-border);">
                    <div style="font-size: 0.75em; color: var(--text-muted); margin-bottom: 5px;">${entry.date}</div>
                    <div style="display: flex; gap: 5px; margin-bottom: 5px;">
                        ${entry.numbers.map(n => `<span class="ball small">${n}</span>`).join('')}
                    </div>
                    ${entry.memo ? `<div style="font-size: 0.8em; color: var(--text-dark);">${entry.memo}</div>` : ''}
                    <button onclick="deleteHistory(${entry.id})" style="background: none; border: none; color: #ef4444; cursor: pointer; font-size: 0.7em; margin-top: 5px;">削除</button>
                </div>
            `).join('');
        }

        function deleteHistory(id) {
            let history = JSON.parse(localStorage.getItem('loto6_history') || '[]');
            history = history.filter(h => h.id !== id);
            localStorage.setItem('loto6_history', JSON.stringify(history));
            updateHistoryUI();
        }

        function clearHistory() {
            if (confirm('全ての履歴を削除しますか？')) {
                localStorage.removeItem('loto6_history');
                updateHistoryUI();
            }
        }

        function onPredictClick() {
            const prediction = generatePrediction();
            displayResult(prediction);
            savePrediction(prediction, currentReasoning);
        }

        function displayResult(nums) {
            const container = document.getElementById('predictionResult');
            container.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 15px;">
                        ${nums.map(n => `<div class="ball">${n}</div>`).join('')}
                    </div>
                    <div id="predictionReasoning" style="font-size: 0.85em; color: var(--text-dark); background: rgba(255,255,255,0.6); padding: 15px; border-radius: 12px; text-align: left; line-height: 1.6; border: 1px solid var(--glass-border); box-shadow: var(--shadow);">
                        <div style="font-weight: bold; margin-bottom: 8px; color: var(--primary-blue); display: flex; align-items: center; gap: 5px;">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
                            予測ロジックの詳細
                        </div>
                        ${currentReasoning}
                    </div>
                </div>
            `;
        }

        function clearSelected() {
            selectedNumbers.clear();
            renderBoard();
        }

        function clearExcluded() {
            excludedNumbers.clear();
            renderBoard();
        }

        updateHistoryUI();

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('active');
        }

        function showPrivacy() {
            document.getElementById('privacyModal').style.display = 'flex';
        }

        function closePrivacy() {
            document.getElementById('privacyModal').style.display = 'none';
        }

        async function exportToImage() {
            const element = document.getElementById('predictionResult');
            const canvas = await html2canvas(element);
            const link = document.createElement('a');
            link.download = `loto6-prediction-${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();
        }
    </script>"""

    # Find the range to replace in the script
    # We want to replace everything from the first "function getSetBallStats" to the last "</script>"
    start_idx = content.find(start_marker)
    last_script_end = content.rfind('</script>') + 9
    
    if start_idx != -1 and last_script_end != -1:
        updated_content = content[:start_idx] + clean_script + content[last_script_end:]
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        print("Success: File updated and encoded to UTF-8.")
    else:
        print(f"Error: Could not find script markers. start={start_idx}, end={last_script_end}")

if __name__ == "__main__":
    update_file()
