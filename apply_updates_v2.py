
import os

filepath = r'c:\Users\Kentaro\Desktop\LOTO7\loto6_board_with_setball.html'

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Update UI: Add toggle checkbox
old_ui = '<option value="J">Jセット</option>\n                            </select>'
new_ui = '<option value="J">Jセット</option>\n                            </select>\n                            <label style="display: flex; align-items: center; gap: 5px; font-size: 0.85em; cursor: pointer; white-space: nowrap; margin-right: 10px;">\n                                <input type="checkbox" id="reflectSetBall" checked style="cursor: pointer;">\n                                予測に反映\n                            </label>'
content = content.replace(old_ui, new_ui)

# 2. Update getSetBallStats logic: Use last 50 draws
old_stats_func = """        function getSetBallStats(sb) {
            if (!sb) return null;
            const stats = {};
            lotoData.forEach(draw => {
                if (draw.set_ball === sb) {
                    draw.numbers.forEach(n => {
                        stats[n] = (stats[n] || 0) + 1;
                    });
                }
            });
            return Object.entries(stats)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 5);
        }"""

new_stats_func = """        function getSetBallStats(sb) {
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
        }"""
content = content.replace(old_stats_func, new_stats_func)

# 3. Update generatePrediction logic
old_predict_func = """        function generatePrediction() {
            let pool = Array.from({length: 43}, (_, i) => i + 1);
            pool = pool.filter(n => !excludedNumbers.has(n));
            
            // Priority 1: Selected (Fixed) numbers
            let prediction = [...selectedNumbers];
            
            // Fill the rest with random choices from pool
            const remainingCount = 6 - prediction.length;
            if (remainingCount > 0) {
                const availablePool = pool.filter(n => !prediction.includes(n));
                const shuffled = availablePool.sort(() => 0.5 - Math.random());
                prediction.push(...shuffled.slice(0, remainingCount));
            }
            
            return prediction.sort((a, b) => a - b);
        }"""

new_predict_func = """        let currentReasoning = "";

        function generatePrediction() {
            const reflectSetBall = document.getElementById('reflectSetBall').checked;
            const selectedSetBall = document.getElementById('setBallSelect').value;
            
            let pool = Array.from({length: 43}, (_, i) => i + 1);
            pool = pool.filter(n => !excludedNumbers.has(n));
            
            let prediction = [...selectedNumbers];
            let reasoning = [];

            if (selectedNumbers.size > 0) {
                reasoning.push(`【固定数字】 ユーザー指定の ${[...selectedNumbers].join(', ')} を優先しました。`);
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
                            reasoning.push(`【セット球分析】 ${selectedSetBall}セットの直近50回における出現上位から ${picks.join(', ')} を抽出しました。`);
                        }
                    }
                }
            } else if (selectedSetBall) {
                reasoning.push(`【セット球表示】 ${selectedSetBall}セットの出現頻度を表示していますが、予測ロジックには反映していません。`);
            }

            // 残りをランダムで補充
            const remainingCount = 6 - prediction.length;
            if (remainingCount > 0) {
                const availablePool = pool.filter(n => !prediction.includes(n));
                const shuffled = availablePool.sort(() => 0.5 - Math.random());
                const randomPicks = shuffled.slice(0, remainingCount);
                prediction.push(...randomPicks);
                reasoning.push(`【数値補充】 残りの枠をランダムな数値 ${randomPicks.join(', ')} で補充しました。`);
            }

            currentReasoning = reasoning.join('<br>');
            return prediction.sort((a, b) => a - b);
        }"""
content = content.replace(old_predict_func, new_predict_func)

# 4. Update displayResult logic (Merge and Clean up)
old_display_func = """        function displayResult(nums) {
            const container = document.getElementById('predictionResult');
            container.innerHTML = `
                <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 20px;">
                    ${nums.map(n => `<div class="ball">${n}</div>`).join('')}
                </div>
            `;
        }"""
# Note: There were multiple definitions, we replace the first one and the others will be handled or replaced.

new_display_func = """        function displayResult(nums) {
            const container = document.getElementById('predictionResult');
            container.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 15px;">
                        ${nums.map(n => `<div class="ball">${n}</div>`).join('')}
                    </div>
                    <div id="predictionReasoning" style="font-size: 0.85em; color: var(--text-muted); background: rgba(255,255,255,0.5); padding: 15px; border-radius: 8px; text-align: left; line-height: 1.6; border: 1px dashed #ccc;">
                        <div style="font-weight: bold; margin-bottom: 5px; color: var(--primary-blue);">■ 予測ロジックの解説</div>
                        ${currentReasoning}
                    </div>
                </div>
            `;
        }"""

# Since there are multiple displayResult and onPredictClick at the end due to a messy backup/previous turn,
# let's replace the whole section from function getSetBallStats to the end of script with a clean version.

import re
script_pattern = re.compile(r'function getSetBallStats\(sb\) \{.*?</script>', re.DOTALL)

clean_script = """function getSetBallStats(sb) {
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
                reasoning.push(`【固定数字】 ユーザー指定の ${[...selectedNumbers].join(', ')} を優先しました。`);
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
                            reasoning.push(`【セット球分析】 ${selectedSetBall}セットの直近50回における出現上位から ${picks.join(', ')} を抽出しました。`);
                        }
                    }
                }
            } else if (selectedSetBall) {
                reasoning.push(`【セット球表示】 ${selectedSetBall}セットの出現頻度を表示していますが、予測ロジックには反映していません。`);
            }

            // 残りをランダムで補充
            const remainingCount = 6 - prediction.length;
            if (remainingCount > 0) {
                const availablePool = pool.filter(n => !prediction.includes(n));
                const shuffled = availablePool.sort(() => 0.5 - Math.random());
                const randomPicks = shuffled.slice(0, remainingCount);
                prediction.push(...randomPicks);
                reasoning.push(`【数値補充】 残りの枠をランダムな数値 ${randomPicks.join(', ')} で補充しました。`);
            }

            currentReasoning = reasoning.join('<br>');
            return prediction.sort((a, b) => a - b);
        }

        function savePrediction(nums) {
            const history = JSON.parse(localStorage.getItem('loto6_history') || '[]');
            const entry = {
                id: Date.now(),
                numbers: nums,
                date: new Date().toLocaleString(),
                memo: document.getElementById('predictionMemo').value || ''
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
            savePrediction(prediction);
        }

        function displayResult(nums) {
            const container = document.getElementById('predictionResult');
            container.innerHTML = `
                <div style="text-align: center; margin-bottom: 20px;">
                    <div style="display: flex; gap: 10px; justify-content: center; margin-bottom: 15px;">
                        ${nums.map(n => `<div class="ball">${n}</div>`).join('')}
                    </div>
                    <div id="predictionReasoning" style="font-size: 0.85em; color: var(--text-muted); background: rgba(255,255,255,0.5); padding: 15px; border-radius: 8px; text-align: left; line-height: 1.6; border: 1px dashed #ccc;">
                        <div style="font-weight: bold; margin-bottom: 5px; color: var(--primary-blue);">■ 予測ロジックの解説</div>
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

        // Initial history load
        updateHistoryUI();

        // Sidebar toggle
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('active');
        }

        // Privacy Modal
        function showPrivacy() {
            document.getElementById('privacyModal').style.display = 'flex';
        }

        function closePrivacy() {
            document.getElementById('privacyModal').style.display = 'none';
        }

        // Image export
        async function exportToImage() {
            const element = document.getElementById('predictionResult');
            const canvas = await html2canvas(element);
            const link = document.createElement('a');
            link.download = `loto6-prediction-${Date.now()}.png`;
            link.href = canvas.toDataURL();
            link.click();
        }
    </script>"""

content = script_pattern.sub(clean_script, content)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Update complete with clean script.")
